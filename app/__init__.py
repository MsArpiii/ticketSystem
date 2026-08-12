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
            
            # Seed realistic tickets
            import random
            
            titles_descs = [
                ("Login page throwing 500 error", "When trying to log in using the SSO button, the page crashes with a 500 error.", "High"),
                ("Unable to reset password", "The password reset link says it's expired immediately after receiving the email.", "High"),
                ("Dashboard charts not loading on mobile", "The charts section is completely blank on iOS Safari.", "Medium"),
                ("Feature request: dark mode for reports", "It would be great to have a dark theme when exporting reports.", "Low"),
                ("Database connection timeout on checkout", "Users are reporting timeouts when trying to pay.", "High"),
                ("Update billing address", "I need to change my corporate billing address for next month.", "Low"),
                ("Add new admin user", "Please provision an admin account for the new IT hire.", "Medium"),
                ("API rate limit exceeded", "Our integration is hitting the 429 rate limit too often.", "Medium"),
                ("Missing data in Analytics tab", "The analytics tab shows 0 tickets for yesterday but we had 5.", "High"),
                ("Change notification email", "Can we route alerts to a specific pager email?", "Low"),
                ("SSO certificate expiring soon", "We got an alert that the SAML cert expires in 3 days.", "High"),
                ("Typo on the landing page", "There is a spelling error in the second paragraph.", "Low"),
                ("Cannot upload attachments > 2MB", "The system rejects my 3MB PDF file.", "Medium"),
                ("Requesting API documentation", "Where can I find the Swagger docs?", "Low"),
                ("Weekly report not sent", "The automated weekly report did not arrive on Monday.", "Medium"),
                ("Account locked out", "I entered the wrong password 5 times and now I'm locked out.", "High"),
                ("Integration webhook failing", "The webhook to Slack is returning a 403 error.", "Medium"),
                ("Upgrade subscription plan", "We want to move to the Enterprise tier.", "Low"),
                ("Slow performance during peak hours", "The dashboard takes 10+ seconds to load at 9 AM.", "High"),
                ("Delete old user accounts", "Please purge the listed inactive accounts.", "Low")
            ]
            
            now = datetime.now()
            tickets_to_add = []
            
            for i, (title, desc, severity) in enumerate(titles_descs):
                days_ago = random.randint(0, 30)
                created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                
                status_roll = random.random()
                if status_roll < 0.45:
                    status = 'Resolved'
                elif status_roll < 0.8:
                    status = 'In Progress'
                else:
                    status = 'Open'
                
                sla_hours = {'Low': 72, 'Medium': 24, 'High': 4}[severity]
                sla_deadline = created_at + timedelta(hours=sla_hours)
                
                is_sla_breached = False
                resolved_at = None
                
                if status == 'Resolved':
                    resolve_time = created_at + timedelta(hours=random.randint(1, sla_hours + 10))
                    resolved_at = resolve_time
                    if resolve_time > sla_deadline:
                        is_sla_breached = True
                else:
                    if now > sla_deadline:
                        is_sla_breached = True
                
                # Guarantee 1-2 SLA breached Open/In-progress tickets
                if i < 2:
                    created_at = now - timedelta(days=5)
                    sla_deadline = created_at + timedelta(hours=sla_hours)
                    is_sla_breached = True
                    status = 'Open'
                
                assigned_to_id = demo_user.id if status != 'Open' else None
                
                t = Ticket(
                    title=title,
                    description=desc,
                    severity=severity,
                    status=status,
                    creator_id=demo_user.id,
                    assigned_to_id=assigned_to_id,
                    created_at=created_at,
                    sla_deadline=sla_deadline,
                    resolved_at=resolved_at,
                    is_sla_breached=is_sla_breached
                )
                tickets_to_add.append(t)
                
            db.session.add_all(tickets_to_add)
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
