import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import Column, Float, Integer, String, Text, text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

import config

Base = declarative_base()


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_date = Column(String(32), nullable=False)
    invoice_number = Column(String(128), nullable=False)
    company_name = Column(String(256), nullable=False)
    total_amount = Column(Float, nullable=False)
    entered_by = Column(String(128), nullable=False)
    notes = Column(Text, nullable=True)
    pdf_path = Column(String(512), nullable=True)
    payment_status = Column(String(32), nullable=False, default="unpaid")
    payment_proof_path = Column(String(512), nullable=True)
    payment_date = Column(String(32), nullable=True)
    credit = Column(Float, nullable=False, default=0.00)
    paid_amount = Column(Float, nullable=False, default=0.00)

class PaymentHistory(Base):
    """付款历史记录模型"""
    __tablename__ = "payment_history"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, nullable=False)
    payment_amount = Column(Float, nullable=False)
    payment_date = Column(String(32), nullable=False)
    payment_proof_path = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(String(32), nullable=True)


def _determine_backend() -> str:
    preferred = os.getenv("DATA_BACKEND", "").strip().lower()
    if preferred:
        return preferred
    if config.SUPABASE_URL and config.SUPABASE_KEY:
        return "supabase"
    return "sqlite"


# ---------- SQLite Backend ----------

class SQLiteBackend:
    def __init__(self) -> None:
        database_url = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{Path(__file__).resolve().parent / 'invoices.db'}",
        )
        self.engine = create_engine(database_url, future=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
        
        Base.metadata.create_all(self.engine)
        
        # 创建 payment_history 表
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS payment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    payment_amount REAL NOT NULL,
                    payment_date TEXT NOT NULL,
                    payment_proof_path TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                )
            """))
            conn.commit()

        
        # 自动迁移: 检测并添加缺失字段
        self._auto_migrate_sqlite()
    
    def _auto_migrate_sqlite(self):
        """SQLite 自动迁移:检测并添加缺失字段"""
        try:
            with self.engine.connect() as conn:
                # 查询现有字段
                result = conn.execute(text("PRAGMA table_info(invoices)"))
                existing_columns = {row[1] for row in result.fetchall()}
                
                # 定义期望字段
                required_fields = {
                    'credit': 'REAL DEFAULT 0.00 NOT NULL',
                    'paid_amount': 'REAL DEFAULT 0.00 NOT NULL'
                }
                
                # 添加缺失字段
                for field_name, field_def in required_fields.items():
                    if field_name not in existing_columns:
                        print(f"SQLite Auto-migration: Adding column '{field_name}'")
                        conn.execute(text(f"ALTER TABLE invoices ADD COLUMN {field_name} {field_def}"))
                        conn.commit()
                        
                        # 为现有数据设置默认值
                        if field_name == 'paid_amount':
                            # 已付款的发票,设置 paid_amount = total_amount
                            conn.execute(text("""
                                UPDATE invoices 
                                SET paid_amount = total_amount 
                                WHERE payment_status = 'paid' AND (paid_amount = 0 OR paid_amount IS NULL)
                            """))
                            conn.commit()
                            print(f"SQLite Auto-migration: Set paid_amount for existing paid invoices")
                        elif field_name == 'credit':
                            # 所有现有记录的 credit 设为 0.00
                            conn.execute(text("UPDATE invoices SET credit = 0.00 WHERE credit IS NULL"))
                            conn.commit()
                            print(f"SQLite Auto-migration: Set credit default value")
        except Exception as e:
            print(f"SQLite Auto-migration warning: {e}")

    @contextmanager
    def session(self) -> Iterable[Session]:
        session: Session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        invoice = Invoice(
            invoice_date=data.get("invoice_date"),
            invoice_number=data.get("invoice_number"),
            company_name=data.get("company_name"),
            total_amount=data.get("total_amount"),
            entered_by=data.get("entered_by"),
            notes=data.get("notes"),
            pdf_path=data.get("pdf_path"),
            payment_status=data.get("payment_status", "unpaid"),
            payment_proof_path=data.get("payment_proof_path"),
            payment_date=data.get("payment_date"),
        )
        with self.session() as session:
            session.add(invoice)
            session.flush()
            session.refresh(invoice)
            return self._to_dict(invoice)

    def get_invoices(
        self,
        company_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with self.session() as session:
            query = session.query(Invoice)
            if company_name:
                query = query.filter(Invoice.company_name.ilike(f"%{company_name}%"))
            if invoice_number:
                query = query.filter(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
            if date_from:
                query = query.filter(Invoice.invoice_date >= date_from)
            if date_to:
                query = query.filter(Invoice.invoice_date <= date_to)

            invoices = query.order_by(Invoice.invoice_date.desc(), Invoice.id.desc()).all()
            return [self._to_dict(invoice) for invoice in invoices]

    def update_invoice(self, invoice_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.session() as session:
            invoice: Optional[Invoice] = session.get(Invoice, invoice_id)
            if not invoice:
                return None
            for key, value in data.items():
                if hasattr(invoice, key):
                    setattr(invoice, key, value)
            session.add(invoice)
            session.flush()
            session.refresh(invoice)
            return self._to_dict(invoice)

    def delete_invoice(self, invoice_id: int) -> bool:
        with self.session() as session:
            invoice: Optional[Invoice] = session.get(Invoice, invoice_id)
            if not invoice:
                return False
            session.delete(invoice)
            return True

    @staticmethod
    def _to_dict(invoice: Invoice) -> Dict[str, Any]:
        return {
            "id": invoice.id,
            "invoice_date": invoice.invoice_date,
            "invoice_number": invoice.invoice_number,
            "company_name": invoice.company_name,
            "total_amount": invoice.total_amount,
            "entered_by": invoice.entered_by,
            "notes": invoice.notes,
            "pdf_path": invoice.pdf_path,
            "payment_status": invoice.payment_status,
            "payment_proof_path": invoice.payment_proof_path,
            "payment_date": invoice.payment_date,
            "credit": invoice.credit,
            "paid_amount": invoice.paid_amount,
        }


    def create_payment_record(self, data: Dict[str, Any]) -> Optional[int]:
        """创建付款历史记录"""
        from datetime import datetime
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO payment_history 
                (invoice_id, payment_amount, payment_date, payment_proof_path, notes, created_at)
                VALUES (:invoice_id, :payment_amount, :payment_date, :payment_proof_path, :notes, :created_at)
            """), {
                'invoice_id': data['invoice_id'],
                'payment_amount': data['payment_amount'],
                'payment_date': data['payment_date'],
                'payment_proof_path': data.get('payment_proof_path'),
                'notes': data.get('notes', ''),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            conn.commit()
            return result.lastrowid
    
    def get_payment_history(self, invoice_id: int) -> List[Dict[str, Any]]:
        """获取发票的付款历史记录"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, invoice_id, payment_amount, payment_date, 
                       payment_proof_path, notes, created_at
                FROM payment_history
                WHERE invoice_id = :invoice_id
                ORDER BY created_at DESC
            """), {'invoice_id': invoice_id})
            
            records = []
            for row in result.fetchall():
                records.append({
                    'id': row[0],
                    'invoice_id': row[1],
                    'payment_amount': row[2],
                    'payment_date': row[3],
                    'payment_proof_path': row[4],
                    'notes': row[5],
                    'created_at': row[6]
                })
            return records


# ---------- Supabase Backend ----------


    def create_payment_record(self, data: Dict[str, Any]) -> Optional[int]:
        """创建付款历史记录"""
        from datetime import datetime
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO payment_history 
                (invoice_id, payment_amount, payment_date, payment_proof_path, notes, created_at)
                VALUES (:invoice_id, :payment_amount, :payment_date, :payment_proof_path, :notes, :created_at)
            """), {
                'invoice_id': data['invoice_id'],
                'payment_amount': data['payment_amount'],
                'payment_date': data['payment_date'],
                'payment_proof_path': data.get('payment_proof_path'),
                'notes': data.get('notes', ''),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            conn.commit()
            return result.lastrowid
    
    def get_payment_history(self, invoice_id: int) -> List[Dict[str, Any]]:
        """获取发票的付款历史记录"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, invoice_id, payment_amount, payment_date, 
                       payment_proof_path, notes, created_at
                FROM payment_history
                WHERE invoice_id = :invoice_id
                ORDER BY created_at DESC
            """), {'invoice_id': invoice_id})
            
            records = []
            for row in result.fetchall():
                records.append({
                    'id': row[0],
                    'invoice_id': row[1],
                    'payment_amount': row[2],
                    'payment_date': row[3],
                    'payment_proof_path': row[4],
                    'notes': row[5],
                    'created_at': row[6]
                })
            return records

class SupabaseBackend:
    def __init__(self) -> None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError("Supabase credentials are missing. Please set SUPABASE_URL and SUPABASE_KEY.")
        try:
            from supabase import Client, create_client  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError(
                "supabase client library is missing. Install it with `pip install supabase` or `pip install -r requirements.txt`."
            ) from exc

        self.client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        self._ensure_table_exists()

    def create_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.table("invoices").insert(data).execute()
        if response.data:
            return response.data[0]
        return data

    def get_invoices(
        self,
        company_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = self.client.table("invoices").select("*")
        if company_name:
            query = query.ilike("company_name", f"%{company_name}%")
        if invoice_number:
            query = query.ilike("invoice_number", f"%{invoice_number}%")
        if date_from:
            query = query.gte("invoice_date", date_from)
        if date_to:
            query = query.lte("invoice_date", date_to)

        response = query.order("invoice_date", desc=True).order("id", desc=True).execute()
        return response.data or []

    def update_invoice(self, invoice_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self.client.table("invoices").update(data).eq("id", invoice_id).execute()
        if response.data:
            return response.data[0]
        return None

    def delete_invoice(self, invoice_id: int) -> bool:
        response = self.client.table("invoices").delete().eq("id", invoice_id).execute()
        return bool(response.data)

    def _ensure_table_exists(self) -> None:
        password = os.getenv("SUPABASE_DB_PASSWORD")
        if not password:
            return

        try:
            from urllib.parse import urlparse
            import psycopg  # type: ignore
        except ModuleNotFoundError:
            return

        parsed = urlparse(config.SUPABASE_URL)
        host_ref = parsed.netloc.split(".")[0] if parsed.netloc else ""
        host = f"db.{host_ref}.supabase.co"

        connection_kwargs = {
            "dbname": os.getenv("SUPABASE_DB_NAME", "postgres"),
            "user": os.getenv("SUPABASE_DB_USER", "postgres"),
            "password": password,
            "host": os.getenv("SUPABASE_DB_HOST", host),
            "port": int(os.getenv("SUPABASE_DB_PORT", "5432")),
            "sslmode": os.getenv("SUPABASE_DB_SSLMODE", "require"),
        }

        ddl = """
        create table if not exists public.invoices (
            id bigint generated by default as identity primary key,
            invoice_date text not null,
            invoice_number text not null,
            company_name text not null,
            total_amount numeric not null,
            entered_by text not null,
            notes text,
            pdf_path text,
            payment_status text default 'unpaid' not null,
            payment_proof_path text,
            payment_date text,
            credit numeric default 0.00 not null,
            paid_amount numeric default 0.00 not null,
            inserted_at timestamp with time zone default now()
        );
        """
        enable_rls = "alter table public.invoices enable row level security;"
        ensure_policies = """
        do $$
        begin
            if not exists (
                select 1 from pg_policies
                where schemaname = 'public'
                  and tablename = 'invoices'
                  and policyname = 'allow anon insert'
            ) then
                create policy "allow anon insert" on public.invoices
                for insert
                using (auth.role() = 'anon')
                with check (auth.role() = 'anon');
            end if;

            if not exists (
                select 1 from pg_policies
                where schemaname = 'public'
                  and tablename = 'invoices'
                  and policyname = 'allow anon select'
            ) then
                create policy "allow anon select" on public.invoices
                for select
                using (auth.role() in ('anon', 'authenticated'));
            end if;

            if not exists (
                select 1 from pg_policies
                where schemaname = 'public'
                  and tablename = 'invoices'
                  and policyname = 'allow anon update'
            ) then
                create policy "allow anon update" on public.invoices
                for update
                using (auth.role() in ('anon', 'authenticated'))
                with check (auth.role() in ('anon', 'authenticated'));
            end if;

            if not exists (
                select 1 from pg_policies
                where schemaname = 'public'
                  and tablename = 'invoices'
                  and policyname = 'allow anon delete'
            ) then
                create policy "allow anon delete" on public.invoices
                for delete
                using (auth.role() in ('anon', 'authenticated'));
            end if;
        end $$;
        """

        try:
            with psycopg.connect(**connection_kwargs) as conn:
                conn.execute(ddl)
                conn.execute(enable_rls)
                conn.execute(ensure_policies)
                
                # 自动迁移: 检测并添加缺失字段
                self._auto_migrate_fields(conn)
                
                conn.commit()
        except Exception:
            return
    
    def _auto_migrate_fields(self, conn) -> None:
        """自动检测并添加缺失的字段"""
        try:
            # 1. 查询现有字段
            cursor = conn.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'invoices' AND table_schema = 'public'
            """)
            existing_columns = {row[0] for row in cursor.fetchall()}
            
            # 2. 定义期望字段
            required_fields = {
                'credit': 'numeric default 0.00 not null',
                'paid_amount': 'numeric default 0.00 not null'
            }
            
            # 3. 添加缺失字段
            for field_name, field_def in required_fields.items():
                if field_name not in existing_columns:
                    print(f"Auto-migration: Adding column '{field_name}'")
                    conn.execute(f"""
                        ALTER TABLE public.invoices 
                        ADD COLUMN {field_name} {field_def}
                    """)
                    
                    # 4. 为现有数据设置默认值
                    if field_name == 'paid_amount':
                        # 已付款的发票,设置 paid_amount = total_amount
                        conn.execute("""
                            UPDATE public.invoices 
                            SET paid_amount = total_amount 
                            WHERE payment_status = 'paid' AND (paid_amount = 0 OR paid_amount IS NULL)
                        """)
                        print(f"Auto-migration: Set paid_amount for existing paid invoices")
                    elif field_name == 'credit':
                        # 所有现有记录的 credit 设为 0.00
                        conn.execute("""
                            UPDATE public.invoices 
                            SET credit = 0.00 
                            WHERE credit IS NULL
                        """)
                        print(f"Auto-migration: Set credit default value for existing invoices")
        except Exception as e:
            print(f"Auto-migration warning: {e}")


    
    def create_payment_record(self, data: Dict[str, Any]) -> Optional[int]:
        """创建付款历史记录"""
        record_data = {
            'invoice_id': data['invoice_id'],
            'payment_amount': data['payment_amount'],
            'payment_date': data['payment_date'],
            'payment_proof_path': data.get('payment_proof_path'),
            'notes': data.get('notes', '')
        }
        response = self.client.table("payment_history").insert(record_data).execute()
        if response.data:
            return response.data[0]['id']
        return None
    
    def get_payment_history(self, invoice_id: int) -> List[Dict[str, Any]]:
        """获取发票的付款历史记录"""
        response = self.client.table("payment_history")\
            .select("*")\
            .eq("invoice_id", invoice_id)\
            .order("created_at", desc=True)\
            .execute()
        return response.data or []


    def create_payment_record(self, data: Dict[str, Any]) -> Optional[int]:
        """创建付款历史记录"""
        record_data = {
            'invoice_id': data['invoice_id'],
            'payment_amount': data['payment_amount'],
            'payment_date': data['payment_date'],
            'payment_proof_path': data.get('payment_proof_path'),
            'notes': data.get('notes', '')
        }
        response = self.client.table("payment_history").insert(record_data).execute()
        if response.data:
            return response.data[0]['id']
        return None
    
    def get_payment_history(self, invoice_id: int) -> List[Dict[str, Any]]:
        """获取发票的付款历史记录"""
        response = self.client.table("payment_history").select("*").eq("invoice_id", invoice_id).order("created_at", desc=True).execute()
        return response.data or []

# ---------- Backend Dispatch ----------

_BACKEND_NAME = _determine_backend()
_BACKEND: Optional[Any] = None


def _get_backend():
    global _BACKEND
    if _BACKEND is None:
        if _BACKEND_NAME == "supabase":
            _BACKEND = SupabaseBackend()
        else:
            _BACKEND = SQLiteBackend()
    return _BACKEND


def create_invoice(data: Dict[str, Any]) -> Dict[str, Any]:
    return _get_backend().create_invoice(data)


def get_invoices(
    company_name: Optional[str] = None,
    invoice_number: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return _get_backend().get_invoices(company_name, invoice_number, date_from, date_to)


def update_invoice(invoice_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return _get_backend().update_invoice(invoice_id, data)


def delete_invoice(invoice_id: int) -> bool:
    return _get_backend().delete_invoice(invoice_id)


def current_backend() -> str:
    """Expose the active data backend name for diagnostics."""
    return _BACKEND_NAME
