from app.models import db, Ticket


def test_unauthorized_dashboard_access(client):
    response = client.get('/dashboard')
    # Flask-Login redirects to login page with a 302
    assert response.status_code == 302

def test_ticket_creation_and_auto_triage(client, app):
    # Log in as user1
    client.post('/login', data={'username': 'user1', 'password': 'userpass'})
    
    # Create ticket
    response = client.post('/', data={
        'title': 'System failure',
        'desc': 'The primary database just crashed',
        'severity': 'Low'
    })
    assert response.status_code == 302 # Redirect to dashboard
    
    # Check if DB actually elevated it to High because of 'database' & 'crash'
    with app.app_context():
        ticket = db.session.query(Ticket).first()
        assert ticket is not None
        assert ticket.severity == 'High'
        assert ticket.creator.username == 'user1'

def test_csrf_protection_on_delete_route(client):
    # Log in as admin
    client.post('/login', data={'username': 'admin', 'password': 'adminpass'})
    
    # Try to access a POST-only route via GET
    response = client.get('/delete/1')
    assert response.status_code == 405 # Method Not Allowed
