"""Authentication endpoints + public-key publishing."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..audit import append_audit, record_op
from ..auth import create_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(..., min_length=6, max_length=72)


class LoginIn(BaseModel):
    username: str
    password: str


class PublishKeysIn(BaseModel):
    kem_public_key: str | None = None
    dsa_public_key: str | None = None


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if len(body.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password must be at most 72 bytes")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    append_audit(db, body.username, "user_registered", "new account created")
    return {"username": user.username, "role": user.role, "token": create_token(user)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    append_audit(db, user.username, "user_login", "login successful")
    return {"username": user.username, "role": user.role, "token": create_token(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "username": user.username,
        "role": user.role,
        "kem_public_key": user.kem_public_key,
        "dsa_public_key": user.dsa_public_key,
        "created_at": str(user.created_at),
    }


@router.post("/publish-keys")
def publish_keys(body: PublishKeysIn, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    if body.kem_public_key:
        user.kem_public_key = body.kem_public_key
    if body.dsa_public_key:
        user.dsa_public_key = body.dsa_public_key
    db.commit()
    record_op(db, user, "publish_keys", "ML-KEM-768/ML-DSA-65")
    append_audit(db, user.username, "keys_published", "public keys published to profile")
    return {"username": user.username, "kem_public_key_set": bool(user.kem_public_key),
            "dsa_public_key_set": bool(user.dsa_public_key)}
