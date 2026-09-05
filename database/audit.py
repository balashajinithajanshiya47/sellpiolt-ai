import sqlite3
import json
from datetime import datetime

DB_NAME = "sellpilot.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action TEXT,
            details TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


def log_event(action, details, status="SUCCESS"):
    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT INTO audit_log
        (timestamp, action, details, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            action,
            details,
            status
        )
    )

    conn.commit()
    conn.close()


def get_audit_logs():
    conn = sqlite3.connect(DB_NAME)

    rows = conn.execute(
        """
        SELECT timestamp, action, details, status
        FROM audit_log
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return rows


def get_audit_logs_json():
    """Return the complete audit trail as JSON."""
    logs = get_audit_logs()

    data = []
    for timestamp, action, details, status in logs:
        data.append({
            "timestamp": timestamp,
            "action": action,
            "details": details,
            "status": status
        })

    return json.dumps(data, indent=2, ensure_ascii=False)


def clear_test_audit_entries():
    """Remove the old test entry if it exists."""
    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        DELETE FROM audit_log
        WHERE details LIKE '%Audit system working integrated upto this%'
        """
    )

    conn.commit()
    conn.close()
