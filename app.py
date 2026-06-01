# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

DB_NAME = "tickets.db"

# ---------- DATABASE CONNECTION LIFECYCLE ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ---------- INIT DATABASE ----------
def init_db():
    with app.app_context():
        db = get_db()
        c = db.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT DEFAULT 'Open',
                created_at TEXT
            )
        ''')

        db.commit()

init_db()

# ---------- HOME ----------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        severity = request.form.get("severity", "").strip()

        # Input Validation
        if not title or not desc or severity not in ['Low', 'Medium', 'High']:
            flash("❌ Invalid input. Please ensure all fields are correctly filled.", "danger")
            return redirect(url_for("home"))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO tickets (title, description, severity, created_at) VALUES (?, ?, ?, ?)",
                (title, desc, severity, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            db.commit()
            flash("✅ Ticket Created Successfully!")
            return redirect(url_for("dashboard"))
        except sqlite3.Error as e:
            flash(f"❌ Database error: {e}", "danger")
            return redirect(url_for("home"))

    return render_template("home.html")

# ---------- DASHBOARD (OPTIMIZED) ----------
@app.route("/dashboard")
def dashboard():
    db = get_db()

    search = request.args.get("search", "")
    severity = request.args.get("severity", "")
    
    # Pagination Setup
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if severity:
        query += " AND severity = ?"
        params.append(severity)

    # Calculate total pages for pagination
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    
    try:
        total_filtered = db.execute(count_query, params).fetchone()[0]
    except sqlite3.Error:
        total_filtered = 0

    total_pages = (total_filtered + per_page - 1) // per_page
    if total_pages == 0: total_pages = 1

    # Clamp page out of bounds
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    # Apply limits
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    try:
        tickets = db.execute(query, params).fetchall()
        
        # Consolidated stats query (overall app stats)
        stats_query = db.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status").fetchall()
        
        total = sum(row[1] for row in stats_query)
        open_t = sum(row[1] for row in stats_query if row[0] == 'Open')
        resolved = sum(row[1] for row in stats_query if row[0] == 'Resolved')

    except sqlite3.Error as e:
        flash(f"❌ Failed to load dashboard: {e}", "danger")
        tickets = []
        total = open_t = resolved = 0

    return render_template(
        "dashboard.html",
        tickets=tickets,
        search=search,
        total=total,
        open=open_t,
        resolved=resolved,
        page=page,
        total_pages=total_pages
    )

# ---------- RESOLVE ----------
@app.route("/resolve/<int:id>")
def resolve(id):
    db = get_db()
    try:
        cursor = db.execute("UPDATE tickets SET status='Resolved' WHERE id=?", (id,))
        if cursor.rowcount == 0:
            flash("❌ Ticket not found.", "danger")
        else:
            db.commit()
            flash("✔ Ticket Resolved")
    except sqlite3.Error as e:
        flash(f"❌ Database error: {e}", "danger")

    return redirect(url_for("dashboard"))

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM tickets WHERE id=?", (id,))
        if cursor.rowcount == 0:
            flash("❌ Ticket not found.", "danger")
        else:
            db.commit()
            flash("🗑 Ticket Deleted")
    except sqlite3.Error as e:
        flash(f"❌ Database error: {e}", "danger")

    return redirect(url_for("dashboard"))

# ---------- UPDATE ----------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = get_db()

    try:
        ticket = db.execute("SELECT * FROM tickets WHERE id=?", (id,)).fetchone()
    except sqlite3.Error as e:
        flash(f"❌ Database error: {e}", "danger")
        return redirect(url_for("dashboard"))

    # Edge Case: Non-existent ticket
    if not ticket:
        flash("❌ Ticket not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        severity = request.form.get("severity", "").strip()

        # Input Validation
        if not title or not desc or severity not in ['Low', 'Medium', 'High']:
            flash("❌ Invalid input. Please ensure all fields are correctly filled.", "danger")
            return redirect(url_for("edit", id=id))

        try:
            db.execute(
                "UPDATE tickets SET title=?, description=?, severity=? WHERE id=?",
                (title, desc, severity, id)
            )
            db.commit()
            flash("✏ Ticket Updated")
            return redirect(url_for("dashboard"))
        except sqlite3.Error as e:
            flash(f"❌ Database error: {e}", "danger")
            return redirect(url_for("edit", id=id))

    return render_template("edit.html", ticket=ticket)

# ---------- ANALYTICS (OPTIMIZED) ----------
@app.route("/analytics")
def analytics():
    db = get_db()

    try:
        stats_query = db.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status").fetchall()
        total = sum(row[1] for row in stats_query)
        open_t = sum(row[1] for row in stats_query if row[0] == 'Open')
        resolved = sum(row[1] for row in stats_query if row[0] == 'Resolved')

        severity_data = db.execute("""
            SELECT severity, COUNT(*) as count
            FROM tickets
            GROUP BY severity
        """).fetchall()
    except sqlite3.Error as e:
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

# ---------- ABOUT ----------
@app.route("/about")
def about():
    return render_template("about.html")

# ---------- ERROR HANDLING ----------
@app.errorhandler(404)
def not_found(e):
    return "<h2>404 - Page Not Found</h2>", 404

@app.errorhandler(500)
def server_error(e):
    return "<h2>500 - Internal Server Error</h2>", 500

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)