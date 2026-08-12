from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import db, Ticket, TicketHistory
from sqlalchemy.exc import SQLAlchemyError
from app.utils import auto_triage_severity, calculate_sla_deadline
import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'log', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

main_bp = Blueprint('main', __name__)

@main_bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        severity = request.form.get("severity", "").strip()

        # Input Validation
        if not title or not desc or severity not in ['Low', 'Medium', 'High']:
            flash("❌ Invalid input. Please ensure all fields are correctly filled.", "danger")
            return redirect(url_for("main.home"))

        # Auto-triage: override severity if NLP detects a major issue
        final_severity = auto_triage_severity(desc, severity)

        # File Upload Handling
        attachment = request.files.get('attachment')
        attachment_filename = None
        if attachment and attachment.filename:
            if allowed_file(attachment.filename):
                safe_filename = secure_filename(attachment.filename)
                unique_filename = f"{uuid.uuid4().hex}_{safe_filename}"
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                attachment.save(upload_path)
                attachment_filename = unique_filename
            else:
                flash("❌ Invalid file type. Allowed: .png, .jpg, .jpeg, .pdf, .log, .txt", "danger")
                return redirect(url_for("main.home"))

        try:
            sla_deadline = calculate_sla_deadline(final_severity)
            new_ticket = Ticket(title=title, description=desc, severity=final_severity, creator_id=current_user.id, sla_deadline=sla_deadline, attachment_filename=attachment_filename)
            db.session.add(new_ticket)
            db.session.flush() # Get new_ticket.id
            
            log = TicketHistory(ticket_id=new_ticket.id, user_id=current_user.id, action="Ticket Created")
            db.session.add(log)
            
            db.session.commit()
            flash("✅ Ticket Created Successfully!")
            return redirect(url_for("tickets.dashboard"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred while creating the ticket.", "danger")
            return redirect(url_for("main.home"))

    return render_template("home.html")

@main_bp.route("/about")
def about():
    return render_template("about.html")

@main_bp.route("/faq")
def faq():
    return render_template("faq.html")
