"""Save requests before attempting notification; never retry ambiguous sends.

The configured SQLite path must reside on persistent, private storage in
production. A local file on an ephemeral hosting instance is not durable storage.
"""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Callable


def submit_reservation(
    database: str, request_id: str, payload: dict, notify: Callable[..., None]
) -> str:
    """Return sent/needs_attention/unknown; keep one attempt per request ID.

    Persist `unknown` before the external call: a process crash or lost HTTP
    acknowledgement must never make a retry look safe. Staff must reconcile
    unknown deliveries with Telegram. Exceptions never enter the database.
    """
    if not database or database == ":memory:":
        raise ValueError("Configure RESERVATION_DB_PATH on persistent storage")
    path = Path(database).expanduser()
    if not path.is_absolute():
        raise ValueError("RESERVATION_DB_PATH must be an absolute path")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    with closing(sqlite3.connect(path, timeout=10)) as connection:
        with connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS reservations (
                request_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            inserted = connection.execute(
                "INSERT OR IGNORE INTO reservations(request_id,payload,status) VALUES (?,?,?)",
                (request_id, encoded, "unknown"),
            ).rowcount
            if not inserted:
                saved, status = connection.execute(
                    "SELECT payload,status FROM reservations WHERE request_id=?", (request_id,)
                ).fetchone()
                if saved != encoded:
                    raise ValueError("Request ID already belongs to another payload")
                return status
        # The transaction above has committed before any external side effect.
        try:
            notify(**payload)
        except KeyError:
            status = "needs_attention"  # configuration missing, no successful notification
        except Exception:
            status = "unknown"  # includes timeouts; Telegram may have accepted it
        else:
            status = "sent"
        with connection:
            connection.execute(
                "UPDATE reservations SET status=?,updated_at=CURRENT_TIMESTAMP WHERE request_id=?",
                (status, request_id),
            )
        return status
