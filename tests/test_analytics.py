from app.models import db, Ticket
from datetime import datetime, timedelta

def test_api_metrics(client, app):
    # Log in as admin
    client.post('/login', data={'username': 'admin', 'password': 'adminpass'})
    
    with app.app_context():
        # Clean up existing tickets for isolated testing
        db.session.query(Ticket).delete()
        
        # Create a ticket that breached SLA
        now = datetime.now().replace(second=0, microsecond=0)
        t1_created = (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M")
        t1 = Ticket(title="T1", description="desc", severity="High", status="Resolved",
                    created_at=t1_created,
                    resolved_at=now,
                    is_sla_breached=True,
                    creator_id=1)
        db.session.add(t1)
        
        # Create an open compliant ticket
        t2 = Ticket(title="T2", description="desc", severity="Low", status="Open",
                    is_sla_breached=False,
                    creator_id=1)
        db.session.add(t2)
        
        # Create another open compliant ticket (Medium)
        t3 = Ticket(title="T3", description="desc", severity="Medium", status="Open",
                    is_sla_breached=False,
                    creator_id=1)
        db.session.add(t3)
        
        db.session.commit()
        
    # Request the metrics API
    response = client.get('/api/v1/metrics')
    assert response.status_code == 200
    data = response.get_json()
    
    # 3 total tickets, 1 breached -> SLA Compliance = 66.67%
    assert data["sla_compliance_rate"] == 66.67
    
    # MTTR: t1 took exactly 10 hours.
    assert data["mttr_hours"] == 10.0
    
    # Open Tickets by Severity: 1 Low, 1 Medium, 0 High
    assert data["open_tickets_by_severity"]["Low"] == 1
    assert data["open_tickets_by_severity"]["Medium"] == 1
    assert data["open_tickets_by_severity"]["High"] == 0
