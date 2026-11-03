"""QUANTUMSHIELD X — FastAPI backend.

Security notes:
- Private keys and shared secrets are never stored, never logged, and (for
  shared secrets) never returned in any response.
- Error responses are generic: no stack traces, no secret material.
- This platform demonstrates standardised post-quantum cryptography. It is
  NOT claimed to be quantum-proof or independently security-certified.
"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import hash_password
from .config import FRONTEND_ORIGIN, UPLOAD_DIR
from .database import Base, SessionLocal, engine
from .models import User
from .ratelimit import RateLimitMiddleware
from .routers import (admin, auth_router, files_router, insights, kem_sign,
                      keys_router, messaging, symmetric_hybrid)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("quantumshield")

app = FastAPI(title="QUANTUMSHIELD X API",
              description="Post-quantum cryptography platform (FIPS 203/204/205 + classical).",
              version="1.0.0")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s", request.url.path)  # never log exc details with secrets
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def startup():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Demo-only seed accounts, clearly documented in README/RUN_STEPS.
        for username, password, role in [("user", "demo123", "user"),
                                         ("admin", "admin123", "admin")]:
            if not db.query(User).filter(User.username == username).first():
                db.add(User(username=username, password_hash=hash_password(password),
                            role=role))
        db.commit()
        logger.info("Startup complete. Demo accounts seeded (user/demo123, admin/admin123).")
    finally:
        db.close()


@app.get("/")
def root():
    return {"name": "QUANTUMSHIELD X", "status": "running",
            "docs": "/docs",
            "note": "Demonstration platform for standardised post-quantum cryptography. "
                    "Not claimed to be quantum-proof or security-certified."}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router.router)
app.include_router(keys_router.router)
app.include_router(kem_sign.router)
app.include_router(symmetric_hybrid.router)
app.include_router(messaging.router)
app.include_router(files_router.router)
app.include_router(insights.router)
app.include_router(admin.router)
