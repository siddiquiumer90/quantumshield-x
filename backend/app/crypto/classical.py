"""Classical cryptography via the maintained `cryptography` package
(OpenSSL-backed). Nothing here is hand-rolled.

Covers: RSA-2048 (OAEP + PSS), ECC P-256 (ECDSA), X25519, AES-256-GCM,
SHA-256, SHA-3 (SHA3-256).
"""
import base64
import hashlib
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def _pem_private(key) -> str:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()).decode()


def _pem_public(key) -> str:
    return key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).decode()


# ---------------- RSA ----------------

def rsa_keygen(key_size: int = 2048) -> dict:
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    pub = key.public_key()
    return {
        "algorithm": f"RSA-{key_size}",
        "public_key": _pem_public(pub),
        "private_key": _pem_private(key),
        "public_key_bytes": len(_pem_public(pub).encode()),
        "private_key_bytes": len(_pem_private(key).encode()),
    }


def _load_rsa_private(pem: str):
    return serialization.load_pem_private_key(pem.encode(), password=None)


def _load_rsa_public(pem: str):
    return serialization.load_pem_public_key(pem.encode())


def rsa_sign(private_pem: str, message: bytes) -> bytes:
    key = _load_rsa_private(private_pem)
    return key.sign(message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                         salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256())


def rsa_verify(public_pem: str, message: bytes, signature: bytes) -> bool:
    key = _load_rsa_public(public_pem)
    try:
        key.verify(signature, message,
                   padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                               salt_length=padding.PSS.MAX_LENGTH),
                   hashes.SHA256())
        return True
    except InvalidSignature:
        return False


# ---------------- ECC P-256 / ECDSA ----------------

def ecc_keygen() -> dict:
    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key()
    return {
        "algorithm": "ECC-P-256",
        "public_key": _pem_public(pub),
        "private_key": _pem_private(key),
        "public_key_bytes": len(_pem_public(pub).encode()),
        "private_key_bytes": len(_pem_private(key).encode()),
    }


def ecc_sign(private_pem: str, message: bytes) -> bytes:
    key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    return key.sign(message, ec.ECDSA(hashes.SHA256()))


def ecc_verify(public_pem: str, message: bytes, signature: bytes) -> bool:
    key = serialization.load_pem_public_key(public_pem.encode())
    try:
        key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


# ---------------- AES-256-GCM ----------------

def aes_encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """Returns (nonce, ciphertext_with_tag)."""
    nonce = os.urandom(12)
    return nonce, AESGCM(key).encrypt(nonce, plaintext, None)


def aes_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Raises InvalidTag on tampered ciphertext (authentication failure)."""
    return AESGCM(key).decrypt(nonce, ciphertext, None)


def aes_keygen() -> bytes:
    return os.urandom(32)


# ---------------- Hashes ----------------

def hash_bytes(data: bytes) -> dict:
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "sha3_256": hashlib.sha3_256(data).hexdigest(),
        "size_bytes": len(data),
    }


# ---------------- X25519 ----------------

def x25519_keygen() -> tuple[bytes, bytes]:
    """Returns (private_bytes, public_bytes), raw 32-byte form."""
    priv = x25519.X25519PrivateKey.generate()
    return (priv.private_bytes(serialization.Encoding.Raw,
                               serialization.PrivateFormat.Raw,
                               serialization.NoEncryption()),
            priv.public_key().public_bytes(serialization.Encoding.Raw,
                                           serialization.PublicFormat.Raw))


def x25519_shared(private_bytes: bytes, public_bytes: bytes) -> bytes:
    priv = x25519.X25519PrivateKey.from_private_bytes(private_bytes)
    pub = x25519.X25519PublicKey.from_public_bytes(public_bytes)
    return priv.exchange(pub)
