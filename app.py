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

ALLOWED_EXTENSIONS = {"pdf"}

# Create uploads directory with error handling
try:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create uploads directory: {e}")
    print("File uploads will use cloud storage if configured.")


def allowed_file(filename: str) -> bool:
    """Returns True when the file extension is part of the allowed list."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health')
def health_check():
    """Health check endpoint for Railway and monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "invoice-management-system",
        "backend": database.current_backend()
    }), 200


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
        except (TypeError, ValueError):
            flash("Total Amount must be a number (example: 1234.56).", 'danger')
            return redirect(url_for('upload'))

        stored_filename = None
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Only PDF files are supported.", 'danger')
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
        return jsonify(success=False, message="Please upload a PDF file."), 400

    if not allowed_file(file.filename):
        return jsonify(success=False, message="Only PDF files are supported."), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
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

    return render_template('edit.html', invoice=invoice)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
