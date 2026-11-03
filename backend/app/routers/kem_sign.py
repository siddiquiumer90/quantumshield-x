"""KEM encapsulation / decapsulation-verification and digital signatures.

KEM privacy rule: the shared secret itself is NEVER returned. Encapsulation
returns the ciphertext plus a SHA-256 commitment of the secret; the
decapsulation check recomputes that commitment and returns only match/no-match.
"""
import hashlib

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import record_op
from ..auth import get_current_user
from ..crypto import classical, pqc
from ..database import get_db
from ..models import User
from ..util import b64decode, b64encode

router = APIRouter(tags=["kem", "signatures"])


class EncapsIn(BaseModel):
    algorithm: str
    public_key: str  # base64


class DecapsVerifyIn(BaseModel):
    algorithm: str
    private_key: str  # base64
    ciphertext: str  # base64
    expected_secret_sha256: str  # hex commitment from the encaps response


class SignIn(BaseModel):
    algorithm: str
    private_key: str  # base64 for PQC, PEM for RSA/ECDSA
    message: str


class VerifyIn(BaseModel):
    algorithm: str
    public_key: str  # base64 for PQC, PEM for RSA/ECDSA
    message: str
    signature: str  # base64


@router.post("/api/kem/encaps")
def kem_encaps(body: EncapsIn, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    try:
        pk = b64decode(body.public_key, "public_key")
        ct, secret = pqc.kem_encaps_secret(body.algorithm, pk)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Encapsulation failed: check algorithm and public key")
    record_op(db, user, "kem_encaps", body.algorithm)
    return {
        "algorithm": body.algorithm,
        "ciphertext": b64encode(ct),
        "ciphertext_bytes": len(ct),
        "secret_sha256": hashlib.sha256(secret).hexdigest(),
        "secret_bytes": len(secret),
        "note": "The shared secret itself is never returned; only its SHA-256 commitment.",
    }


@router.post("/api/kem/decaps-verify")
def kem_decaps_verify(body: DecapsVerifyIn, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    try:
        sk = b64decode(body.private_key, "private_key")
        ct = b64decode(body.ciphertext, "ciphertext")
        secret = pqc.kem_decaps_secret(body.algorithm, sk, ct)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Decapsulation failed: check algorithm, private key and ciphertext")
    match = hashlib.sha256(secret).hexdigest() == body.expected_secret_sha256.lower()
    record_op(db, user, "kem_decaps_verify", body.algorithm, success=match)
    return {"algorithm": body.algorithm, "match": match}


@router.post("/api/sign")
def sign(body: SignIn, user: User = Depends(get_current_user),
         db: Session = Depends(get_db)):
    msg = body.message.encode("utf-8")
    alg = body.algorithm
    try:
        if alg in pqc.SIG_ALGORITHMS:
            sk = b64decode(body.private_key, "private_key")
            result = pqc.sig_sign(alg, sk, msg)
            sig_b64 = result["signature"]
            sig_bytes = result["signature_bytes"]
        elif alg == "RSA-PSS":
            sig = classical.rsa_sign(body.private_key, msg)
            sig_b64, sig_bytes = b64encode(sig), len(sig)
        elif alg == "ECDSA-P-256":
            sig = classical.ecc_sign(body.private_key, msg)
            sig_b64, sig_bytes = b64encode(sig), len(sig)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {alg}")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Signing failed: check algorithm and private key")
    record_op(db, user, "sign", alg)
    return {"algorithm": alg, "signature": sig_b64, "signature_bytes": sig_bytes}


@router.post("/api/verify")
def verify(body: VerifyIn, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    msg = body.message.encode("utf-8")
    alg = body.algorithm
    try:
        if alg in pqc.SIG_ALGORITHMS:
            pk = b64decode(body.public_key, "public_key")
            sig = b64decode(body.signature, "signature")
            valid = pqc.sig_verify(alg, pk, msg, sig)
        elif alg == "RSA-PSS":
            sig = b64decode(body.signature, "signature")
            valid = classical.rsa_verify(body.public_key, msg, sig)
        elif alg == "ECDSA-P-256":
            sig = b64decode(body.signature, "signature")
            valid = classical.ecc_verify(body.public_key, msg, sig)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {alg}")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Verification failed: check inputs")
    record_op(db, user, "verify", alg, success=valid)
    return {"algorithm": alg, "valid": valid}
