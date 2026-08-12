from flask import Blueprint, render_template, flash, jsonify
from flask_login import login_required, current_user
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

@analytics_bp.route("/api/v1/metrics")
@login_required
def api_metrics():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        # 1. SLA Compliance Rate
        total_tickets = db.session.query(Ticket).count()
        if total_tickets == 0:
            sla_compliance_rate = 100.0
        else:
            breached_tickets = db.session.query(Ticket).filter(Ticket.is_sla_breached == True).count()
            sla_compliance_rate = ((total_tickets - breached_tickets) / total_tickets) * 100.0
            
        # 2. Tickets by Severity (Open)
        severity_counts = db.session.query(Ticket.severity, func.count(Ticket.id)).filter(Ticket.status == 'Open').group_by(Ticket.severity).all()
        severity_data = {sev: count for sev, count in severity_counts}
        # ensure all keys exist
        for k in ['High', 'Medium', 'Low']:
            if k not in severity_data:
                severity_data[k] = 0
                
        # 3. MTTR (Mean Time To Resolution)
        # SQLite: julianday() converts datetime strings to Julian day numbers (days).
        # We compute the average difference, then multiply by 24 for hours.
        # Since created_at format is "YYYY-MM-DD HH:MM" and resolved_at is datetime, SQLite can handle it.
        # Wait, created_at string might need appending ':00' or julianday handles it. 
        # Using julianday for both.
        mttr_query = db.session.query(
            func.avg(
                func.julianday(Ticket.resolved_at) - func.julianday(Ticket.created_at)
            )
        ).filter(Ticket.status == 'Resolved').scalar()
        
        # mttr_query is in days. Convert to hours.
        if mttr_query is not None:
            mttr_hours = mttr_query * 24.0
        else:
            mttr_hours = 0.0
            
        return jsonify({
            "mttr_hours": round(mttr_hours, 2),
            "sla_compliance_rate": round(sla_compliance_rate, 2),
            "open_tickets_by_severity": severity_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
