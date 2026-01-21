import os
import tempfile
from datetime import datetime

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

import database
import ocr_handler
import storage_handler

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max file size

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "tiff", "tif"}

# Create uploads directory with error handling
try:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create uploads directory: {e}")
    print("File uploads will use cloud storage if configured.")


def allowed_file(filename: str) -> bool:
    """Returns True when the file extension is part of the allowed list."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_mime_type(filename: str) -> str:
    """Returns the MIME type based on file extension."""
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    mime_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "tiff": "image/tiff",
        "tif": "image/tiff",
    }
    return mime_types.get(ext, "application/octet-stream")


# ========== 辅助函数 ==========
def calculate_payment_status(total_amount: float, paid_amount: float) -> str:
    """根据 total_amount 和 paid_amount 计算付款状态"""
    if paid_amount == 0:
        return "unpaid"
    elif paid_amount >= total_amount:
        return "paid"
    else:
        return "partial"

def calculate_remaining_amount(total_amount: float, paid_amount: float, credit: float = 0.0) -> float:
    """计算剩余应付金额 = total_amount - paid_amount - credit"""
    return max(0.0, total_amount - paid_amount - credit)

def get_payment_status_badge(status: str) -> str:
    """返回付款状态的 Bootstrap 徽章 HTML"""
    badge_map = {
        "unpaid": '<span class="badge bg-danger">Unpaid</span>',
        "partial": '<span class="badge bg-warning text-dark">Partial</span>',
        "paid": '<span class="badge bg-success">Paid</span>'
    }
    return badge_map.get(status, '<span class="badge bg-secondary">Unknown</span>')

# 注册为 Jinja2 过滤器
app.jinja_env.filters['payment_status_badge'] = get_payment_status_badge
app.jinja_env.filters['calculate_remaining'] = calculate_remaining_amount


def format_date_english(date_string):
    """Format date string to English format (e.g., 'November 5, 2025')."""
    if not date_string:
        return ""
    try:
        # Try to parse various date formats
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                date_obj = datetime.strptime(date_string, fmt)
                return date_obj.strftime("%B %d, %Y")
            except ValueError:
                continue
        # If no format matched, return original
        return date_string
    except Exception:
        return date_string


# Register custom Jinja2 filter
app.jinja_env.filters['format_date'] = format_date_english


@app.route('/health')
def health_check():
    """Health check endpoint for Railway and monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "invoice-management-system",
        "backend": database.get_backend()
    }), 200


# 付款历史包装函数
def create_payment_record(data):
    """创建付款历史记录"""
    try:
        backend = database._get_backend()
        return backend.create_payment_record(data)
    except Exception as e:
        print(f"Error creating payment record: {e}")
        import traceback
        traceback.print_exc()
    return None

def get_payment_history(invoice_id):
    """获取付款历史"""
    try:
        backend = database._get_backend()
        return backend.get_payment_history(invoice_id)
    except Exception as e:
        print(f"Error getting payment history: {e}")
    return []



@app.route('/test-ocr')
def test_ocr_endpoint():
    """Test OCR functionality endpoint for debugging."""
    import subprocess

    result = {
        "tesseract_installed": False,
        "tesseract_path": None,
        "tesseract_version": None,
        "languages": [],
        "pytesseract_available": False,
        "ocr_test": None,
        "error": None
    }

    try:
        # Check tesseract command
        proc = subprocess.run(
            ["which", "tesseract"],
            capture_output=True,
            text=True,
            timeout=5
        )
        result["tesseract_installed"] = proc.returncode == 0
        result["tesseract_path"] = proc.stdout.strip() if proc.returncode == 0 else None

        if result["tesseract_installed"]:
            # Get version
            proc = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_lines = (proc.stderr or proc.stdout).split('\n')
            result["tesseract_version"] = version_lines[0] if version_lines else "unknown"

            # Get languages
            proc = subprocess.run(
                ["tesseract", "--list-langs"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if proc.stdout:
                langs = [
                    line.strip() for line in proc.stdout.split('\n')
                    if line.strip() and not line.startswith("List")
                ]
                result["languages"] = langs

        # Test pytesseract
        try:
            import pytesseract
            from PIL import Image, ImageDraw

            result["pytesseract_available"] = True

            # Create test image
            img = Image.new('RGB', (300, 100), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 40), "TEST OCR 12345", fill='black')

            # Try OCR
            text = pytesseract.image_to_string(img, lang='eng')
            result["ocr_test"] = {
                "success": bool(text.strip()),
                "output": text.strip(),
                "length": len(text.strip())
            }

        except ImportError as e:
            result["pytesseract_available"] = False
            result["ocr_test"] = {"success": False, "error": f"ImportError: {str(e)}"}
        except Exception as e:
            result["ocr_test"] = {"success": False, "error": str(e)}

    except Exception as e:
        result["error"] = str(e)

    return jsonify(result), 200


@app.route('/')
def index():
    company_name = (request.args.get('companyName') or '').strip()
    invoice_number = (request.args.get('invoiceNumber') or '').strip()
    date_from = (request.args.get('startDate') or '').strip()
    date_to = (request.args.get('endDate') or '').strip()

    parsed_from = None
    parsed_to = None

    if date_from:
        try:
            parsed_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            flash("Start date format is invalid. Use YYYY-MM-DD.", 'danger')
            date_from = ''
    if date_to:
        try:
            parsed_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            flash("End date format is invalid. Use YYYY-MM-DD.", 'danger')
            date_to = ''

    invoices = []
    if parsed_from and parsed_to and parsed_from > parsed_to:
        flash("Start date must be earlier than or equal to End date.", 'danger')
    else:
        try:
            invoices = database.get_invoices(
                company_name=company_name or None,
                invoice_number=invoice_number or None,
                date_from=date_from or None,
                date_to=date_to or None,
            )
        except Exception as exc:
            flash(f"Failed to load invoices: {exc}", 'danger')
            invoices = []

    return render_template(
        'index.html',
        invoices=invoices,
        filters={
            "companyName": company_name,
            "invoiceNumber": invoice_number,
            "startDate": date_from,
            "endDate": date_to,
        },
    )

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        invoice_date = request.form.get('invoiceDate')
        invoice_number = request.form.get('invoiceNumber')
        company_name = request.form.get('companyName')
        total_amount_raw = request.form.get('totalAmount')
        entered_by = request.form.get('enteredBy')
        notes = request.form.get('notes')
        credit_raw = request.form.get('credit', '0.00')
        credit_raw = request.form.get('credit', '0.00')
        file = request.files.get('invoiceFile')

        missing_fields = [
            label for key, label in (
                (invoice_date, "Invoice Date"),
                (invoice_number, "Invoice Number"),
                (company_name, "Company Name"),
                (total_amount_raw, "Total Amount"),
                (entered_by, "Entered By"),
            ) if not key
        ]
        if missing_fields:
            flash(f"Please fill in required fields: {', '.join(missing_fields)}", 'danger')
            return redirect(url_for('upload'))

        try:
            total_amount = float(total_amount_raw.replace(',', ''))
            credit = float(credit_raw.replace(',', '')) if credit_raw else 0.00
        except (TypeError, ValueError):
            flash("Total Amount and Credit must be numbers (example: 1234.56).", 'danger')
            return redirect(url_for('upload'))

        stored_filename = None
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Supported file types: PDF, JPEG, PNG, TIFF", 'danger')
                return redirect(url_for('upload'))

            # Check if Supabase Storage is enabled
            if storage_handler.should_use_storage():
                # Upload to Supabase Storage
                try:
                    file_data = file.read()
                    filename = secure_filename(file.filename)
                    storage_path, error = storage_handler.upload_file(file_data, filename)

                    if error:
                        flash(f"Failed to upload file to cloud storage: {error}", 'danger')
                        return redirect(url_for('upload'))

                    stored_filename = storage_path
                except Exception as exc:
                    flash(f"File upload error: {exc}", 'danger')
                    return redirect(url_for('upload'))
            else:
                # Fallback to local storage
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                filename = secure_filename(file.filename)
                stored_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)
                file.save(file_path)

        invoice_record = {
            "invoice_date": invoice_date,
            "invoice_number": invoice_number,
            "company_name": company_name,
            "total_amount": total_amount,
            "entered_by": entered_by,
            "notes": notes,
            "pdf_path": stored_filename,
            "credit": credit,
            "paid_amount": 0.00,
        }

        try:
            database.create_invoice(invoice_record)
        except Exception as exc:
            flash(f"Failed to save invoice: {exc}", 'danger')
            return redirect(url_for('upload'))

        flash("Invoice saved successfully.", 'success')
        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    file = request.files.get('invoiceFile')
    if not file or file.filename == '':
        return jsonify(success=False, message="Please upload a file."), 400

    if not allowed_file(file.filename):
        return jsonify(success=False, message="Supported file types: PDF, JPEG, PNG, TIFF"), 400

    # Get file extension for temp file
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "pdf"

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
        temp_path = temp_file.name
        file.save(temp_path)

    try:
        data, warnings = ocr_handler.extract_invoice_data(temp_path)
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 422
    except Exception as exc:
        return jsonify(success=False, message=f"Failed to read PDF: {exc}"), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return jsonify(success=True, data=data, warnings=warnings)

@app.route('/files/<path:filename>')
def download_invoice(filename: str):
    """Serves uploaded invoice PDFs or redirects to Supabase Storage URL."""
    # Check if using Supabase Storage
    if storage_handler.should_use_storage():
        # Get public URL from Supabase Storage
        public_url = storage_handler.get_public_url(filename)
        if public_url:
            return redirect(public_url)
        else:
            abort(404, description="File not found in cloud storage")
    else:
        # Serve from local storage
        safe_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.isfile(safe_path):
            abort(404)
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route('/edit/<int:invoice_id>', methods=['GET', 'POST'])
def edit_invoice(invoice_id: int):
    if request.method == 'POST':
        invoice_date = request.form.get('invoiceDate')
        invoice_number = request.form.get('invoiceNumber')
        company_name = request.form.get('companyName')
        total_amount_raw = request.form.get('totalAmount')
        entered_by = request.form.get('enteredBy')
        notes = request.form.get('notes')
        credit_raw = request.form.get('credit', '0.00')

        missing_fields = [
            label for key, label in (
                (invoice_date, "Invoice Date"),
                (invoice_number, "Invoice Number"),
                (company_name, "Company Name"),
                (total_amount_raw, "Total Amount"),
                (entered_by, "Entered By"),
            ) if not key
        ]
        if missing_fields:
            flash(f"Please fill in required fields: {', '.join(missing_fields)}", 'danger')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))

        try:
            total_amount = float(total_amount_raw.replace(',', ''))
            credit = float(credit_raw.replace(',', '')) if credit_raw else 0.00
        except (TypeError, ValueError):
            flash("Total Amount must be a number (example: 1234.56).", 'danger')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))

        invoice_data = {
            "invoice_date": invoice_date,
            "invoice_number": invoice_number,
            "company_name": company_name,
            "total_amount": total_amount,
            "entered_by": entered_by,
            "notes": notes,
            "credit": credit,
        }

        try:
            result = database.update_invoice(invoice_id, invoice_data)
            if result:
                flash("Invoice updated successfully.", 'success')
                return redirect(url_for('index'))
            else:
                flash("Invoice not found.", 'danger')
                return redirect(url_for('index'))
        except Exception as exc:
            flash(f"Failed to update invoice: {exc}", 'danger')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))

    # GET request - load existing invoice data
    invoices = database.get_invoices()
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)

    if not invoice:
        flash("Invoice not found.", 'danger')
        return redirect(url_for('index'))

    # 获取付款历史
    payment_history = get_payment_history(invoice_id)
    return render_template('edit.html', invoice=invoice, payment_history=payment_history)

@app.route('/delete/<int:invoice_id>', methods=['POST'])
def delete_invoice(invoice_id: int):
    try:
        # Get invoice to check if it has a PDF file
        invoices = database.get_invoices()
        invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)

        if not invoice:
            flash("Invoice not found.", 'danger')
            return redirect(url_for('index'))

        # Delete from database
        success = database.delete_invoice(invoice_id)

        if success:
            # Try to delete the PDF file if it exists
            if invoice.get('pdf_path'):
                if storage_handler.should_use_storage():
                    # Delete from Supabase Storage
                    try:
                        storage_handler.delete_file(invoice['pdf_path'])
                    except Exception as exc:
                        # Log error but don't fail the deletion
                        print(f"Failed to delete file from storage: {exc}")
                else:
                    # Delete from local storage
                    try:
                        file_path = os.path.join(app.config["UPLOAD_FOLDER"], invoice['pdf_path'])
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except OSError as exc:
                        # Log error but don't fail the deletion
                        print(f"Failed to delete local file: {exc}")

            flash("Invoice deleted successfully.", 'success')
        else:
            flash("Failed to delete invoice.", 'danger')
    except Exception as exc:
        flash(f"Error deleting invoice: {exc}", 'danger')

    return redirect(url_for('index'))

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/upload_payment/<int:invoice_id>', methods=['POST'])
def upload_payment_proof(invoice_id: int):
    """上传付款凭证并记录实付金额(支持部分付款)或更新 Credit"""
    # 1. 获取发票信息
    invoices = database.get_invoices()
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
    if not invoice:
        flash("Invoice not found.", 'danger')
        return redirect(url_for('index'))
    
    # 2. 接收表单数据
    paid_amount_raw = request.form.get('paidAmount', '').strip()
    payment_date = request.form.get('paymentDate', '').strip()
    credit_raw = request.form.get('credit', '').strip()
    
    # 3. 判断是更新 Credit 还是记录付款
    has_payment = bool(paid_amount_raw)
    has_credit_update = bool(credit_raw)
    
    if not has_payment and not has_credit_update:
        flash("Please enter either a payment amount or update the credit.", 'warning')
        return redirect(url_for('edit_invoice', invoice_id=invoice_id))
    
    update_data = {}
    
    # 4. 处理 Credit 更新
    if has_credit_update:
        try:
            credit = float(credit_raw.replace(',', ''))
            update_data['credit'] = credit
        except (TypeError, ValueError):
            flash("Credit must be a valid number.", 'danger')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
    
    # 5. 处理付款
    if has_payment:
        if not payment_date:
            flash("Payment date is required when recording a payment.", 'danger')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        try:
            new_payment = float(paid_amount_raw.replace(',', ''))
            if new_payment <= 0:
                flash("Paid amount must be greater than 0.", 'danger')
                return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        except (TypeError, ValueError):
            flash("Paid amount must be a valid number.", 'danger')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        # 累加已付金额
        current_paid = invoice.get('paid_amount', 0.00)
        total_paid = current_paid + new_payment
        total_amount = invoice.get('total_amount', 0.00)
        
        # 防止超额支付
        if total_paid > total_amount:
            flash(f"Total paid amount (${total_paid:.2f}) cannot exceed total amount (${total_amount:.2f}).", 'danger')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        # 处理付款凭证文件上传(可选)
        payment_file = request.files.get('paymentProof')
        stored_filename = invoice.get('payment_proof_path')
        
        if payment_file and payment_file.filename:
            if not allowed_file(payment_file.filename):
                flash("Supported file types for payment proof: PDF, JPEG, PNG, TIFF", 'danger')
                return redirect(url_for('edit_invoice', invoice_id=invoice_id))
            
            try:
                if storage_handler.should_use_storage():
                    file_data = payment_file.read()
                    filename = secure_filename(payment_file.filename)
                    payment_filename = f"payment_{filename}"
                    storage_path, error = storage_handler.upload_file(file_data, payment_filename)
                    
                    if error:
                        flash(f"Failed to upload payment proof: {error}", 'danger')
                        return redirect(url_for('edit_invoice', invoice_id=invoice_id))
                    
                    stored_filename = storage_path
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = secure_filename(payment_file.filename)
                    stored_filename = f"payment_{timestamp}_{filename}"
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)
                    payment_file.save(file_path)
            except Exception as exc:
                flash(f"Error uploading payment proof: {exc}", 'danger')
                return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        # 自动计算付款状态
        new_status = calculate_payment_status(total_amount, total_paid)
        
        # 添加付款相关更新
        update_data.update({
            'paid_amount': total_paid,
            'payment_status': new_status,
            'payment_date': payment_date,
        })
        if stored_filename:
            update_data['payment_proof_path'] = stored_filename
    
    # 6. 更新数据库
    try:
        result = database.update_invoice(invoice_id, update_data)
        if result:
            # 创建付款历史记录(如果有付款)
            if has_payment:
                try:
                    create_payment_record({
                        'invoice_id': invoice_id,
                        'payment_amount': new_payment,
                        'payment_date': payment_date,
                        'payment_proof_path': stored_filename,
                        'notes': f'Payment of ${new_payment:.2f}'
                    })
                    print(f"✅ Payment record created: ${new_payment:.2f}")
                except Exception as e:
                    print(f"⚠️ Failed to create payment record: {e}")
            
            messages = []
            if has_credit_update:
                messages.append(f"Credit updated: ${update_data.get('credit', 0):.2f}")
            if has_payment:
                status_text = {
                    'unpaid': 'Unpaid',
                    'partial': 'Partial',
                    'paid': 'Paid'
                }.get(update_data.get('payment_status', ''), '')
                messages.append(f"Payment recorded: ${update_data['paid_amount']:.2f}, Status: {status_text}")
            
            flash(" | ".join(messages), 'success')
        else:
            flash("Invoice not found.", 'danger')
    except Exception as exc:
        flash(f"Error updating invoice: {exc}", 'danger')
    
    return redirect(url_for('edit_invoice', invoice_id=invoice_id))
@app.route('/payment_files/<path:filename>')
def download_payment_proof(filename: str):
    """Serves payment proof PDFs or redirects to Supabase Storage URL."""
    # Check if using Supabase Storage
    if storage_handler.should_use_storage():
        # Get public URL from Supabase Storage
        public_url = storage_handler.get_public_url(filename)
        if public_url:
            return redirect(public_url)
        else:
            abort(404, description="Payment proof file not found in cloud storage")
    else:
        # Serve from local storage
        safe_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.isfile(safe_path):
            abort(404)
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route('/mark_unpaid/<int:invoice_id>', methods=['POST'])
def mark_unpaid(invoice_id: int):
    """Mark an invoice as unpaid and remove payment proof."""
    try:
        # Get invoice to check if it has a payment proof file
        invoices = database.get_invoices()
        invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)

        if not invoice:
            flash("Invoice not found.", 'danger')
            return redirect(url_for('index'))

        # Delete payment proof file if it exists
        if invoice.get('payment_proof_path'):
            if storage_handler.should_use_storage():
                try:
                    storage_handler.delete_file(invoice['payment_proof_path'])
                except Exception as exc:
                    print(f"Failed to delete payment proof from storage: {exc}")
            else:
                try:
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], invoice['payment_proof_path'])
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except OSError as exc:
                    print(f"Failed to delete local payment proof file: {exc}")

        # Update invoice status
        update_data = {
            "payment_status": "unpaid",
            "payment_proof_path": None,
            "payment_date": None,
        }

        result = database.update_invoice(invoice_id, update_data)
        if result:
            # 创建付款历史记录(如果有付款)
            if has_payment:
                create_payment_record({
                    'invoice_id': invoice_id,
                    'payment_amount': new_payment,
                    'payment_date': payment_date,
                    'payment_proof_path': stored_filename,
                    'notes': f'Payment of ${new_payment:.2f}'
                })
            
            flash("Invoice marked as unpaid.", 'success')
        else:
            flash("Failed to update invoice.", 'danger')

    except Exception as exc:
        flash(f"Error updating invoice: {exc}", 'danger')

    return redirect(url_for('edit_invoice', invoice_id=invoice_id))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
