"""Database models.

Security rule enforced by design: NO model stores a private key, a shared
secret, or plaintext message/file content. Messages and files are stored as
ciphertext only. Public keys are public and may be stored.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(16), default="user", nullable=False)  # user | admin
    kem_public_key = Column(Text, nullable=True)  # base64, public only
    dsa_public_key = Column(Text, nullable=True)  # base64, public only
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class CryptoOperation(Base):
    """One row per cryptographic operation, used for the dashboard.

    Only metadata is stored: never ciphertext payloads, keys, or secrets.
    """
    __tablename__ = "crypto_operations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(64), nullable=True)
    operation = Column(String(64), nullable=False)  # keygen, kem, sign, verify, ...
    algorithm = Column(String(64), nullable=False)
    success = Column(Integer, default=1, nullable=False)  # 1 ok, 0 failed
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Message(Base):
    """User-to-user message, ciphertext only."""
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kem_algorithm = Column(String(64), default="ML-KEM-768", nullable=False)
    kem_ciphertext = Column(Text, nullable=False)  # base64
    nonce = Column(Text, nullable=False)  # base64
    ciphertext = Column(Text, nullable=False)  # base64 AES-256-GCM output
    signature = Column(Text, nullable=False)  # base64 ML-DSA signature
    sender_dsa_public_key = Column(Text, nullable=False)  # base64
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class FileRecord(Base):
    """Encrypted file metadata. File bytes live on disk, encrypted."""
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_name = Column(String(256), nullable=False)
    stored_name = Column(String(128), nullable=False)  # random id, on disk
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    sha3_256 = Column(String(64), nullable=False)
    kem_algorithm = Column(String(64), default="ML-KEM-768", nullable=False)
    kem_ciphertext = Column(Text, nullable=False)  # base64
    nonce = Column(Text, nullable=False)  # base64
    signature = Column(Text, nullable=True)  # base64 ML-DSA signature, if signed
    signature_algorithm = Column(String(64), nullable=True)
    signer_dsa_public_key = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class AuditEntry(Base):
    """Hash-chained audit log. Each entry hashes the previous entry's hash,
    so tampering with any row breaks the chain (see /api/audit/verify-chain)."""
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(64), nullable=False)
    action = Column(String(128), nullable=False)
    details = Column(String(512), nullable=True)  # metadata only, never secrets
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
