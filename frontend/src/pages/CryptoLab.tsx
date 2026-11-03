import { useState } from 'react';
import { api } from '../api';

function Field({ label, value, onChange, mono, textarea }: { label: string; value: string; onChange: (v: string) => void; mono?: boolean; textarea?: boolean }) {
  return (
    <div className="mb-3">
      <label className="label">{label}</label>
      {textarea
        ? <textarea className={`input ${mono ? 'mono' : ''}`} rows={3} value={value} onChange={(e) => onChange(e.target.value)} />
        : <input className={`input ${mono ? 'mono' : ''}`} value={value} onChange={(e) => onChange(e.target.value)} />}
    </div>
  );
}

function Result({ data }: { data: unknown }) {
  if (data === null) return null;
  return <pre className="mono bg-black/40 border border-sky-500/20 rounded-lg p-3 mt-3 overflow-auto max-h-64">{JSON.stringify(data, null, 2)}</pre>;
}

export default function CryptoLab() {
  // KEM section
  const [kemAlg, setKemAlg] = useState('ML-KEM-768');
  const [kemKeys, setKemKeys] = useState<{ public_key: string; private_key: string } | null>(null);
  const [kemEnc, setKemEnc] = useState<Record<string, unknown> | null>(null);
  const [kemMatch, setKemMatch] = useState<boolean | null>(null);
  // AES section
  const [plain, setPlain] = useState('Hello, quantum-safe world!');
  const [aesKey, setAesKey] = useState('');
  const [aesOut, setAesOut] = useState<Record<string, unknown> | null>(null);
  const [aesDec, setAesDec] = useState('');
  // Hybrid section
  const [hybKeys, setHybKeys] = useState<Record<string, string> | null>(null);
  const [hybEnc, setHybEnc] = useState<Record<string, unknown> | null>(null);
  const [hybDec, setHybDec] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function run<T>(fn: () => Promise<T>, set: (v: T) => void) {
    setError(''); setBusy(true);
    try { set(await fn()); } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Cryptography Lab</h1>
      <div className="warn mb-6">Lab warning: never paste real secrets, passwords, or production private keys here. This is a demonstration environment — generated keys are for learning and testing only.</div>
      {error && <div className="err mb-4">{error}</div>}

      <div className="glass p-5 mb-4">
        <h2 className="font-semibold mb-3">1 · ML-KEM key encapsulation roundtrip</h2>
        <div className="flex gap-2 mb-3">
          <select className="input max-w-xs" value={kemAlg} onChange={(e) => setKemAlg(e.target.value)}>
            <option>ML-KEM-512</option><option>ML-KEM-768</option><option>ML-KEM-1024</option>
          </select>
          <button className="btn" disabled={busy} onClick={() => run(() => api('/api/keys/generate', { method: 'POST', body: JSON.stringify({ algorithm: kemAlg }) }), setKemKeys as never)}>Generate keypair</button>
        </div>
        {kemKeys && <>
          <Field label="Public key (base64)" value={kemKeys.public_key} onChange={() => {}} mono textarea />
          <div className="flex gap-2">
            <button className="btn" disabled={busy} onClick={() => run(() => api('/api/kem/encaps', { method: 'POST', body: JSON.stringify({ algorithm: kemAlg, public_key: kemKeys.public_key }) }), setKemEnc as never)}>Encapsulate</button>
            {kemEnc && <button className="btn btn-secondary" disabled={busy} onClick={async () => {
              setError(''); setBusy(true);
              try {
                const r = await api<{ match: boolean }>('/api/kem/decaps-verify', { method: 'POST', body: JSON.stringify({ algorithm: kemAlg, private_key: kemKeys.private_key, ciphertext: kemEnc['ciphertext'], expected_secret_sha256: kemEnc['secret_sha256'] }) });
                setKemMatch(r.match);
              } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
              finally { setBusy(false); }
            }}>Decapsulate + verify</button>}
          </div>
          {kemMatch !== null && <div className={kemMatch ? 'ok mt-3' : 'err mt-3'}>Shared-secret match: {kemMatch ? 'YES ✓ — encapsulation and decapsulation agree' : 'NO ✗'}</div>}
          <p className="text-xs text-slate-500 mt-2">The shared secret itself is never sent to or from the server — only its SHA-256 commitment is compared.</p>
          <Result data={kemEnc} />
        </>}
      </div>

      <div className="glass p-5 mb-4">
        <h2 className="font-semibold mb-3">2 · AES-256-GCM encrypt / decrypt</h2>
        <Field label="Plaintext" value={plain} onChange={setPlain} textarea />
        <button className="btn" disabled={busy} onClick={() => run(() => api('/api/symmetric/encrypt', { method: 'POST', body: JSON.stringify({ plaintext: plain }) }), setAesOut as never)}>Encrypt (new random key)</button>
        <Result data={aesOut} />
        {aesOut && <div className="mt-3">
          <Field label="AES key (base64)" value={aesKey || String(aesOut['key'])} onChange={setAesKey} mono />
          <button className="btn btn-secondary" disabled={busy} onClick={async () => {
            setError(''); setBusy(true);
            try {
              const r = await api<{ plaintext: string }>('/api/symmetric/decrypt', { method: 'POST', body: JSON.stringify({ key: aesKey || String(aesOut['key']), nonce: aesOut['nonce'], ciphertext: aesOut['ciphertext'] }) });
              setAesDec(r.plaintext);
            } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
            finally { setBusy(false); }
          }}>Decrypt</button>
          {aesDec && <div className="ok mt-3">Decrypted: {aesDec}</div>}
        </div>}
      </div>

      <div className="glass p-5">
        <h2 className="font-semibold mb-3">3 · Hybrid mode — X25519 + ML-KEM-768</h2>
        <p className="text-sm text-slate-400 mb-3">Standard hybrid KEM combiner: HKDF-SHA256(X25519 secret ‖ ML-KEM-768 secret) → AES-256-GCM key. Secure if either component holds.</p>
        <button className="btn" disabled={busy} onClick={() => run(() => api('/api/hybrid/keygen', { method: 'POST' }), setHybKeys as never)}>Generate hybrid keypair</button>
        {hybKeys && <>
          <div className="flex gap-2 mt-3">
            <button className="btn btn-secondary" disabled={busy} onClick={() => run(() => api('/api/hybrid/encrypt', { method: 'POST', body: JSON.stringify({ x25519_public_key: hybKeys['x25519_public_key'], kem_public_key: hybKeys['kem_public_key'], plaintext: plain }) }), setHybEnc as never)}>Hybrid encrypt</button>
            {hybEnc && <button className="btn btn-secondary" disabled={busy} onClick={async () => {
              setError(''); setBusy(true);
              try {
                const r = await api<{ plaintext: string }>('/api/hybrid/decrypt', { method: 'POST', body: JSON.stringify({ x25519_private_key: hybKeys['x25519_private_key'], kem_private_key: hybKeys['kem_private_key'], x25519_public_key: hybEnc['x25519_public_key'], kem_ciphertext: hybEnc['kem_ciphertext'], nonce: hybEnc['nonce'], ciphertext: hybEnc['ciphertext'] }) });
                setHybDec(r.plaintext);
              } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
              finally { setBusy(false); }
            }}>Hybrid decrypt</button>}
          </div>
          {hybDec && <div className="ok mt-3">Decrypted: {hybDec}</div>}
          <Result data={hybEnc} />
        </>}
      </div>
    </div>
  );
}
