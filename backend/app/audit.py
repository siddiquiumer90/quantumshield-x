"""Hash-chained audit log helpers.

entry_hash = SHA-256(prev_hash || actor || action || details).
The chain starts at the fixed GENESIS hash. Verification recomputes every
link; any edited, deleted, or inserted row breaks it.
"""
import hashlib
import json

from sqlalchemy.orm import Session

from .models import AuditEntry, CryptoOperation

GENESIS = "0" * 64


def _canonical(actor: str, action: str, details: str) -> str:
    return json.dumps({"actor": actor, "action": action, "details": details},
                      sort_keys=True, separators=(",", ":"))


def append_audit(db: Session, actor: str, action: str, details: str = "") -> AuditEntry:
    last = db.query(AuditEntry).order_by(AuditEntry.id.desc()).first()
    prev = last.entry_hash if last else GENESIS
    entry_hash = hashlib.sha256(
        (prev + _canonical(actor, action, details)).encode("utf-8")).hexdigest()
    entry = AuditEntry(actor=actor, action=action, details=details[:512],
                       prev_hash=prev, entry_hash=entry_hash)
    db.add(entry)
    db.commit()
    return entry


def verify_chain(db: Session) -> dict:
    entries = db.query(AuditEntry).order_by(AuditEntry.id.asc()).all()
    prev = GENESIS
    checked = 0
    for e in entries:
        expected = hashlib.sha256(
            (prev + _canonical(e.actor, e.action, e.details)).encode("utf-8")
        ).hexdigest()
        if e.prev_hash != prev or e.entry_hash != expected:
            return {"valid": False, "checked": checked, "broken_at_id": e.id,
                    "total": len(entries)}
        prev = e.entry_hash
        checked += 1
    return {"valid": True, "checked": checked, "broken_at_id": None,
            "total": len(entries)}


def record_op(db: Session, user, operation: str, algorithm: str, success: bool = True):
    """Record a dashboard operation (metadata only, never secrets)."""
    db.add(CryptoOperation(
        user_id=user.id if user else None,
        username=user.username if user else None,
        operation=operation, algorithm=algorithm, success=1 if success else 0))
    db.commit()
