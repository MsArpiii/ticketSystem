from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

DB_NAME = "tickets.db"

# ---------- DATABASE CONNECTION ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- INIT DATABASE ----------
def init_db():
    conn = get_db()
    c = conn.cursor()

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

    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        severity = request.form["severity"]

        conn = get_db()
        conn.execute(
            "INSERT INTO tickets (title, description, severity, created_at) VALUES (?, ?, ?, ?)",
            (title, desc, severity, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        conn.close()

        flash("✅ Ticket Created Successfully!")
        return redirect(url_for("dashboard"))

    return render_template("home.html")

# ---------- DASHBOARD (FIXED & MERGED) ----------
@app.route("/dashboard")
def dashboard():
    conn = get_db()

    search = request.args.get("search", "")
    severity = request.args.get("severity", "")

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if severity:
        query += " AND severity = ?"
        params.append(severity)

    tickets = conn.execute(query, params).fetchall()

    # Stats
    total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    open_t = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Resolved'").fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        tickets=tickets,
        search=search,
        total=total,
        open=open_t,
        resolved=resolved
    )

# ---------- RESOLVE ----------
@app.route("/resolve/<int:id>")
def resolve(id):
    conn = get_db()
    conn.execute("UPDATE tickets SET status='Resolved' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("✔ Ticket Resolved")
    return redirect(url_for("dashboard"))

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM tickets WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("🗑 Ticket Deleted")
    return redirect(url_for("dashboard"))

# ---------- UPDATE ----------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db()

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        severity = request.form["severity"]

        conn.execute(
            "UPDATE tickets SET title=?, description=?, severity=? WHERE id=?",
            (title, desc, severity, id)
        )
        conn.commit()
        conn.close()

        flash("✏ Ticket Updated")
        return redirect(url_for("dashboard"))

    ticket = conn.execute("SELECT * FROM tickets WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit.html", ticket=ticket)

# ---------- ANALYTICS ----------
@app.route("/analytics")
def analytics():
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    open_t = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Resolved'").fetchone()[0]

    severity_data = conn.execute("""
        SELECT severity, COUNT(*) as count
        FROM tickets
        GROUP BY severity
    """).fetchall()

    conn.close()

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