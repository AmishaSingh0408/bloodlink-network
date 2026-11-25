
"""
BloodLink Network - simulated hospital coordination agent.

Converts supplier recommendations into human-reviewable transfer requests.
Uses SQLite to persist requests and their approval/rejection history.

This module does not contact hospitals, reserve stock, or execute transfers.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


# Store the database in the project's data directory.
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "coordination.db"

_lock = Lock()


def _get_connection():
    """Create a connection to the SQLite database."""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _initialize_database():
    """Create the transfer requests table if it does not exist."""
    with _get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transfer_requests (
                request_id TEXT PRIMARY KEY,
                shortage_hospital TEXT NOT NULL,
                supplier_hospital TEXT NOT NULL,
                blood_type TEXT NOT NULL,
                recommended_units INTEGER NOT NULL,
                required_units INTEGER NOT NULL,
                distance_km REAL NOT NULL,
                shortage_date TEXT,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                decision_note TEXT,
                decided_at TEXT,
                simulation_only INTEGER NOT NULL DEFAULT 1
            )
        """)


def _priority(required_units, projected_stock, safety_stock):
    """Assign a transparent operational priority from the projected stock gap."""
    gap = max(0.0, float(safety_stock) - float(projected_stock))

    if float(projected_stock) < 0:
        return "CRITICAL"
    if gap >= max(10.0, float(required_units) * 0.75):
        return "HIGH"
    if gap > 0:
        return "MEDIUM"
    return "LOW"


def _rows_to_dicts(rows):
    """Convert SQLite rows into ordinary dictionaries."""
    return [dict(row) for row in rows]


def build_transfer_requests(matching_results):
    """
    Create one pending simulated request per recommended supplier allocation.

    If requests already exist, return them instead of generating duplicates.
    """
    with _lock:
        with _get_connection() as connection:
            existing = connection.execute(
                "SELECT * FROM transfer_requests ORDER BY rowid"
            ).fetchall()

            if existing:
                return _rows_to_dicts(existing)

            for case in matching_results:
                for recommendation in case.get("recommendations", []):
                    required = int(case.get("required_units", 0))
                    projected = float(case.get("current_stock", 0))
                    safety = float(case.get("safety_stock", 0))

                    request = {
                        "request_id": str(uuid4()),
                        "shortage_hospital": case["hospital"],
                        "supplier_hospital": recommendation["supplier_hospital"],
                        "blood_type": case["blood_type"],
                        "recommended_units": int(
                            recommendation["recommended_transfer"]
                        ),
                        "required_units": required,
                        "distance_km": float(recommendation["distance_km"]),
                        "shortage_date": str(case.get("shortage_date", "")),
                        "priority": _priority(required, projected, safety),
                        "status": "PENDING_APPROVAL",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "decision_note": None,
                        "decided_at": None,
                        "simulation_only": 1,
                    }

                    columns = ", ".join(request.keys())
                    placeholders = ", ".join("?" for _ in request)

                    connection.execute(
                        f"""
                        INSERT INTO transfer_requests ({columns})
                        VALUES ({placeholders})
                        """,
                        tuple(request.values()),
                    )

            rows = connection.execute(
                "SELECT * FROM transfer_requests ORDER BY rowid"
            ).fetchall()

            return _rows_to_dicts(rows)


def list_transfer_requests():
    """Return all saved transfer requests."""
    with _get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM transfer_requests ORDER BY rowid"
        ).fetchall()

    return _rows_to_dicts(rows)


def decide_transfer_request(request_id, decision, note=None):
    """Record a human approval/rejection; never execute a physical transfer."""
    normalized = str(decision).strip().upper()

    if normalized not in {"APPROVE", "REJECT"}:
        raise ValueError("decision must be APPROVE or REJECT")

    with _lock:
        with _get_connection() as connection:
            existing = connection.execute(
                """
                SELECT * FROM transfer_requests
                WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()

            if existing is None:
                return None

            if existing["status"] != "PENDING_APPROVAL":
                raise ValueError("only pending requests can be decided")

            new_status = (
                "APPROVED_SIMULATED"
                if normalized == "APPROVE"
                else "REJECTED"
            )

            decided_at = datetime.now(timezone.utc).isoformat()

            connection.execute(
                """
                UPDATE transfer_requests
                SET status = ?, decision_note = ?, decided_at = ?
                WHERE request_id = ?
                """,
                (new_status, note, decided_at, request_id),
            )

            updated = connection.execute(
                """
                SELECT * FROM transfer_requests
                WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()

            return dict(updated)


# Initialize the database when this module is loaded.
_initialize_database()
