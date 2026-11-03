"""Admin-only endpoints. Non-admin users get 403 (enforced in auth)."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..models import AuditEntry, CryptoOperation, FileRecord, Message, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
def users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.id.asc()).all()
    return [{"id": u.id, "username": u.username, "role": u.role,
             "kem_key_published": bool(u.kem_public_key),
             "dsa_key_published": bool(u.dsa_public_key),
             "created_at": str(u.created_at)} for u in rows]


@router.get("/stats")
def stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "users": db.query(func.count(User.id)).scalar(),
        "operations": db.query(func.count(CryptoOperation.id)).scalar(),
        "messages": db.query(func.count(Message.id)).scalar(),
        "files": db.query(func.count(FileRecord.id)).scalar(),
        "audit_entries": db.query(func.count(AuditEntry.id)).scalar(),
    }


@router.get("/audit")
def audit(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AuditEntry).order_by(AuditEntry.id.desc()).limit(100).all()
    return [{"id": r.id, "actor": r.actor, "action": r.action, "details": r.details,
             "entry_hash": r.entry_hash, "created_at": str(r.created_at)} for r in rows]
