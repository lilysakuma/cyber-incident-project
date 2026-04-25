import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "project.db"

app = Flask(__name__)
app.secret_key = "dev-secret-key"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_db_connection()
    schema_path = BASE_DIR / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db_connection()
    seed_path = BASE_DIR / "seed.sql"
    with open(seed_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db_connection()
    incidents = conn.execute("""
        SELECT i.incident_id, i.title, i.incident_type, i.status, i.severity,
               i.created_at, u.name AS reporter_name
        FROM incidents i
        JOIN users u ON i.reporter_id = u.user_id
        ORDER BY i.incident_id DESC
    """).fetchall()
    conn.close()
    return render_template("home.html", incidents=incidents)


@app.route("/init")
def initialize_database():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    seed_db()
    flash("Database created and seeded successfully.")
    return redirect(url_for("home"))


@app.route("/incident/create", methods=["GET", "POST"])
def create_incident():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users ORDER BY name").fetchall()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        incident_type = request.form["incident_type"].strip()
        status = request.form["status"]
        severity = request.form["severity"]
        reporter_id = request.form["reporter_id"]
        assignee_id = request.form["assignee_id"] or None

        conn.execute("""
            INSERT INTO incidents
            (title, description, incident_type, status, severity, reporter_id, assignee_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (title, description, incident_type, status, severity, reporter_id, assignee_id))

        conn.commit()
        conn.close()
        flash("Incident created successfully.")
        return redirect(url_for("home"))

    conn.close()
    return render_template("create_incident.html", users=users)


@app.route("/incident/<int:incident_id>")
def incident_detail(incident_id):
    conn = get_db_connection()

    incident = conn.execute("""
        SELECT i.*, 
               r.name AS reporter_name,
               a.name AS assignee_name
        FROM incidents i
        JOIN users r ON i.reporter_id = r.user_id
        LEFT JOIN users a ON i.assignee_id = a.user_id
        WHERE i.incident_id = ?
    """, (incident_id,)).fetchone()

    if incident is None:
        conn.close()
        return "Incident not found", 404

    evidence_items = conn.execute("""
        SELECT e.*, u.name AS added_by_name
        FROM evidence e
        LEFT JOIN users u ON e.added_by = u.user_id
        WHERE e.incident_id = ?
        ORDER BY e.evidence_id DESC
    """, (incident_id,)).fetchall()

    tasks = conn.execute("""
        SELECT t.*, u.name AS created_by_name
        FROM tasks t
        JOIN users u ON t.created_by = u.user_id
        WHERE t.incident_id = ?
        ORDER BY t.task_id DESC
    """, (incident_id,)).fetchall()

    assets = conn.execute("""
        SELECT a.*
        FROM assets a
        JOIN incident_asset ia ON a.asset_id = ia.asset_id
        WHERE ia.incident_id = ?
        ORDER BY a.asset_id DESC
    """, (incident_id,)).fetchall()

    tags = conn.execute("""
        SELECT t.*
        FROM tags t
        JOIN incident_tag it ON t.tag_id = it.tag_id
        WHERE it.incident_id = ?
        ORDER BY t.name
    """, (incident_id,)).fetchall()

    vuln_matches = conn.execute("""
        SELECT DISTINCT v.*
        FROM vulnerabilities v
        JOIN evidence e ON e.value = v.cve_id
        WHERE e.incident_id = ? AND e.evidence_type = 'cve'
    """, (incident_id,)).fetchall()

    related_incidents = conn.execute("""
        SELECT DISTINCT i.incident_id, i.title, i.status
        FROM incidents i
        JOIN evidence e2 ON i.incident_id = e2.incident_id
        WHERE i.incident_id != ?
          AND e2.value IN (
              SELECT value
              FROM evidence
              WHERE incident_id = ?
                AND evidence_type IN ('cve', 'url', 'domain', 'hash')
          )
        ORDER BY i.incident_id DESC
    """, (incident_id, incident_id)).fetchall()

    users = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
    conn.close()

    return render_template(
        "incident_detail.html",
        incident=incident,
        evidence_items=evidence_items,
        tasks=tasks,
        assets=assets,
        tags=tags,
        vuln_matches=vuln_matches,
        related_incidents=related_incidents,
        users=users
    )


@app.route("/incident/<int:incident_id>/edit", methods=["GET", "POST"])
def edit_incident(incident_id):
    conn = get_db_connection()

    incident = conn.execute(
        "SELECT * FROM incidents WHERE incident_id = ?",
        (incident_id,)
    ).fetchone()

    users = conn.execute("SELECT * FROM users ORDER BY name").fetchall()

    if incident is None:
        conn.close()
        return "Incident not found", 404

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        incident_type = request.form["incident_type"].strip()
        status = request.form["status"]
        severity = request.form["severity"]
        assignee_id = request.form["assignee_id"] or None

        conn.execute("""
            UPDATE incidents
            SET title = ?,
                description = ?,
                incident_type = ?,
                status = ?,
                severity = ?,
                assignee_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE incident_id = ?
        """, (title, description, incident_type, status, severity, assignee_id, incident_id))

        conn.commit()
        conn.close()
        flash("Incident updated successfully.")
        return redirect(url_for("incident_detail", incident_id=incident_id))

    conn.close()
    return render_template("edit_incident.html", incident=incident, users=users)


@app.route("/incident/<int:incident_id>/delete", methods=["POST"])
def delete_incident(incident_id):
    conn = get_db_connection()

    conn.execute("DELETE FROM tasks WHERE incident_id = ?", (incident_id,))
    conn.execute("DELETE FROM evidence WHERE incident_id = ?", (incident_id,))
    conn.execute("DELETE FROM incident_tag WHERE incident_id = ?", (incident_id,))
    conn.execute("DELETE FROM incident_asset WHERE incident_id = ?", (incident_id,))
    conn.execute("DELETE FROM incidents WHERE incident_id = ?", (incident_id,))

    conn.commit()
    conn.close()

    flash("Incident deleted successfully.")
    return redirect(url_for("home"))


@app.route("/incident/<int:incident_id>/evidence/add", methods=["GET", "POST"])
def add_evidence(incident_id):
    conn = get_db_connection()

    incident = conn.execute(
        "SELECT * FROM incidents WHERE incident_id = ?",
        (incident_id,)
    ).fetchone()

    users = conn.execute("SELECT * FROM users ORDER BY name").fetchall()

    if incident is None:
        conn.close()
        return "Incident not found", 404

    if request.method == "POST":
        evidence_type = request.form["evidence_type"]
        value = request.form["value"].strip()
        added_by = request.form["added_by"]
        file_path = request.form["file_path"].strip()

        try:
            conn.execute("""
                INSERT INTO evidence (incident_id, evidence_type, value, file_path, added_by)
                VALUES (?, ?, ?, ?, ?)
            """, (incident_id, evidence_type, value, file_path or None, added_by))
            conn.commit()
            flash("Evidence added successfully.")
        except sqlite3.IntegrityError:
            flash("That evidence already exists for this incident.")

        conn.close()
        return redirect(url_for("incident_detail", incident_id=incident_id))

    conn.close()
    return render_template("add_evidence.html", incident=incident, users=users)


@app.route("/incident/<int:incident_id>/task/add", methods=["GET", "POST"])
def add_task(incident_id):
    conn = get_db_connection()

    incident = conn.execute(
        "SELECT * FROM incidents WHERE incident_id = ?",
        (incident_id,)
    ).fetchone()

    users = conn.execute("SELECT * FROM users ORDER BY name").fetchall()

    if incident is None:
        conn.close()
        return "Incident not found", 404

    if request.method == "POST":
        task_type = request.form["task_type"]
        status = request.form["status"]
        due_date = request.form["due_date"]
        notes = request.form["notes"].strip()
        created_by = request.form["created_by"]

        conn.execute("""
            INSERT INTO tasks (incident_id, created_by, task_type, status, due_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (incident_id, created_by, task_type, status, due_date or None, notes))

        conn.commit()
        conn.close()
        flash("Task added successfully.")
        return redirect(url_for("incident_detail", incident_id=incident_id))

    conn.close()
    return render_template("add_task.html", incident=incident, users=users)


if __name__ == "__main__":
    app.run(debug=True)