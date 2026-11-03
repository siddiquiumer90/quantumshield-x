const ENDPOINTS: [string, string, string][] = [
  ['POST /api/auth/register', 'Create account', 'username, password'],
  ['POST /api/auth/login', 'Log in, get JWT', 'username, password'],
  ['GET /api/auth/me', 'Current user + published keys', 'auth'],
  ['POST /api/auth/publish-keys', 'Publish public keys to profile', 'auth, kem_public_key?, dsa_public_key?'],
  ['GET /api/keys/algorithms', 'Enabled algorithm lists', 'auth'],
  ['POST /api/keys/generate', 'Generate keypair (private key shown once)', 'auth, algorithm'],
  ['POST /api/kem/encaps', 'Encapsulate; returns ciphertext + secret commitment', 'auth, algorithm, public_key'],
  ['POST /api/kem/decaps-verify', 'Decapsulate and compare commitment', 'auth, algorithm, private_key, ciphertext, expected_secret_sha256'],
  ['POST /api/sign', 'Sign a message', 'auth, algorithm, private_key, message'],
  ['POST /api/verify', 'Verify a signature', 'auth, algorithm, public_key, message, signature'],
  ['POST /api/symmetric/encrypt', 'AES-256-GCM encrypt', 'auth, plaintext, key?'],
  ['POST /api/symmetric/decrypt', 'AES-256-GCM decrypt (tampering fails)', 'auth, key, nonce, ciphertext'],
  ['POST /api/hybrid/keygen', 'X25519 + ML-KEM-768 keypair', 'auth'],
  ['POST /api/hybrid/encrypt', 'Hybrid encrypt', 'auth, x25519_public_key, kem_public_key, plaintext'],
  ['POST /api/hybrid/decrypt', 'Hybrid decrypt', 'auth, private keys + bundle'],
  ['POST /api/messages/send', 'Send encrypted message', 'auth, recipient_username, plaintext, signing_private_key'],
  ['GET /api/messages/inbox', 'My received messages (ciphertext only)', 'auth'],
  ['GET /api/messages/sent', 'My sent messages', 'auth'],
  ['POST /api/messages/{id}/decrypt', 'Recipient decrypts a message', 'auth, kem_private_key'],
  ['POST /api/messages/verify-text', 'Verify a message signature', 'auth, message_id, plaintext'],
  ['POST /api/files/upload', 'Upload + encrypt (10 MB, pdf/txt/docx/png/zip)', 'auth, file, kem_public_key'],
  ['GET /api/files/list', 'My files', 'auth'],
  ['POST /api/files/{id}/decrypt', 'Decrypt + download a file', 'auth, kem_private_key'],
  ['POST /api/files/{id}/verify-integrity', 'Decrypt + re-hash + compare', 'auth, kem_private_key'],
  ['POST /api/files/{id}/sign', 'Sign a file with ML-DSA/SLH-DSA', 'auth, keys, algorithm'],
  ['POST /api/files/{id}/verify-signature-with-key', 'Verify a file signature', 'auth, kem_private_key'],
  ['GET /api/dashboard', 'Real counts from the database', 'auth'],
  ['GET /api/audit/list', 'Recent audit entries', 'auth'],
  ['GET /api/audit/verify-chain', 'Recompute the audit hash chain', 'auth'],
  ['GET /api/benchmark', 'Live-measured timings and sizes', 'auth'],
  ['POST /api/migration', 'Migration readiness score + recommendations', 'auth, systems[]'],
  ['POST /api/hndl', 'Mosca X+Y>Z exposure estimate (educational model)', 'auth, algorithm, secrecy_years, migration_years, threat_years_estimate'],
  ['GET /api/simulator', 'Classical-vs-quantum model + Shor/Grover explainers', 'auth'],
  ['GET /api/admin/users', 'User list (admin only)', 'admin'],
  ['GET /api/admin/stats', 'System totals (admin only)', 'admin'],
  ['GET /api/admin/audit', 'Full audit log (admin only)', 'admin'],
];

export default function Documentation() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Documentation</h1>
      <p className="text-sm text-slate-400 mb-6">Full API reference. Interactive docs are also available at <span className="mono">http://localhost:8000/docs</span> when the backend is running.</p>

      <div className="glass p-5 mb-4">
        <h2 className="font-semibold mb-3">Architecture</h2>
        <p className="text-sm text-slate-300">
          React + TypeScript frontend (Vite) talks to a FastAPI backend over REST. The backend uses
          liboqs-python (audited liboqs) for ML-KEM / ML-DSA / SLH-DSA and the <span className="mono">cryptography</span> package
          (OpenSSL) for RSA, ECC, X25519 and AES-256-GCM. SQLite is the default database (zero-setup);
          set <span className="mono">DATABASE_URL</span> for PostgreSQL in production. See <span className="mono">docs/ARCHITECTURE.md</span> in the repo for the diagram.
        </p>
        <h2 className="font-semibold mt-5 mb-3">Security rules enforced by the code</h2>
        <ul className="text-sm text-slate-300 list-disc ml-5 space-y-1">
          <li>Private keys are never stored server-side and never logged; they appear only in the direct generation response.</li>
          <li>Shared secrets are never returned by any endpoint; KEM verification uses a SHA-256 commitment.</li>
          <li>Messages and files are stored as ciphertext only.</li>
          <li>Passwords are bcrypt-hashed; auth uses JWT bearer tokens; admin routes require the admin role (non-admins get 403).</li>
          <li>Inputs are validated with Pydantic; uploads are capped at 10 MB with an extension allowlist.</li>
          <li>Rate limiting is applied per IP (Redis if configured, in-memory otherwise).</li>
          <li>Error responses are generic — no stack traces or secret material.</li>
        </ul>
        <h2 className="font-semibold mt-5 mb-3">Honest limitations</h2>
        <ul className="text-sm text-slate-300 list-disc ml-5 space-y-1">
          <li>This is a demonstration and research platform. It is not quantum-proof and not independently security-certified.</li>
          <li>Simulator and HNDL outputs are educational models, not quantum attacks or predictions.</li>
          <li>Demo accounts (user/demo123, admin/admin123) must be changed or disabled in production.</li>
          <li>Production deployment needs HTTPS, a strong QS_SECRET_KEY, and PostgreSQL — see README.</li>
        </ul>
      </div>

      <div className="glass p-5 overflow-auto">
        <h2 className="font-semibold mb-3">API endpoints</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-400"><th>Endpoint</th><th>What it does</th><th>Inputs</th></tr></thead>
          <tbody>
            {ENDPOINTS.map(([e, d, i]) => (
              <tr key={e} className="border-t border-white/5">
                <td className="mono py-1.5 pr-3">{e}</td>
                <td className="text-slate-300">{d}</td>
                <td className="mono text-slate-400">{i}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
