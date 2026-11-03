"""AES-256-GCM symmetric crypto and the X25519 + ML-KEM-768 hybrid mode."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import record_op
from ..auth import get_current_user
from ..crypto import classical, hybrid
from ..database import get_db
from ..models import User
from ..util import b64decode, b64encode

router = APIRouter(tags=["symmetric", "hybrid"])


class AesEncryptIn(BaseModel):
    plaintext: str
    key: str | None = None  # base64 32-byte key; generated if omitted


class AesDecryptIn(BaseModel):
    key: str
    nonce: str
    ciphertext: str


class HybridEncryptIn(BaseModel):
    x25519_public_key: str
    kem_public_key: str
    plaintext: str


class HybridDecryptIn(BaseModel):
    x25519_private_key: str
    kem_private_key: str
    x25519_public_key: str
    kem_ciphertext: str
    nonce: str
    ciphertext: str


@router.post("/api/symmetric/encrypt")
def aes_encrypt(body: AesEncryptIn, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    key = b64decode(body.key, "key") if body.key else classical.aes_keygen()
    if len(key) != 32:
        raise HTTPException(status_code=400, detail="AES key must be 32 bytes (AES-256)")
    nonce, ct = classical.aes_encrypt(key, body.plaintext.encode("utf-8"))
    record_op(db, user, "aes_encrypt", "AES-256-GCM")
    return {"key": b64encode(key), "nonce": b64encode(nonce),
            "ciphertext": b64encode(ct)}


@router.post("/api/symmetric/decrypt")
def aes_decrypt(body: AesDecryptIn, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    key = b64decode(body.key, "key")
    nonce = b64decode(body.nonce, "nonce")
    ct = b64decode(body.ciphertext, "ciphertext")
    try:
        pt = classical.aes_decrypt(key, nonce, ct)
    except Exception:
        record_op(db, user, "aes_decrypt", "AES-256-GCM", success=False)
        raise HTTPException(status_code=400, detail="Authentication failed: ciphertext tampered or wrong key")
    record_op(db, user, "aes_decrypt", "AES-256-GCM")
    return {"plaintext": pt.decode("utf-8")}


@router.post("/api/hybrid/keygen")
def hybrid_keygen(user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    record_op(db, user, "keygen", "Hybrid-X25519-ML-KEM-768")
    return {**hybrid.hybrid_keygen(),
            "warning": "Private keys are shown only once and are never stored server-side."}


@router.post("/api/hybrid/encrypt")
def hybrid_encrypt(body: HybridEncryptIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    try:
        x_pub = b64decode(body.x25519_public_key, "x25519_public_key")
        kem_pub = b64decode(body.kem_public_key, "kem_public_key")
        result = hybrid.hybrid_encrypt(x_pub, kem_pub, body.plaintext.encode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Hybrid encryption failed: check public keys")
    record_op(db, user, "hybrid_encrypt", "Hybrid-X25519-ML-KEM-768")
    return {**result,
            "assumption": "Secure if EITHER X25519 or ML-KEM-768 holds (standard hybrid KEM combiner).",
            "construction": "HKDF-SHA256(X25519_secret || ML-KEM-768_secret) -> AES-256-GCM key"}


@router.post("/api/hybrid/decrypt")
def hybrid_decrypt(body: HybridDecryptIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    try:
        pt = hybrid.hybrid_decrypt(
            b64decode(body.x25519_private_key, "x25519_private_key"),
            b64decode(body.kem_private_key, "kem_private_key"),
            b64decode(body.x25519_public_key, "x25519_public_key"),
            b64decode(body.kem_ciphertext, "kem_ciphertext"),
            b64decode(body.nonce, "nonce"),
            b64decode(body.ciphertext, "ciphertext"))
    except Exception:
        record_op(db, user, "hybrid_decrypt", "Hybrid-X25519-ML-KEM-768", success=False)
        raise HTTPException(status_code=400, detail="Hybrid decryption failed: authentication error or wrong keys")
    record_op(db, user, "hybrid_decrypt", "Hybrid-X25519-ML-KEM-768")
    return {"plaintext": pt.decode("utf-8")}
