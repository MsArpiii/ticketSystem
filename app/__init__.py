import os
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
    
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    with app.app_context():
        db.create_all()

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.tickets import tickets_bp
    from app.routes.analytics import analytics_bp
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp

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

    return app
