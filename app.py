
from flask import Flask, render_template, abort
import sqlite3
from datetime import datetime, timezone

app = Flask(__name__)

DATABASE = "kits.db"


# Connect to our database
def get_connection():
    return sqlite3.connect(DATABASE)


# Create the database tables
def setup_database():
    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS kits (
                kit_id TEXT PRIMARY KEY
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kit_id TEXT NOT NULL,
                scanned_at TEXT NOT NULL,
                FOREIGN KEY (kit_id) REFERENCES kits(kit_id)
            )
        """)

        # Add three example kits
        for kit_id in ["KIT-001", "KIT-002", "KIT-003"]:
            connection.execute(
                "INSERT OR IGNORE INTO kits (kit_id) VALUES (?)",
                (kit_id,)
            )


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Individual kit page
@app.route("/kit/<kit_id>")
def kit_page(kit_id):

    with get_connection() as connection:

        # Check if the kit exists
        kit = connection.execute(
            "SELECT kit_id FROM kits WHERE kit_id = ?",
            (kit_id,)
        ).fetchone()

        if kit is None:
            abort(404)

        # Record the scan time
        scanned_at = datetime.now(timezone.utc).isoformat()

        connection.execute(
            "INSERT INTO scans (kit_id, scanned_at) VALUES (?, ?)",
            (kit_id, scanned_at)
        )

    return render_template("kit.html", kit_id=kit_id)


# Development-only page to view kit scan counts
@app.route("/report")
def report():
    with get_connection() as connection:
        results = connection.execute("""
            SELECT
                kits.kit_id,
                COUNT(scans.id) AS scan_count,
                CASE
                    WHEN COUNT(scans.id) > 0 THEN 'Scanned'
                    ELSE 'Not Scanned'
                END AS status
            FROM kits
            LEFT JOIN scans
                ON kits.kit_id = scans.kit_id
            GROUP BY kits.kit_id
            ORDER BY kits.kit_id
        """).fetchall()

    return render_template("report.html", results=results)

if __name__ == "__main__":
    setup_database()
    app.run(debug=True)

