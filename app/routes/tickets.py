from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Ticket, TicketHistory
from sqlalchemy.exc import SQLAlchemyError

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route("/dashboard")
@login_required
def dashboard():
    search = request.args.get("search", "")
    severity = request.args.get("severity", "")
    page = request.args.get("page", 1, type=int)
    per_page = 6
    
    query = db.select(Ticket)

    if search:
        query = query.where(Ticket.title.like(f"%{search}%"))
    if severity:
        query = query.where(Ticket.severity == severity)

    query = query.order_by(Ticket.id.desc())
    
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    tickets = pagination.items
    total_pages = pagination.pages or 1

    return render_template(
        "dashboard.html",
        tickets=tickets,
        search=search,
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
        try:
            ticket.status = 'Resolved'
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
        try:
            ticket.assigned_to_id = current_user.id
            if ticket.status == 'Open':
                ticket.status = 'In Progress'
            
            log = TicketHistory(ticket_id=ticket.id, user_id=current_user.id, action="Claimed Ticket & marked In Progress")
            db.session.add(log)
            db.session.commit()
            flash("🤝 Ticket Claimed!")
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred while claiming.", "danger")
    return redirect(url_for("tickets.dashboard"))
