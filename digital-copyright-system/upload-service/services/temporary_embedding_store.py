from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Optional


_lock = Lock()
_store: dict[str, dict] = {}
_ttl = timedelta(minutes=30)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cleanup_expired() -> None:
    now = _now()
    expired_ids = [
        check_id
        for check_id, item in _store.items()
        if item["expires_at"] <= now
    ]
    for check_id in expired_ids:
        _store.pop(check_id, None)


def save_temporary_embedding(
    check_id: str,
    feature: dict,
    decision: dict,
    can_register: bool,
    file_bytes: bytes | None = None,
    filename: str | None = None,
    report: dict | None = None,
) -> None:
    with _lock:
        _cleanup_expired()
        _store[check_id] = {
            "feature": feature,
            "decision": decision,
            "can_register": can_register,
            "file_bytes": file_bytes,
            "filename": filename,
            "manual_review_status": None,
            "manual_review_reason": None,
            "report": deepcopy(report) if report else None,
            "created_at": _now(),
            "expires_at": _now() + _ttl,
        }


def get_temporary_embedding(check_id: str) -> Optional[dict]:
    with _lock:
        _cleanup_expired()
        return _store.get(check_id)


def delete_temporary_embedding(check_id: str) -> None:
    with _lock:
        _store.pop(check_id, None)


def review_temporary_embedding(check_id: str, approved: bool, reason: Optional[str] = None) -> Optional[dict]:
    with _lock:
        _cleanup_expired()
        item = _store.get(check_id)

        if item is None:
            return None

        item["manual_review_status"] = "approved" if approved else "rejected"
        item["manual_review_reason"] = reason
        item["can_register"] = approved

        report = item.get("report")
        if report:
            report["can_register"] = approved
            report["registration_status"] = "allowed" if approved else "blocked"
            report["registration_reason"] = (
                "Registrasi diizinkan setelah hasil pengecekan disetujui melalui review manual."
                if approved
                else "Registrasi ditolak setelah hasil pengecekan ditolak melalui review manual."
            )
            report["manual_review_status"] = item["manual_review_status"]
            report["manual_review_reason"] = reason

        return item
