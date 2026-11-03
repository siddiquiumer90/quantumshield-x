"""Key generation. The private key appears ONLY in this response (one-time
download). It is never stored server-side, never logged, and never returned
by any other endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import append_audit, record_op
from ..auth import get_current_user
from ..crypto import classical, pqc
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/keys", tags=["keys"])

WARNING = ("WARNING: This private key is shown only once. Download it now and "
           "store it safely. The server does NOT store it and cannot recover it.")

KEM_SET = set(pqc.KEM_ALGORITHMS)
SIG_SET = set(pqc.SIG_ALGORITHMS)


class GenerateIn(BaseModel):
    algorithm: str


@router.get("/algorithms")
def algorithms():
    return {
        "kem": pqc.enabled_kems(),
        "signatures": pqc.enabled_sigs(),
        "classical": ["RSA-2048", "ECC-P-256"],
    }


@router.post("/generate")
def generate(body: GenerateIn, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    alg = body.algorithm
    if alg in KEM_SET:
        result = pqc.kem_keygen(alg)
    elif alg in SIG_SET:
        result = pqc.sig_keygen(alg)
    elif alg == "RSA-2048":
        result = classical.rsa_keygen(2048)
    elif alg == "ECC-P-256":
        result = classical.ecc_keygen()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {alg}")
    record_op(db, user, "keygen", alg)
    append_audit(db, user.username, "key_generated", f"algorithm={alg}")
    return {**result, "warning": WARNING, "stored_server_side": False}
