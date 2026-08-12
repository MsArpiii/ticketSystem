from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Ticket, TicketHistory, TicketAuditLog
from sqlalchemy.exc import SQLAlchemyError

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route("/dashboard")
@login_required
def dashboard():
    from sqlalchemy import or_
    
    q = request.args.get("q", request.args.get("search", ""))
    status = request.args.get("status", "")
    severity = request.args.get("severity", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    query = db.select(Ticket)

    if q:
        query = query.where(or_(Ticket.title.ilike(f"%{q}%"), Ticket.description.ilike(f"%{q}%")))
    if status:
        query = query.where(Ticket.status == status)
    if severity:
        query = query.where(Ticket.severity == severity)

    query = query.order_by(Ticket.id.desc())
    
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    tickets = pagination.items
    total_pages = pagination.pages or 1

    return render_template(
        "dashboard.html",
        tickets=tickets,
        search=q,
        q=q,
        status=status,
        severity=severity,
        page=page,
        total_pages=total_pages
    )

@tickets_bp.route("/resolve/<int:id>", methods=["POST"])
@login_required
def resolve(id):
    if not current_user.is_admin:
        flash("❌ Unauthorized: Only Admins can resolve tickets.", "danger")
        return redirect(url_for("tickets.dashboard"))
        
    ticket = db.session.get(Ticket, id)
    if not ticket:
        flash("❌ Ticket not found.", "danger")
    else:
        if ticket.status != 'In Progress':
            flash("❌ Ticket must be 'In Progress' to be resolved.", "danger")
            return redirect(url_for("tickets.dashboard"))
            
        try:
            from datetime import datetime
            old_status = ticket.status
            ticket.status = 'Resolved'
            ticket.resolved_at = datetime.now()
            
            # Check SLA breach
            if ticket.sla_deadline and ticket.resolved_at > ticket.sla_deadline:
                ticket.is_sla_breached = True
            else:
                ticket.is_sla_breached = False
            
            audit_log = TicketAuditLog(
                ticket_id=ticket.id,
                changed_by_id=current_user.id,
                old_status=old_status,
                new_status='Resolved',
                action_note="Ticket resolved"
            )
            db.session.add(audit_log)
            
            log = TicketHistory(ticket_id=ticket.id, user_id=current_user.id, action="Resolved Ticket")
            db.session.add(log)
            db.session.commit()
            flash("✔ Ticket Resolved")
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred while resolving the ticket.", "danger")
    return redirect(url_for("tickets.dashboard"))

@tickets_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    if not current_user.is_admin:
        flash("❌ Unauthorized: Only Admins can delete tickets.", "danger")
        return redirect(url_for("tickets.dashboard"))
        
    ticket = db.session.get(Ticket, id)
    if not ticket:
        flash("❌ Ticket not found.", "danger")
    else:
        try:
            db.session.query(TicketHistory).filter_by(ticket_id=id).delete()
            db.session.delete(ticket)
            db.session.commit()
            flash("🗑 Ticket Deleted")
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred while deleting the ticket.", "danger")
    return redirect(url_for("tickets.dashboard"))

@tickets_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    if not current_user.is_admin:
        flash("❌ Unauthorized: Only Admins can edit tickets.", "danger")
        return redirect(url_for("tickets.dashboard"))
        
    ticket = db.session.get(Ticket, id)
    if not ticket:
        flash("❌ Ticket not found.", "danger")
        return redirect(url_for("tickets.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        severity = request.form.get("severity", "").strip()

        if not title or not desc or severity not in ['Low', 'Medium', 'High']:
            flash("❌ Invalid input. Please ensure all fields are correctly filled.", "danger")
            return redirect(url_for("tickets.edit", id=id))

        try:
            ticket.title = title
            ticket.description = desc
            ticket.severity = severity
            log = TicketHistory(ticket_id=ticket.id, user_id=current_user.id, action="Edited Ticket details")
            db.session.add(log)
            db.session.commit()
            flash("✏ Ticket Updated")
            return redirect(url_for("tickets.dashboard"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred while updating the ticket.", "danger")
            return redirect(url_for("tickets.edit", id=id))

    return render_template("edit.html", ticket=ticket)

@tickets_bp.route('/view/<int:id>')
@login_required
def view(id):
    ticket = db.session.get(Ticket, id)
    if not ticket:
        flash('Ticket not found!', 'danger')
        return redirect(url_for('tickets.dashboard'))
        
    history = db.session.query(TicketHistory).filter_by(ticket_id=id).order_by(TicketHistory.timestamp.desc()).all()
    
    return render_template('ticket_detail.html', ticket=ticket, history=history)

@tickets_bp.route("/claim/<int:id>", methods=["POST"])
@login_required
def claim(id):
    if not current_user.is_admin:
        flash("❌ Unauthorized: Only Admins can claim tickets.", "danger")
        return redirect(url_for("tickets.dashboard"))
        
    ticket = db.session.get(Ticket, id)
    if not ticket:
        flash("❌ Ticket not found.", "danger")
    else:
        if ticket.status != 'Open':
            flash("❌ Ticket must be 'Open' to be claimed.", "danger")
            return redirect(url_for("tickets.dashboard"))
            
        try:
            old_status = ticket.status
            ticket.assigned_to_id = current_user.id
            ticket.status = 'In Progress'
            
            audit_log = TicketAuditLog(
                ticket_id=ticket.id,
                changed_by_id=current_user.id,
                old_status=old_status,
                new_status='In Progress',
                action_note="Ticket claimed and marked In Progress"
            )
            db.session.add(audit_log)
            
            log = TicketHistory(ticket_id=ticket.id, user_id=current_user.id, action="Claimed Ticket & marked In Progress")
            db.session.add(log)
            db.session.commit()
            flash("🤝 Ticket Claimed!")
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred while claiming.", "danger")
    return redirect(url_for("tickets.dashboard"))
