"""Configuration for QUANTUMSHIELD X.

All secrets come from environment variables. Defaults are demo-only values
and must be overridden in production (see .env.example).
"""
import os

# Absolute defaults derived from this file's location, so the backend works
# no matter which directory you start it from (repo root or backend/).
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get("QS_SECRET_KEY", "dev-only-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("QS_TOKEN_HOURS", "24"))
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{_BACKEND_DIR}/data/quantumshield.db"
)
REDIS_URL = os.environ.get("REDIS_URL", "")
_raw_frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
# Render's fromService gives a bare hostname (no scheme); CORS needs a full
# origin, so add https:// when no scheme is present.
FRONTEND_ORIGIN = (_raw_frontend_origin if "://" in _raw_frontend_origin
                   else "https://" + _raw_frontend_origin)
MAX_UPLOAD_BYTES = int(os.environ.get("QS_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("QS_RATE_LIMIT_PER_MINUTE", "120"))
UPLOAD_DIR = os.environ.get("QS_UPLOAD_DIR", os.path.join(_BACKEND_DIR, "data", "files"))
