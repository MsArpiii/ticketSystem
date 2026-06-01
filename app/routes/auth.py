from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from sqlalchemy.exc import SQLAlchemyError

auth_bp = Blueprint('auth', __name__)



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tickets.dashboard'))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        user = db.session.scalar(db.select(User).where(User.username == username))
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("✅ Successfully logged in!", "success")
            return redirect(url_for('tickets.dashboard'))
            
        flash("❌ Invalid username or password", "danger")
        
    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('tickets.dashboard'))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password or len(password) < 6:
            flash("❌ Username required and password must be at least 6 characters.", "danger")
            return redirect(url_for('auth.register'))
            
        # First registered user becomes Admin
        count = db.session.query(User).count()
        role = 'admin' if count == 0 else 'user'
        
        hashed_pw = generate_password_hash(password)
        
        existing = db.session.scalar(db.select(User).where(User.username == username))
        if existing:
            flash("❌ Username already exists", "danger")
            return render_template("auth/register.html")
            
        try:
            new_user = User(username=username, password=hashed_pw, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash("✅ Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except SQLAlchemyError:
            db.session.rollback()
            flash("❌ A database error occurred during registration. Please try again.", "danger")
            return render_template("auth/register.html")
            
    return render_template("auth/register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 Logged out successfully", "success")
    return redirect(url_for('main.home'))

@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@auth_bp.route("/admin/users")
@login_required
def admin_users():
    if not current_user.is_admin:
        flash("You do not have permission to view this page.")
        return redirect(url_for('tickets.dashboard'))
    
    users = db.session.scalars(db.select(User)).all()
    return render_template("admin_users.html", users=users)
