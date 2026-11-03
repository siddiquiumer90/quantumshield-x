"""User-to-user secure messaging.

Per message: ML-KEM-768 key establishment against the recipient's published
public key + AES-256-GCM encryption + ML-DSA-65 signature by the sender.
Messages are stored as ciphertext only. Private keys are supplied per request
(pasted from the sender's/recipient's one-time key download), used in memory
only, and never stored or logged.
"""
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import append_audit, record_op
from ..auth import get_current_user
from ..crypto import classical, pqc
from ..database import get_db
from ..models import Message, User
from ..util import b64decode, b64encode

router = APIRouter(prefix="/api/messages", tags=["messages"])

KEM_ALG = "ML-KEM-768"
SIG_ALG = "ML-DSA-65"


class SendIn(BaseModel):
    recipient_username: str
    plaintext: str
    signing_private_key: str  # base64 ML-DSA-65 private key (sender's own)


class DecryptIn(BaseModel):
    kem_private_key: str  # base64 ML-KEM-768 private key (recipient's own)


@router.post("/send")
def send(body: SendIn, user: User = Depends(get_current_user),
         db: Session = Depends(get_db)):
    recipient = db.query(User).filter(User.username == body.recipient_username).first()
    if recipient is None:
        raise HTTPException(status_code=404, detail="Recipient not found")
    if recipient.kem_public_key is None:
        raise HTTPException(status_code=400, detail="Recipient has not published an ML-KEM public key yet (Key Management page)")
    if user.dsa_public_key is None:
        raise HTTPException(status_code=400, detail="Publish your ML-DSA public key first (Key Management page)")
    try:
        kem_pub = b64decode(recipient.kem_public_key, "recipient kem_public_key")
        kem_ct, ss = pqc.kem_encaps_secret(KEM_ALG, kem_pub)
        key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                   info=b"quantumshield-x-message-v1").derive(ss)
        nonce, ct = classical.aes_encrypt(key, body.plaintext.encode("utf-8"))
        sig = pqc.sig_sign(SIG_ALG, b64decode(body.signing_private_key, "signing_private_key"),
                           body.plaintext.encode("utf-8"))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Message encryption failed: check your signing private key")
    msg = Message(sender_id=user.id, recipient_id=recipient.id, kem_algorithm=KEM_ALG,
                  kem_ciphertext=b64encode(kem_ct), nonce=b64encode(nonce),
                  ciphertext=b64encode(ct), signature=sig["signature"],
                  sender_dsa_public_key=user.dsa_public_key)
    db.add(msg)
    db.commit()
    record_op(db, user, "message_send", f"{KEM_ALG}+AES-256-GCM+{SIG_ALG}")
    append_audit(db, user.username, "message_sent", f"to={recipient.username}")
    return {"id": msg.id, "recipient": recipient.username,
            "status": "encrypted_and_stored", "kem": KEM_ALG, "signature": SIG_ALG}


def _serialise(m: Message, db: Session) -> dict:
    sender = db.query(User).filter(User.id == m.sender_id).first()
    recipient = db.query(User).filter(User.id == m.recipient_id).first()
    return {
        "id": m.id,
        "sender": sender.username if sender else "?",
        "recipient": recipient.username if recipient else "?",
        "kem_algorithm": m.kem_algorithm,
        "kem_ciphertext": m.kem_ciphertext,
        "nonce": m.nonce,
        "ciphertext": m.ciphertext,
        "signature": m.signature,
        "created_at": str(m.created_at),
    }


@router.get("/inbox")
def inbox(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Message).filter(Message.recipient_id == user.id).order_by(Message.id.desc()).all()
    return [_serialise(m, db) for m in rows]


@router.get("/sent")
def sent(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Message).filter(Message.sender_id == user.id).order_by(Message.id.desc()).all()
    return [_serialise(m, db) for m in rows]


@router.post("/{msg_id}/decrypt")
def decrypt(msg_id: int, body: DecryptIn, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    m = db.query(Message).filter(Message.id == msg_id).first()
    if m is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if m.recipient_id != user.id:
        raise HTTPException(status_code=403, detail="Only the recipient can decrypt this message")
    try:
        ss = pqc.kem_decaps_secret(KEM_ALG, b64decode(body.kem_private_key, "kem_private_key"),
                                   b64decode(m.kem_ciphertext, "kem_ciphertext"))
        key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                   info=b"quantumshield-x-message-v1").derive(ss)
        pt = classical.aes_decrypt(key, b64decode(m.nonce, "nonce"),
                                   b64decode(m.ciphertext, "ciphertext"))
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed: wrong private key or tampered message")
    record_op(db, user, "message_decrypt", KEM_ALG)
    return {"id": m.id, "plaintext": pt.decode("utf-8")}


# Verification needs the plaintext, which only the recipient can recover by
# decrypting first — so the verify endpoint takes the decrypted plaintext and
# checks it against the stored ML-DSA signature and sender public key.
class VerifyTextIn(BaseModel):
    message_id: int
    plaintext: str


@router.post("/verify-text")
def verify_text(body: VerifyTextIn, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    m = db.query(Message).filter(Message.id == body.message_id).first()
    if m is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if m.recipient_id != user.id and m.sender_id != user.id:
        raise HTTPException(status_code=403, detail="Not a party to this message")
    valid = pqc.sig_verify(SIG_ALG, b64decode(m.sender_dsa_public_key, "sender_dsa_public_key"),
                           body.plaintext.encode("utf-8"),
                           b64decode(m.signature, "signature"))
    record_op(db, user, "message_verify", SIG_ALG, success=valid)
    return {"id": m.id, "valid": valid}
