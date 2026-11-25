"""
BloodLink Network - simulated hospital coordination agent.

Converts supplier recommendations into human-reviewable transfer requests.
This module does not contact hospitals, reserve stock, or execute transfers.
"""

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4


_requests = []
_lock = Lock()


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


def build_transfer_requests(matching_results):
    """
    Create one pending simulated request per recommended supplier allocation.
    Repeated calls return the existing generated requests instead of duplicates.
    """
    with _lock:
        if _requests:
            return list(_requests)

        for case in matching_results:
            for recommendation in case.get("recommendations", []):
                required = int(case.get("required_units", 0))
                projected = float(case.get("current_stock", 0))
                safety = float(case.get("safety_stock", 0))
                _requests.append({
                    "request_id": str(uuid4()),
                    "shortage_hospital": case["hospital"],
                    "supplier_hospital": recommendation["supplier_hospital"],
                    "blood_type": case["blood_type"],
                    "recommended_units": int(recommendation["recommended_transfer"]),
                    "required_units": required,
                    "distance_km": float(recommendation["distance_km"]),
                    "shortage_date": str(case.get("shortage_date", "")),
                    "priority": _priority(required, projected, safety),
                    "status": "PENDING_APPROVAL",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "decision_note": None,
                    "decided_at": None,
                    "simulation_only": True,
                })
        return list(_requests)


def list_transfer_requests():
    with _lock:
        return [dict(item) for item in _requests]


def decide_transfer_request(request_id, decision, note=None):
    """Record a human approval/rejection; never execute a physical transfer."""
    normalized = str(decision).strip().upper()
    if normalized not in {"APPROVE", "REJECT"}:
        raise ValueError("decision must be APPROVE or REJECT")

    with _lock:
        for item in _requests:
            if item["request_id"] == request_id:
                if item["status"] != "PENDING_APPROVAL":
                    raise ValueError("only pending requests can be decided")
                item["status"] = (
                    "APPROVED_SIMULATED" if normalized == "APPROVE"
                    else "REJECTED"
                )
                item["decision_note"] = note
                item["decided_at"] = datetime.now(timezone.utc).isoformat()
                return dict(item)
    return None
