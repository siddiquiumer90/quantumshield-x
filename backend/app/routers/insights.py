"""Dashboard (real DB counts only), audit log, live benchmarks, migration
readiness, Harvest-Now-Decrypt-Later estimator, and the quantum simulator.

Honesty rules enforced here:
- Dashboard numbers come only from the database; an empty DB reports zeros.
- Benchmark numbers are measured live at request time (cached 120 s).
- Simulator and HNDL outputs are explicitly labelled educational models.
"""
import base64
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..audit import verify_chain
from ..auth import get_current_user
from ..crypto import classical, pqc
from ..database import get_db
from ..models import AuditEntry, CryptoOperation, FileRecord, Message, User

router = APIRouter(tags=["insights"])

EDU_LABEL = "Educational model only — not an actual quantum attack or prediction."


@router.get("/api/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_ops = db.query(func.count(CryptoOperation.id)).scalar()
    total_signs = db.query(func.count(CryptoOperation.id)).filter(
        CryptoOperation.operation == "sign").scalar()
    ver_rows = db.query(CryptoOperation).filter(CryptoOperation.operation == "verify").all()
    total_ver = len(ver_rows)
    ok_ver = sum(1 for r in ver_rows if r.success == 1)
    usage_rows = db.query(CryptoOperation.algorithm, func.count(CryptoOperation.id)).group_by(
        CryptoOperation.algorithm).all()
    recent = db.query(CryptoOperation).order_by(CryptoOperation.id.desc()).limit(10).all()
    active = sorted({r.algorithm for r in db.query(CryptoOperation.algorithm).all()})
    return {
        "total_operations": total_ops,
        "total_signatures": total_signs,
        "total_verifications": total_ver,
        "successful_verifications": ok_ver,
        "algorithm_usage": [{"algorithm": a, "count": c} for a, c in usage_rows],
        "recent_events": [{"id": r.id, "operation": r.operation, "algorithm": r.algorithm,
                           "username": r.username, "success": bool(r.success),
                           "created_at": str(r.created_at)} for r in recent],
        "active_algorithms": active,
        "total_messages": db.query(func.count(Message.id)).scalar(),
        "total_files": db.query(func.count(FileRecord.id)).scalar(),
        "total_users": db.query(func.count(User.id)).scalar(),
    }


@router.get("/api/audit/list")
def audit_list(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(AuditEntry).order_by(AuditEntry.id.desc()).limit(50).all()
    return [{"id": r.id, "actor": r.actor, "action": r.action, "details": r.details,
             "prev_hash": r.prev_hash, "entry_hash": r.entry_hash,
             "created_at": str(r.created_at)} for r in rows]


@router.get("/api/audit/verify-chain")
def audit_verify(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return verify_chain(db)


# ---------------- Live benchmarks ----------------
_bench_cache: dict = {"at": 0.0, "data": None}


def _time(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return (time.perf_counter() - t0) * 1000.0, out


@router.get("/api/benchmark")
def benchmark(user: User = Depends(get_current_user)):
    now = time.time()
    if _bench_cache["data"] is not None and now - _bench_cache["at"] < 120:
        return {**_bench_cache["data"], "cached": True}
    results = []

    def kem_row(alg):
        t_key, keys = _time(pqc.kem_keygen, alg)
        t_enc, enc = _time(pqc.kem_encaps_secret, alg,
                           base64.b64decode(keys["public_key"]))
        results.append({
            "algorithm": alg, "family": "ML-KEM (FIPS 203)",
            "keygen_ms": round(t_key, 2), "encaps_ms": round(t_enc, 2),
            "public_key_bytes": keys["public_key_bytes"],
            "private_key_bytes": keys["private_key_bytes"],
            "ciphertext_bytes": len(enc[0]), "signature_bytes": None})

    for alg in ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"]:
        kem_row(alg)

    def sig_row(alg):
        t_key, keys = _time(pqc.sig_keygen, alg)
        t_sign, sig = _time(pqc.sig_sign, alg,
                            base64.b64decode(keys["private_key"]), b"benchmark")
        results.append({
            "algorithm": alg,
            "family": "ML-DSA (FIPS 204)" if alg.startswith("ML-DSA") else "SLH-DSA (FIPS 205)",
            "keygen_ms": round(t_key, 2), "encaps_ms": round(t_sign, 2),
            "public_key_bytes": keys["public_key_bytes"],
            "private_key_bytes": keys["private_key_bytes"],
            "ciphertext_bytes": None, "signature_bytes": sig["signature_bytes"]})

    for alg in ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87", "SLH_DSA_PURE_SHA2_128S"]:
        sig_row(alg)

    t_key, rsa = _time(classical.rsa_keygen, 2048)
    t_sign, _ = _time(classical.rsa_sign, rsa["private_key"], b"benchmark")
    results.append({"algorithm": "RSA-2048", "family": "Classical (RSA)",
                    "keygen_ms": round(t_key, 2), "encaps_ms": round(t_sign, 2),
                    "public_key_bytes": rsa["public_key_bytes"],
                    "private_key_bytes": rsa["private_key_bytes"],
                    "ciphertext_bytes": 256, "signature_bytes": 256})
    t_key, ecc = _time(classical.ecc_keygen)
    t_sign, esig = _time(classical.ecc_sign, ecc["private_key"], b"benchmark")
    results.append({"algorithm": "ECC-P-256", "family": "Classical (ECC)",
                    "keygen_ms": round(t_key, 2), "encaps_ms": round(t_sign, 2),
                    "public_key_bytes": ecc["public_key_bytes"],
                    "private_key_bytes": ecc["private_key_bytes"],
                    "ciphertext_bytes": None, "signature_bytes": len(esig)})
    t_enc, _ = _time(classical.aes_encrypt, classical.aes_keygen(), b"benchmark")
    results.append({"algorithm": "AES-256-GCM", "family": "Symmetric",
                    "keygen_ms": 0.0, "encaps_ms": round(t_enc, 3),
                    "public_key_bytes": None, "private_key_bytes": 32,
                    "ciphertext_bytes": None, "signature_bytes": None})
    data = {"measured_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "note": "Measured live on this server at request time (not hardcoded).",
            "results": results}
    _bench_cache.update({"at": now, "data": data})
    return {**data, "cached": False}


# ---------------- Migration readiness ----------------
class SystemIn(BaseModel):
    name: str
    algorithm: str
    data_secrecy_years: int = Field(..., ge=0, le=100)


class MigrationIn(BaseModel):
    systems: list[SystemIn]


VULNERABLE = {"RSA-1024", "RSA-2048", "RSA-4096", "ECC-P-256", "ECC-P-384",
              "ECDH", "X25519", "DSA", "DH"}
QUANTUM_SAFE = {"ML-KEM-512", "ML-KEM-768", "ML-KEM-1024", "ML-DSA-44",
                "ML-DSA-65", "ML-DSA-87", "SLH_DSA_PURE_SHA2_128S",
                "SLH_DSA_PURE_SHA2_192S", "SLH_DSA_PURE_SHAKE_128S",
                "Hybrid-X25519-ML-KEM-768"}
SYMMETRIC_OK = {"AES-256-GCM", "AES-128-GCM", "SHA-256", "SHA-3", "SHA3-256"}


@router.post("/api/migration")
def migration(body: MigrationIn, user: User = Depends(get_current_user)):
    if not body.systems:
        return {"score": None, "recommendations": ["Add at least one system to assess."]}
    score = 100
    recs: list[str] = []
    for s in body.systems:
        alg = s.algorithm
        if alg in VULNERABLE:
            penalty = 30 if s.data_secrecy_years >= 10 else 20
            score -= penalty
            recs.append(f"{s.name}: {alg} is vulnerable to Shor's algorithm — migrate to "
                        f"ML-KEM/ML-DSA. Data must stay secret {s.data_secrecy_years} years, "
                        f"so this is {'high' if s.data_secrecy_years >= 10 else 'medium'} priority.")
        elif alg in QUANTUM_SAFE:
            recs.append(f"{s.name}: {alg} is a standardised post-quantum algorithm — keep it.")
        elif alg in SYMMETRIC_OK:
            recs.append(f"{s.name}: {alg} is symmetric/hashing — Grover's algorithm only "
                        f"halves effective strength; AES-256 remains acceptable.")
        else:
            score -= 10
            recs.append(f"{s.name}: unknown algorithm {alg} — verify it against FIPS 203/204/205.")
    score = max(0, min(100, score))
    if score >= 80:
        recs.append("Overall: strong posture. Keep a crypto-agility plan so algorithms can be swapped.")
    elif score >= 50:
        recs.append("Overall: partial readiness. Prioritise migrating long-secrecy RSA/ECC systems first.")
    else:
        recs.append("Overall: low readiness. Start migration now for anything with secrecy over 10 years.")
    return {"score": score, "recommendations": recs}


# ---------------- Harvest Now, Decrypt Later ----------------
class HndlIn(BaseModel):
    algorithm: str
    secrecy_years: int = Field(..., ge=0, le=100)
    migration_years: int = Field(5, ge=0, le=50)
    threat_years_estimate: int = Field(10, ge=1, le=50)


@router.post("/api/hndl")
def hndl(body: HndlIn, user: User = Depends(get_current_user)):
    x, y, z = body.secrecy_years, body.migration_years, body.threat_years_estimate
    at_risk = (x + y) > z
    vulnerable = body.algorithm in VULNERABLE
    if not vulnerable:
        level = "low"
        verdict = (f"{body.algorithm} is not broken by Shor's algorithm, so harvested "
                   f"ciphertexts are not exposed by a future quantum computer on current knowledge.")
    elif at_risk:
        level = "high"
        verdict = (f"X+Y > Z: data secret for {x} years + migration taking {y} years exceeds "
                   f"the assumed {z}-year quantum timeline — ciphertexts harvested today could "
                   f"be decrypted within their secrecy lifetime.")
    else:
        level = "medium"
        verdict = (f"X+Y <= Z on your assumptions ({x}+{y} <= {z}), but the margin is an "
                   f"assumption, not a guarantee — migrate long-secrecy {body.algorithm} data anyway.")
    return {"model": "Mosca X+Y>Z", "label": EDU_LABEL,
            "x_secrecy_years": x, "y_migration_years": y, "z_threat_years_estimate": z,
            "x_plus_y": x + y, "at_risk": at_risk and vulnerable,
            "exposure_level": level, "verdict": verdict,
            "note": "Z is YOUR assumption about when a cryptographically relevant quantum "
                    "computer arrives — nobody knows this value. Change it to test sensitivity."}


# ---------------- Quantum simulator (educational model) ----------------
@router.get("/api/simulator")
def simulator(user: User = Depends(get_current_user)):
    return {
        "label": EDU_LABEL,
        "comparison": [
            {"algorithm": "RSA-2048", "classical_security_bits": 112,
             "quantum_vulnerable": True, "attack": "Shor's algorithm (polynomial time)",
             "pqc_replacement": "ML-KEM-768 / ML-DSA-65"},
            {"algorithm": "ECC P-256", "classical_security_bits": 128,
             "quantum_vulnerable": True, "attack": "Shor's algorithm (polynomial time)",
             "pqc_replacement": "ML-KEM-768 / ML-DSA-65"},
            {"algorithm": "AES-256", "classical_security_bits": 256,
             "quantum_vulnerable": False, "attack": "Grover's algorithm (quadratic speedup only)",
             "pqc_replacement": "AES-256 stays acceptable (effective ~128-bit vs Grover)"},
            {"algorithm": "SHA-256", "classical_security_bits": 256,
             "quantum_vulnerable": False, "attack": "Grover's algorithm (quadratic speedup only)",
             "pqc_replacement": "SHA-256 / SHA-3 remain acceptable"},
            {"algorithm": "ML-KEM-768", "classical_security_bits": 192,
             "quantum_vulnerable": False, "attack": "No known quantum attack",
             "pqc_replacement": "This IS the replacement (FIPS 203)"},
            {"algorithm": "ML-DSA-65", "classical_security_bits": 192,
             "quantum_vulnerable": False, "attack": "No known quantum attack",
             "pqc_replacement": "This IS the replacement (FIPS 204)"},
        ],
        "shor": {
            "title": "Shor's algorithm (educational explanation)",
            "idea": "Shor's algorithm turns integer factoring and discrete logarithms into a "
                    "period-finding problem, which a quantum computer solves with the quantum "
                    "Fourier transform in polynomial time — O(n^3) for an n-bit number, versus "
                    "sub-exponential time for the best classical factoring (number field sieve).",
            "why_rsa_breaks": "RSA security rests on factoring being hard. Shor factors in polynomial "
                             "time, so RSA-2048's ~112-bit classical security collapses.",
            "why_ecc_breaks": "Elliptic-curve discrete logarithms are also period-finding problems, so "
                             "ECC falls the same way.",
            "label": EDU_LABEL,
        },
        "grover": {
            "title": "Grover's algorithm (educational explanation)",
            "idea": "Grover's algorithm searches an unsorted space of N items in about sqrt(N) "
                    "steps — a quadratic speedup, not exponential. For symmetric crypto this "
                    "halves effective key strength: AES-256 behaves like ~128-bit, AES-128 like "
                    "~64-bit. Doubling symmetric key sizes restores the margin.",
            "label": EDU_LABEL,
        },
        "hndl_note": "Harvest Now, Decrypt Later: an attacker can record encrypted traffic today "
                      "and decrypt it later once a capable quantum computer exists — which is "
                      "why long-secrecy data needs post-quantum protection before that day.",
    }
