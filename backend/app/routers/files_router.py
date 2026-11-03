"""File security: upload (10 MB cap, allowlist), ML-KEM-wrapped encryption,
hashing, integrity verification, digital signatures.

Files are stored on disk encrypted only; the original plaintext is never
stored. Private keys are supplied per request, used in memory only.
"""
import os
import secrets

from cryptography.hazmat.primitives import hashes as crypto_hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import append_audit, record_op
from ..auth import get_current_user
from ..config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from ..crypto import classical, pqc
from ..database import get_db
from ..models import FileRecord, User
from ..util import b64decode, b64encode

router = APIRouter(prefix="/api/files", tags=["files"])

ALLOWED_EXT = {"pdf", "txt", "docx", "png", "zip"}
KEM_ALG = "ML-KEM-768"


class DecryptIn(BaseModel):
    kem_private_key: str


class SignFileIn(BaseModel):
    kem_private_key: str
    signing_private_key: str
    signing_public_key: str
    algorithm: str = "ML-DSA-65"


def _load_record(fid: int, user: User, db: Session) -> FileRecord:
    rec = db.query(FileRecord).filter(FileRecord.id == fid).first()
    if rec is None:
        raise HTTPException(status_code=404, detail="File not found")
    if rec.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can access this file")
    return rec


def _decrypt_bytes(rec: FileRecord, kem_private_key: str) -> bytes:
    ss = pqc.kem_decaps_secret(KEM_ALG, b64decode(kem_private_key, "kem_private_key"),
                               b64decode(rec.kem_ciphertext, "kem_ciphertext"))
    key = HKDF(algorithm=crypto_hashes.SHA256(), length=32, salt=None,
               info=b"quantumshield-x-file-v1").derive(ss)
    with open(os.path.join(UPLOAD_DIR, rec.stored_name), "rb") as f:
        encrypted = f.read()
    return classical.aes_decrypt(key, b64decode(rec.nonce, "nonce"), encrypted)


@router.post("/upload")
async def upload(file: UploadFile = File(...), kem_public_key: str = Form(...),
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"File type not allowed: .{ext}. Allowed: pdf, txt, docx, png, zip")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 10 MB limit")
    file_hashes = classical.hash_bytes(data)
    try:
        kem_ct, ss = pqc.kem_encaps_secret(KEM_ALG, b64decode(kem_public_key, "kem_public_key"))
    except Exception:
        raise HTTPException(status_code=400, detail="Encryption failed: check the ML-KEM public key")
    key = HKDF(algorithm=crypto_hashes.SHA256(), length=32, salt=None,
               info=b"quantumshield-x-file-v1").derive(ss)
    nonce, ct = classical.aes_encrypt(key, data)
    stored = secrets.token_hex(16) + ".enc"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(UPLOAD_DIR, stored), "wb") as f:
        f.write(ct)
    rec = FileRecord(owner_id=user.id, original_name=file.filename, stored_name=stored,
                     size_bytes=len(data), sha256=file_hashes["sha256"],
                     sha3_256=file_hashes["sha3_256"], kem_algorithm=KEM_ALG,
                     kem_ciphertext=b64encode(kem_ct), nonce=b64encode(nonce))
    db.add(rec)
    db.commit()
    record_op(db, user, "file_encrypt", KEM_ALG)
    append_audit(db, user.username, "file_uploaded_encrypted", f"name={file.filename} size={len(data)}")
    return {"id": rec.id, "original_name": rec.original_name, "size_bytes": rec.size_bytes,
            "sha256": rec.sha256, "sha3_256": rec.sha3_256, "status": "encrypted_and_stored"}


@router.get("/list")
def list_files(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(FileRecord).filter(FileRecord.owner_id == user.id).order_by(FileRecord.id.desc()).all()
    return [{"id": r.id, "original_name": r.original_name, "size_bytes": r.size_bytes,
             "sha256": r.sha256, "sha3_256": r.sha3_256, "signed": bool(r.signature),
             "created_at": str(r.created_at)} for r in rows]


@router.post("/{fid}/decrypt")
def decrypt(fid: int, body: DecryptIn, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    rec = _load_record(fid, user, db)
    try:
        pt = _decrypt_bytes(rec, body.kem_private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed: wrong private key or tampered file")
    record_op(db, user, "file_decrypt", KEM_ALG)
    tmp = os.path.join(UPLOAD_DIR, f"dl_{rec.id}_{secrets.token_hex(8)}")
    with open(tmp, "wb") as f:
        f.write(pt)

    def _cleanup(path: str):
        try:
            os.remove(path)
        except OSError:
            pass

    return FileResponse(tmp, filename=rec.original_name,
                        background=BackgroundTask(_cleanup, tmp))


@router.post("/{fid}/verify-integrity")
def verify_integrity(fid: int, body: DecryptIn, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    rec = _load_record(fid, user, db)
    try:
        pt = _decrypt_bytes(rec, body.kem_private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed: wrong private key or tampered file")
    h = classical.hash_bytes(pt)
    match = h["sha256"] == rec.sha256 and h["sha3_256"] == rec.sha3_256
    record_op(db, user, "file_verify_integrity", KEM_ALG, success=match)
    return {"id": rec.id, "match": match, "sha256": h["sha256"], "sha3_256": h["sha3_256"],
            "stored_sha256": rec.sha256, "stored_sha3_256": rec.sha3_256}


@router.post("/{fid}/sign")
def sign_file(fid: int, body: SignFileIn, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    rec = _load_record(fid, user, db)
    if body.algorithm not in pqc.SIG_ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {body.algorithm}")
    try:
        pt = _decrypt_bytes(rec, body.kem_private_key)
        sig = pqc.sig_sign(body.algorithm, b64decode(body.signing_private_key, "signing_private_key"), pt)
    except Exception:
        raise HTTPException(status_code=400, detail="Signing failed: check private keys")
    rec.signature = sig["signature"]
    rec.signature_algorithm = body.algorithm
    rec.signer_dsa_public_key = body.signing_public_key
    db.commit()
    record_op(db, user, "file_sign", body.algorithm)
    return {"id": rec.id, "signature": sig["signature"], "signature_bytes": sig["signature_bytes"]}


# Signature verification needs the file bytes, which are stored encrypted —
# so verification decrypts in memory with the owner's ML-KEM private key and
# checks the stored ML-DSA signature against the stored signer public key.
class VerifySigKeyIn(BaseModel):
    kem_private_key: str


@router.post("/{fid}/verify-signature-with-key")
def verify_file_signature_with_key(fid: int, body: VerifySigKeyIn,
                                   user: User = Depends(get_current_user),
                                   db: Session = Depends(get_db)):
    rec = _load_record(fid, user, db)
    if not rec.signature or not rec.signer_dsa_public_key:
        raise HTTPException(status_code=400, detail="This file has not been signed yet")
    try:
        pt = _decrypt_bytes(rec, body.kem_private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed: wrong private key or tampered file")
    alg = rec.signature_algorithm or "ML-DSA-65"
    valid = pqc.sig_verify(alg, b64decode(rec.signer_dsa_public_key, "signer_dsa_public_key"),
                           pt, b64decode(rec.signature, "signature"))
    record_op(db, user, "file_verify_signature", alg, success=valid)
    return {"id": rec.id, "valid": valid}
