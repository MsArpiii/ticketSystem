import os
from datetime import timedelta, datetime
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "danger"
login_manager.login_message = "❌ Please log in to access this page."

@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))

def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    # Load basic config from environment
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "fallback-dev-key")
    
    # Configure Persistent Sessions
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # Use DATABASE_URL for Postgres in Prod, fallback to local SQLite
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        db_name = os.environ.get("DB_NAME", "tickets.db")
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, db_name)}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure Uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
    
    # Ensure instance and upload folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        from werkzeug.security import generate_password_hash
        from app.models import Ticket
        
        demo_user = db.session.scalar(db.select(User).where(User.username == 'demo_admin'))
        if not demo_user:
            demo_user = User(username='demo_admin', password=generate_password_hash('demo1234'), role='admin')
            db.session.add(demo_user)
            db.session.commit()
            
            # Seed tickets
            t1 = Ticket(title='Server crash in US-East', description='The main database server crashed.', severity='High', status='Open', creator_id=demo_user.id, sla_deadline=datetime.now() + timedelta(hours=4))
            t2 = Ticket(title='Need access to Jira', description='Please grant me access to the engineering Jira board.', severity='Low', status='In Progress', creator_id=demo_user.id, assigned_to_id=demo_user.id, sla_deadline=datetime.now() + timedelta(hours=48))
            t3 = Ticket(title='UI bug on dashboard', description='The charts are not rendering correctly on mobile.', severity='Medium', status='Open', creator_id=demo_user.id, sla_deadline=datetime.now() + timedelta(hours=24))
            t4 = Ticket(title='Resolved: Payment gateway failure', description='Payments were failing. It has been fixed.', severity='High', status='Resolved', creator_id=demo_user.id, assigned_to_id=demo_user.id, resolved_at=datetime.now(), is_sla_breached=False)
            db.session.add_all([t1, t2, t3, t4])
            db.session.commit()

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.tickets import tickets_bp
    from app.routes.analytics import analytics_bp
    from app.routes.auth import auth_bp, oauth
    from app.routes.api import api_bp
    
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=os.environ.get("GOOGLE_CLIENT_ID", "default-client-id"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", "default-client-secret"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.models import Notification
            unread = db.session.query(Notification).filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
            return dict(unread_notifications=unread, unread_count=len(unread))
        return dict(unread_notifications=[], unread_count=0)

    return app
