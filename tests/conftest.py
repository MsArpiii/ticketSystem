import pytest
from app import create_app
from app.models import db, User

@pytest.fixture
def app():
    # Use an in-memory SQLite database for testing
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.app_context():
        db.create_all()
        # Create a test admin and a test standard user
        from werkzeug.security import generate_password_hash
        admin = User(username='admin', password=generate_password_hash('adminpass'), role='admin')
        user = User(username='user1', password=generate_password_hash('userpass'), role='user')
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
