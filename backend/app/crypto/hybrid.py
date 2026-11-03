"""Hybrid key establishment: X25519 + ML-KEM-768.

Construction (standard hybrid KEM combiner, not an invented one):
  1. Ephemeral X25519 exchange  -> shared secret ss_x
  2. ML-KEM-768 encapsulation  -> shared secret ss_kem
  3. Concatenate ss_x || ss_kem and run HKDF-SHA256 to derive the AES key.

Security assumption (documented in README and in API responses): the
derived key is secure if EITHER component holds — a classical break of
X25519 does not expose the key while ML-KEM holds, and a future break of
ML-KEM does not expose it while X25519 holds. This is the same combiner
pattern standardised for hybrid KEMs (e.g. the approach used in
draft-ietf-tls-hybrid-design / X-Wing-style combiners).
"""
import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from . import classical, pqc

INFO = b"quantumshield-x-hybrid-v1"
KEM_ALG = "ML-KEM-768"


def _derive(ss_x: bytes, ss_kem: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=INFO).derive(ss_x + ss_kem)


def hybrid_encrypt(recipient_x25519_public: bytes,
                   recipient_kem_public: bytes,
                   plaintext: bytes) -> dict:
    """One-shot hybrid encryption. Returns only public/transmittable values."""
    x_priv, x_pub = classical.x25519_keygen()
    ss_x = classical.x25519_shared(x_priv, recipient_x25519_public)
    kem_ct, ss_kem = pqc.kem_encaps_secret(KEM_ALG, recipient_kem_public)
    key = _derive(ss_x, ss_kem)
    nonce, ct = classical.aes_encrypt(key, plaintext)
    return {
        "x25519_public_key": base64.b64encode(x_pub).decode(),
        "kem_ciphertext": base64.b64encode(kem_ct).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ct).decode(),
    }


def hybrid_decrypt(x25519_private: bytes, kem_private: bytes,
                   x25519_public: bytes, kem_ciphertext: bytes,
                   nonce: bytes, ciphertext: bytes) -> bytes:
    """Recompute the hybrid key and AES-GCM decrypt. Raises on tampering."""
    ss_x = classical.x25519_shared(x25519_private, x25519_public)
    ss_kem = pqc.kem_decaps_secret(KEM_ALG, kem_private, kem_ciphertext)
    key = _derive(ss_x, ss_kem)
    return classical.aes_decrypt(key, nonce, ciphertext)


def hybrid_keygen() -> dict:
    """Generates a recipient hybrid keypair (X25519 + ML-KEM-768)."""
    x_priv, x_pub = classical.x25519_keygen()
    kem = pqc.kem_keygen(KEM_ALG)
    return {
        "x25519_private_key": base64.b64encode(x_priv).decode(),
        "x25519_public_key": base64.b64encode(x_pub).decode(),
        "kem_private_key": kem["private_key"],
        "kem_public_key": kem["public_key"],
    }
