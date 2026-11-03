# QUANTUMSHIELD X — Hosting par Deploy Guide (Render)

Ye guide poora project internet par live karne ke liye hai, taaki friend
mobile browser se sirf link tap karke poora project khol sake.
Total time: lagbhag 30–45 minute (backend ka pehla build 10–20 minute
is me shamil hai). Chahiye: GitHub account aur Render account — dono free.

## Step 1 — Code GitHub par dalo

1. Laptop par ZIP extract karo (D: drive par), folder ka naam
   `quantumshield-x` hoga.
2. github.com kholo, sign in karo, **New repository** par click karo.
   Naam rakho `quantumshield-x`, **Public** chuno, Create par click karo.
3. Naye repo page par **uploading an existing file** link par click karo.
   Extract kiye hue folder ke andar ki saari files aur folders wahan
   drag-drop karo, phir **Commit changes** par click karo.
   (ZIP me `node_modules` aur `dist` nahi hain, isliye iski tension nahi.)
4. Confirm karo: repo me `render.yaml`, `backend/` aur `frontend/`
   dikhna chahiye.

## Step 2 — Render account banao

1. render.com kholo, **Sign Up with GitHub** par click karo aur
   GitHub authorize karo.

## Step 3 — Blueprint se deploy karo

1. Render Dashboard me **New -> Blueprint** par click karo.
2. `quantumshield-x` repo select karo, phir **Apply** par click karo.
3. Teen cheezein ban jayengi: `quantumshield-backend` (web service),
   `quantumshield-frontend` (static site) aur `quantumshield-db`
   (database). Env vars `render.yaml` se apne aap set ho jayenge.
4. Backend ka build 10–20 minute le sakta hai (liboqs compile hota hai).
   Beech me **Cancel ya redeploy mat karna**. Progress dekhne ke liye
   backend service ke **Logs** tab me jao.

## Step 4 — SPA rewrite rule lagao (zaroori)

Iske bina `/dashboard` jaise pages refresh karne par 404 aayega.

1. Frontend service (`quantumshield-frontend`) kholo.
2. **Redirects/Rewrites** me jao, **Add Rule** par click karo.
3. Source: `/*`, Destination: `/index.html`, Action: **Rewrite**,
   phir Save karo.

## Step 5 — Test karo

1. Frontend ka URL kholo (jaise
   `https://quantumshield-frontend.onrender.com`).
   Pehli baar khulne me lagbhag 1 minute lag sakta hai — free service
   sleep se jagta hai (cold start), ye normal hai.
2. Login karo: `user` / `demo123` (admin ke liye `admin` / `admin123`).
3. Lab me ek test karo: key generate karo, phir encrypt aur decrypt —
   sab chalna chahiye.

## Step 6 — Friend ko bhejo

Wahi frontend URL friend ko bhej do. Mobile browser me khul jayega,
kuch install nahi karna padega.

## Agar kuch atak jaye

- **Frontend par "backend unreachable" dikhe:** Backend service ke
  **Environment** me `FRONTEND_ORIGIN` check karo — us me frontend ka
  URL hona chahiye. Frontend service ke **Environment** me
  `VITE_API_URL` check karo — us me backend ka URL hona chahiye.
  Galat ho to sahi value daal kar Save karo (frontend dobara build hoga).
- **Backend build fail ho:** Logs me aakhri error ka screenshot mujhe
  bhej do, main dekh lunga.
- **Free database:** Render ka free database 30 din me expire ho sakta
  hai. Demo ke liye theek hai; lambi use ke liye paid plan lena padega.
- **Upload ki hui files:** Redeploy par mit sakti hain (ephemeral disk).
  Demo ke liye theek hai.
- **Demo passwords:** `user/demo123` aur `admin/admin123` sirf demo ke
  liye hain. Asli use se pehle inhe badal dena.
