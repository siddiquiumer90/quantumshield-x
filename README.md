# QUANTUMSHIELD X

**Next-Generation Post-Quantum Cryptography & Cybersecurity Platform**

A complete, working platform demonstrating how digital communication and sensitive
data can be protected against future quantum-computing threats — using real,
standardised post-quantum cryptography: **ML-KEM (FIPS 203)**, **ML-DSA (FIPS 204)**
and **SLH-DSA (FIPS 205)**, plus classical RSA, ECC, X25519 and AES-256-GCM.

> **Honest scope.** This is a demonstration and research platform. It is **not**
> claimed to be quantum-proof and **not** independently security-certified.
> Simulator and Harvest-Now-Decrypt-Later outputs are **educational models**, not
> actual quantum attacks or predictions.

## What it does

| Area | Real functionality |
|---|---|
| Cryptography Lab | ML-KEM-512/768/1024 keygen + encaps/decaps roundtrip (secret never returned — verified by SHA-256 commitment), AES-256-GCM encrypt/decrypt, X25519 + ML-KEM-768 hybrid mode |
| Digital signatures | ML-DSA-44/65/87, SLH-DSA variants, RSA-PSS, ECDSA — sign, verify, tamper tests |
| Secure messaging | User-to-user messages: ML-KEM-768 establishment + AES-256-GCM + ML-DSA-65 signatures; stored as ciphertext only |
| File security | Upload (10 MB cap, pdf/txt/docx/png/zip), ML-KEM-wrapped encryption, SHA-256 + SHA3-256 hashing, integrity verification, file signing |
| Dashboard | Counts read only from the database — zero hardcoded statistics |
| Audit log | Hash-chained entries with a chain-verification endpoint |
| Benchmarks | Timings and key/ciphertext/signature sizes measured live at request time |
| Migration readiness | Score + recommendations computed from your own algorithm inventory |
| HNDL estimator | Mosca X+Y>Z exposure assessment (educational model) |
| Quantum simulator | Classical-vs-quantum comparison, Shor/Grover explainers (labelled educational) |
| Admin | User list, system stats, audit — admin role only (non-admin gets 403) |

## Tech stack

- **Frontend:** React 18 + TypeScript + Vite, Tailwind CSS v4, Framer Motion, Lucide icons, Recharts, React Router
- **Backend:** Python + FastAPI, Pydantic validation, SQLAlchemy
- **Crypto:** `liboqs-python` (official wrapper around audited liboqs) for all PQC;
  `cryptography` (OpenSSL-backed) for RSA, ECC, X25519, AES-256-GCM, SHA-256, SHA-3.
  Nothing cryptographic is hand-rolled.
- **Database:** SQLite by default (zero-setup). Set `DATABASE_URL` for PostgreSQL in production.
- **Rate limiting:** per-IP sliding window; Redis if `REDIS_URL` is set and `redis` is
  installed, otherwise in-memory fallback.

## Quick start (Linux / this machine)

```bash
cd quantumshield-x/backend
pip install --user --break-system-packages -r requirements.txt
# First run builds liboqs once (needs git + cmake + a C compiler) — a few minutes.
python -m uvicorn app.main:app --port 8000

cd quantumshield-x/frontend
npm install
npm run dev        # http://localhost:5173
```

> **Windows laptop?** Follow `RUN_STEPS.md` instead — it gives literal one-command-at-a-time
> steps for a D: drive install, including the one-time liboqs build prerequisites.

**Demo logins (demo-only — change them in production):**

| User | Password | Role |
|---|---|---|
| `user` | `demo123` | user |
| `admin` | `admin123` | admin |

## API summary

Interactive docs at `http://localhost:8000/docs` when the backend runs.
Full endpoint table: frontend **Documentation** page, or `docs/ARCHITECTURE.md`.

Key endpoints: `POST /api/auth/register`, `POST /api/auth/login`,
`POST /api/keys/generate`, `POST /api/kem/encaps`, `POST /api/kem/decaps-verify`,
`POST /api/sign`, `POST /api/verify`, `POST /api/symmetric/encrypt|decrypt`,
`POST /api/hybrid/encrypt|decrypt`, `POST /api/messages/send`,
`POST /api/files/upload`, `GET /api/dashboard`, `GET /api/audit/verify-chain`,
`GET /api/benchmark`, `POST /api/migration`, `POST /api/hndl`,
`GET /api/simulator`, `GET /api/admin/*`.

## Security rules enforced by the code

- **Private keys are never stored server-side** and never logged. A private key appears
  only in the direct generation response (one-time download) — lose it and it is gone.
- **Shared secrets are never returned** by any endpoint. KEM roundtrips are verified
  with a SHA-256 commitment of the secret, never the secret itself.
- Messages and files are stored as **ciphertext only**; originals are never stored.
- Passwords are bcrypt-hashed; auth uses JWT bearer tokens; admin routes require
  the admin role.
- Uploads: 10 MB cap + extension allowlist. Inputs validated with Pydantic.
- Error responses are generic — no stack traces or secret material.
- Structured logging never logs keys, secrets, or plaintext.

## Hybrid mode — security assumption

Hybrid encryption combines X25519 and ML-KEM-768: both shared secrets are
concatenated and passed through HKDF-SHA256 to derive the AES-256-GCM key.
This is the standard hybrid KEM combiner construction, not an invented one.
Assumption, stated in the API response and UI: **the derived key is secure if
either component holds**.

## Tests

```bash
cd quantumshield-x/backend
python -m pytest tests/ -v
```

Covers: key generation, KEM roundtrip, sign/verify + tamper failure, AES-GCM
roundtrip + tamper failure, hybrid roundtrip, file hash integrity, messaging flow,
auth success/failure, admin RBAC 403, invalid-input handling, audit chain, simulator
labelling, migration + HNDL.

## Production notes (optional path)

- `docker-compose.yml` is the optional production path (PostgreSQL + backend + frontend).
  Docker is **not** required for the laptop demo — SQLite + `npm run dev` is enough.
- Before any production use: set a strong `QS_SECRET_KEY`, serve over HTTPS, replace
  the demo accounts, and use PostgreSQL. See `.env.example`.

## Project layout

```
quantumshield-x/
  README.md  RUN_STEPS.md  .env.example  docker-compose.yml
  backend/
    requirements.txt
    app/
      main.py  config.py  database.py  models.py  auth.py  audit.py  ratelimit.py  util.py
      crypto/  pqc.py  classical.py  hybrid.py
      routers/ auth_router.py  keys_router.py  kem_sign.py  symmetric_hybrid.py
               messaging.py  files_router.py  insights.py  admin.py
    tests/  conftest.py  test_api.py
  frontend/
    src/  App.tsx  api.ts  main.tsx  index.css
    src/components/Layout.tsx
    src/pages/  Landing, Auth, Dashboard, CryptoLab, Messaging, FileSecurity,
                SignatureLab, Simulator, Compare, KeyManagement, AuditLogs,
                LearningCenter, Documentation, Profile, Admin
  docs/ARCHITECTURE.md
```

## Limitations (stated honestly)

- Simulator and HNDL outputs are educational models, not predictions of when a
  quantum computer will arrive or what it will break.
- The demo stores private keys nowhere — that is deliberate, but it means key
  recovery is impossible; users must keep their one-time downloads.
- Messaging requires both parties to have published public keys first.
- No independent security audit or certification has been performed.
