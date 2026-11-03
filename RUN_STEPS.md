# RUN_STEPS — QUANTUMSHIELD X on your Windows laptop

Read this top to bottom. **One command at a time.** Wait for each command to
finish before typing the next one. Everything goes on **D:** because C: is
nearly full — do not install anything on C:.

## Step 0 — What you need first (install once)

1. **Python 3.12** from python.org. During install, tick
   **"Add python.exe to PATH"**.
2. **Node.js 20 or newer (LTS)** from nodejs.org (this also installs npm).
3. **Git for Windows** from git-scm.com (needed once: the first backend start
   downloads and builds the liboqs cryptography library).
4. **CMake** from cmake.org — during install, tick **"Add CMake to the system
   PATH"**.
5. **Visual Studio Build Tools** (free) from visualstudio.microsoft.com:
   choose the **"Desktop development with C++"** workload. This is the C
   compiler the liboqs build needs. This download is large — start it early.

Check each one in a terminal (Command Prompt or PowerShell) with one command
at a time:

```
python --version
```

```
node --version
```

```
npm --version
```

```
git --version
```

```
cmake --version
```

If any of these says "not recognized", that program is not on PATH yet — fix
that one before continuing.

## Step 1 — Extract the zip on D:

1. Copy `quantumshield-x.zip` to `D:\`.
2. Right-click it → **Extract All** → extract to `D:\`.
3. You must end up with this exact folder:

```
D:\quantumshield-x
```

Open that folder. Inside it you must see `README.md`, `backend`, `frontend`.
If you see `quantumshield-x` inside `quantumshield-x` again, you extracted one
level too deep — move the inner folder out to `D:\quantumshield-x`.

## Step 2 — Install backend dependencies (one command at a time)

Open a terminal **inside** `D:\quantumshield-x\backend`
(File Explorer → click the address bar → type `cmd` → Enter).

Run this command, then wait for it to finish:

```
pip install -r requirements.txt
```

If pip complains about an "externally managed environment", run this instead:

```
pip install --break-system-packages -r requirements.txt
```

This installs FastAPI, liboqs-python, cryptography, and the rest.

## Step 3 — Start the backend (first start builds liboqs — be patient)

In the same terminal, run:

```
python -m uvicorn app.main:app --port 8000
```

**First run only:** you will see liboqs downloading and building. This takes
**5–15 minutes** and must not be interrupted. It happens once; later starts
are fast. When it is ready you will see a line like:

```
Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

**Leave this terminal open.** Do not close it while using the app.

Check it works — open this link in your browser:

```
http://localhost:8000/health
```

You should see: `{"status":"ok"}`.

## Step 4 — Install and start the frontend (second terminal)

Open a **second** terminal **inside** `D:\quantumshield-x\frontend`.

Run this command, then wait for it to finish:

```
npm install
```

Then run:

```
npm run dev
```

Wait for a line like:

```
Local: http://localhost:5173/
```

**Leave this terminal open too.**

## Step 5 — Open the app and click this first

Open in your browser:

```
http://localhost:5173
```

Log in with a demo account (demo-only):

| User | Password |
|---|---|
| `user` | `demo123` |
| `admin` | `admin123` |

**Click this first, in this order:**

1. **Key Management** → pick `ML-KEM-768` → **Generate keypair** → **Download
   private key** (keep this file — the server never stores it and cannot
   recover it) → **Publish as my ML-KEM public key**.
2. Do the same for `ML-DSA-65` → **Publish as my ML-DSA public key**.
3. **Cryptography Lab** → ML-KEM roundtrip → Encapsulate → Decapsulate +
   verify. You should see **Shared-secret match: YES**.
4. **Dashboard** — the numbers move as you use the app. Nothing here is
   hardcoded.
5. **Quantum Simulator** and **Algorithm Comparison** — the comparison page
   measures timings live on your machine.

## Step 6 — Stopping the app

Press `Ctrl + C` in each terminal, then close them. To start again later,
repeat Step 3 (backend) and Step 4's `npm run dev` (frontend) only — you do
not need to reinstall anything.

## Troubleshooting

- **"Port 8000 already in use"** — another backend is already running. Close
  the old terminal, or start on another port:
  `python -m uvicorn app.main:app --port 8001` (then the frontend still
  expects 8000, so prefer closing the old one).
- **Backend page shows nothing / frontend says "Backend offline"** — the
  backend terminal is not running. Go back to Step 3.
- **First backend start fails during the liboqs build** — check Step 0:
  Git, CMake, and the C++ Build Tools must all be installed, then try Step 3
  again.
- **"npm" not recognized** — Node.js is not on PATH. Reinstall Node.js and
  tick the PATH option, then reopen the terminal.
- **Out of disk space** — keep everything on D:. Do not copy the project to
  Desktop or Documents (those live on C:).
