from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Ticket, TicketHistory, TicketAuditLog, Notification
from sqlalchemy.exc import SQLAlchemyError

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route("/dashboard")
@login_required
def dashboard():
    from sqlalchemy import or_, func
    import json
    
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
    
    # Calculate Metrics
    total_tickets = db.session.query(Ticket).count()
    sla_breaches = db.session.query(Ticket).filter(Ticket.is_sla_breached == True).count()
    open_incidents = db.session.query(Ticket).filter(Ticket.status == 'Open').count()
    
    mttr_query = db.session.query(
        func.avg(func.julianday(Ticket.resolved_at) - func.julianday(Ticket.created_at))
    ).filter(Ticket.status == 'Resolved').scalar()
    avg_mttr = round(mttr_query * 24.0, 1) if mttr_query else 0.0

    # Chart Data
    severity_counts = db.session.query(Ticket.severity, func.count(Ticket.id)).group_by(Ticket.severity).all()
    severity_dict = {sev: count for sev, count in severity_counts}
    severity_data = [severity_dict.get('High', 0), severity_dict.get('Medium', 0), severity_dict.get('Low', 0)]

    status_counts = db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    status_dict = {st: count for st, count in status_counts}
    status_data = [status_dict.get('Open', 0), status_dict.get('In Progress', 0), status_dict.get('Resolved', 0)]

    return render_template(
        "dashboard.html",
        tickets=tickets,
        search=q,
        q=q,
        status=status,
        severity=severity,
        page=page,
        total_pages=total_pages,
        total_tickets=total_tickets,
        sla_breaches=sla_breaches,
        open_incidents=open_incidents,
        avg_mttr=avg_mttr,
        severity_data=json.dumps(severity_data),
        status_data=json.dumps(status_data)
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
            
            # Create Notification
            if ticket.creator_id != current_user.id:
                notif = Notification(user_id=ticket.creator_id, message=f"Your ticket #{ticket.id} was resolved.")
                db.session.add(notif)
                
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
            
            # Create Notification
            if ticket.creator_id != current_user.id:
                notif = Notification(user_id=ticket.creator_id, message=f"Your ticket #{ticket.id} was updated.")
                db.session.add(notif)
                
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
            
            # Create Notification
            if ticket.creator_id != current_user.id:
                notif = Notification(user_id=ticket.creator_id, message=f"Your ticket #{ticket.id} was claimed by {current_user.username}.")
                db.session.add(notif)
                
            db.session.commit()
            flash("🤝 Ticket Claimed!")
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred while claiming.", "danger")
    return redirect(url_for("tickets.dashboard"))

@tickets_bp.route("/history")
@login_required
def history():
    user_tickets = db.session.query(Ticket).filter_by(creator_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template("history.html", tickets=user_tickets)

@tickets_bp.route("/comment/<int:id>", methods=["POST"])
@login_required
def add_comment(id):
    ticket = db.session.get(Ticket, id)
    if not ticket:
        flash("❌ Ticket not found.", "danger")
        return redirect(url_for("tickets.dashboard"))
        
    if current_user.id != ticket.creator_id and current_user.id != ticket.assigned_to_id and not current_user.is_admin:
        flash("❌ Unauthorized.", "danger")
        return redirect(url_for("tickets.view", id=id))
        
    comment_text = request.form.get("comment_text", "").strip()
    if not comment_text:
        flash("❌ Comment cannot be empty.", "danger")
        return redirect(url_for("tickets.view", id=id))
        
    from app.models import TicketComment
    new_comment = TicketComment(ticket_id=ticket.id, user_id=current_user.id, comment_text=comment_text)
    db.session.add(new_comment)
    
    if current_user.id != ticket.creator_id:
        notif1 = Notification(user_id=ticket.creator_id, message=f"New comment on ticket #{ticket.id} by {current_user.username}")
        db.session.add(notif1)
    if ticket.assigned_to_id and current_user.id != ticket.assigned_to_id:
        notif2 = Notification(user_id=ticket.assigned_to_id, message=f"New comment on ticket #{ticket.id} by {current_user.username}")
        db.session.add(notif2)
        
    try:
        db.session.commit()
        flash("💬 Comment added")
    except SQLAlchemyError:
        db.session.rollback()
        flash("❌ Error adding comment.", "danger")
        
    return redirect(url_for("tickets.view", id=id))
