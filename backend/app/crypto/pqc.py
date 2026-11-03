"""Post-quantum cryptography via liboqs-python (the official, maintained
wrapper around audited liboqs). Nothing here is hand-rolled: key generation,
encapsulation, and signatures all run inside liboqs.

Supported parameter sets (validated against the installed liboqs build).
Note: liboqs 0.16 names the FIPS 205 pure variants SLH_DSA_PURE_* — these
ARE the standardised SLH-DSA-SHA2/SHAKE parameter sets, just under liboqs's
naming. DISPLAY_NAMES maps them to the friendly FIPS names for the UI.
  ML-KEM:  ML-KEM-512, ML-KEM-768, ML-KEM-1024   (FIPS 203)
  ML-DSA:  ML-DSA-44, ML-DSA-65, ML-DSA-87       (FIPS 204)
  SLH-DSA: SLH_DSA_PURE_SHA2_128S (= SLH-DSA-SHA2-128s),
           SLH_DSA_PURE_SHA2_192S (= SLH-DSA-SHA2-192s),
           SLH_DSA_PURE_SHAKE_128S (= SLH-DSA-SHAKE-128s)  (FIPS 205)

Private keys and shared secrets are handled in memory only and are never
logged or stored by this module.
"""
import oqs

KEM_ALGORITHMS = ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"]
SIG_ALGORITHMS = [
    "ML-DSA-44", "ML-DSA-65", "ML-DSA-87",
    "SLH_DSA_PURE_SHA2_128S", "SLH_DSA_PURE_SHA2_192S", "SLH_DSA_PURE_SHAKE_128S",
]
DISPLAY_NAMES = {
    "ML-DSA-44": "ML-DSA-44 (FIPS 204)",
    "ML-DSA-65": "ML-DSA-65 (FIPS 204)",
    "ML-DSA-87": "ML-DSA-87 (FIPS 204)",
    "SLH_DSA_PURE_SHA2_128S": "SLH-DSA-SHA2-128s (FIPS 205)",
    "SLH_DSA_PURE_SHA2_192S": "SLH-DSA-SHA2-192s (FIPS 205)",
    "SLH_DSA_PURE_SHAKE_128S": "SLH-DSA-SHAKE-128s (FIPS 205)",
}


def enabled_kems() -> list[str]:
    try:
        enabled = set(oqs.get_enabled_kem_mechanisms())
    except Exception:
        enabled = set()
    return [a for a in KEM_ALGORITHMS if a in enabled] or KEM_ALGORITHMS


def enabled_sigs() -> list[str]:
    try:
        enabled = set(oqs.get_enabled_sig_mechanisms())
    except Exception:
        enabled = set()
    return [a for a in SIG_ALGORITHMS if a in enabled] or SIG_ALGORITHMS


def _check_kem(alg: str):
    if alg not in KEM_ALGORITHMS:
        raise ValueError(f"Unsupported KEM algorithm: {alg}")


def _check_sig(alg: str):
    if alg not in SIG_ALGORITHMS:
        raise ValueError(f"Unsupported signature algorithm: {alg}")


# ---------------- ML-KEM ----------------

def kem_keygen(alg: str) -> dict:
    """Returns base64 public/private keys plus their byte lengths."""
    import base64
    _check_kem(alg)
    with oqs.KeyEncapsulation(alg) as kem:
        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()
    return {
        "algorithm": alg,
        "public_key": base64.b64encode(public_key).decode(),
        "private_key": base64.b64encode(secret_key).decode(),
        "public_key_bytes": len(public_key),
        "private_key_bytes": len(secret_key),
    }


def kem_encaps(alg: str, public_key: bytes) -> dict:
    """Encapsulate against a public key. Returns ciphertext + lengths only.

    The shared secret itself is NEVER returned by this function; callers that
    need it (decrypt flows) use kem_decaps + the secret in memory only.
    """
    import base64
    _check_kem(alg)
    with oqs.KeyEncapsulation(alg) as kem:
        ciphertext, _shared_secret = kem.encap_secret(public_key)
    return {
        "algorithm": alg,
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "ciphertext_bytes": len(ciphertext),
    }


def kem_decaps_match(alg: str, secret_key: bytes, ciphertext: bytes,
                     expected_secret: bytes) -> bool:
    """Decapsulate and compare to an expected secret in constant time.

    Used by the lab verification flow: the caller supplies the secret it got
    from encaps (held client-side for the demo roundtrip); the server only
    reports match / no-match, never the secret.
    """
    import hmac
    _check_kem(alg)
    with oqs.KeyEncapsulation(alg, secret_key) as kem:
        shared_secret = kem.decap_secret(ciphertext)
    return hmac.compare_digest(shared_secret, expected_secret)


def kem_encaps_secret(alg: str, public_key: bytes) -> tuple[bytes, bytes]:
    """Internal helper: returns (ciphertext, shared_secret) in memory."""
    _check_kem(alg)
    with oqs.KeyEncapsulation(alg) as kem:
        return kem.encap_secret(public_key)


def kem_decaps_secret(alg: str, secret_key: bytes, ciphertext: bytes) -> bytes:
    """Internal helper: returns the shared secret in memory."""
    _check_kem(alg)
    with oqs.KeyEncapsulation(alg, secret_key) as kem:
        return kem.decap_secret(ciphertext)


# ---------------- ML-DSA / SLH-DSA ----------------

def sig_keygen(alg: str) -> dict:
    import base64
    _check_sig(alg)
    with oqs.Signature(alg) as sig:
        public_key = sig.generate_keypair()
        secret_key = sig.export_secret_key()
    return {
        "algorithm": alg,
        "public_key": base64.b64encode(public_key).decode(),
        "private_key": base64.b64encode(secret_key).decode(),
        "public_key_bytes": len(public_key),
        "private_key_bytes": len(secret_key),
    }


def sig_sign(alg: str, secret_key: bytes, message: bytes) -> dict:
    import base64
    _check_sig(alg)
    with oqs.Signature(alg, secret_key) as sig:
        signature = sig.sign(message)
    return {
        "algorithm": alg,
        "signature": base64.b64encode(signature).decode(),
        "signature_bytes": len(signature),
    }


def sig_verify(alg: str, public_key: bytes, message: bytes, signature: bytes) -> bool:
    _check_sig(alg)
    try:
        with oqs.Signature(alg) as sig:
            return bool(sig.verify(message, signature, public_key))
    except Exception:
        return False
