from flask import Blueprint, jsonify
from app.models import db, Ticket
from flask_login import login_required

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/tickets', methods=['GET'])
@login_required
def get_tickets():
    """
    RESTful endpoint returning all tickets in JSON format.
    Requires authentication via session cookie (flask_login).
    In a real headless environment, you would use JWTs or API keys here.
    """
    tickets = db.session.query(Ticket).order_by(Ticket.id.desc()).all()
    
    # Serialize the models to dictionaries
    ticket_list = []
    for t in tickets:
        ticket_list.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "severity": t.severity,
            "status": t.status,
            "created_at": t.created_at,
            "creator_id": t.creator_id,
            "assigned_to_id": t.assigned_to_id
        })
        
    return jsonify({
        "status": "success",
        "count": len(ticket_list),
        "data": ticket_list
    }), 200
