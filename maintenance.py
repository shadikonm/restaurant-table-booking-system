"""SQLite backups and scheduled email reminders.
Run: python maintenance.py backup | restore PATH | reminders
Use OS scheduler for reminders (e.g. every 15 minutes).
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from app import DATABASE, init_db, send_booking_email

ROOT = Path(__file__).resolve().parent
BACKUPS = ROOT / "backups"


def backup():
    BACKUPS.mkdir(exist_ok=True)
    target = BACKUPS / f"restaurant_{datetime.now():%Y%m%d_%H%M%S}.db"
    with sqlite3.connect(DATABASE) as source, sqlite3.connect(target) as destination:
        source.backup(destination)
    print(f"Backup created: {target}")
    return target


def restore(path):
    source_path = Path(path).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    with sqlite3.connect(source_path) as source:
        integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"Invalid backup: {integrity}")
        with sqlite3.connect(DATABASE) as destination:
            source.backup(destination)
    print("Restored database. Restart Flask application.")


def reminders():
    if not __import__("os").environ.get("SMTP_HOST"):
        print("SMTP_HOST not set; reminders not sent")
        return
    init_db()
    now = datetime.now()
    end = now + timedelta(hours=24)
    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT r.id, r.table_number, r.reservation_date, r.reservation_time, u.email
            FROM reservations r JOIN users u ON u.id = r.user_id
            LEFT JOIN email_reminders m ON m.reservation_id = r.id
            WHERE r.status = 'confirmed' AND m.reservation_id IS NULL
              AND (r.reservation_date || ' ' || r.reservation_time) > ?
              AND (r.reservation_date || ' ' || r.reservation_time) <= ?
        """,
            (now.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M")),
        ).fetchall()
        for row in rows:
            ok = send_booking_email(
                row["email"],
                "Напоминание о бронировании TABLE",
                f"Напоминаем: бронь №{row['id']}, стол №{row['table_number']}, {row['reservation_date']} в {row['reservation_time']}.",
            )
            if ok:
                connection.execute(
                    "INSERT OR IGNORE INTO email_reminders (reservation_id) VALUES (?)",
                    (row["id"],),
                )
        connection.commit()
    print(f"Checked {len(rows)} reservations")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "backup"
    if command == "backup":
        backup()
    elif command == "restore" and len(sys.argv) == 3:
        restore(sys.argv[2])
    elif command == "reminders":
        reminders()
    else:
        raise SystemExit(
            "Usage: python maintenance.py backup | restore FILE | reminders"
        )
