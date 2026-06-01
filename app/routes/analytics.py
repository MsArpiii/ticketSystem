from flask import Blueprint, render_template, flash
from app.models import db, Ticket
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route("/analytics")
def analytics():
    try:
        status_counts = db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
        total = sum(count for _, count in status_counts)
        open_t = next((count for status, count in status_counts if status == 'Open'), 0)
        resolved = next((count for status, count in status_counts if status == 'Resolved'), 0)

        severity_query = db.session.query(Ticket.severity, func.count(Ticket.id)).group_by(Ticket.severity).all()
        severity_data = [{'severity': sev, 'count': c} for sev, c in severity_query]
    except Exception as e:
        flash(f"❌ Database error: {e}", "danger")
        total = open_t = resolved = 0
        severity_data = []

    return render_template(
        "analytics.html",
        total=total,
        open=open_t,
        resolved=resolved,
        severity_data=severity_data
    )
