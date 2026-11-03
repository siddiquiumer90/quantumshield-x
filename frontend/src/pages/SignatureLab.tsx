import { useState } from 'react';
import { api } from '../api';

export default function SignatureLab() {
  const [alg, setAlg] = useState('ML-DSA-65');
  const [keys, setKeys] = useState<{ public_key: string; private_key: string } | null>(null);
  const [message, setMessage] = useState('Document: QuantumShield X agreement v1');
  const [sig, setSig] = useState('');
  const [valid, setValid] = useState<boolean | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function gen() {
    setError(''); setBusy(true);
    try {
      const k = await api<{ public_key: string; private_key: string }>('/api/keys/generate', { method: 'POST', body: JSON.stringify({ algorithm: alg }) });
      setKeys(k); setSig(''); setValid(null);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  async function sign() {
    if (!keys) return;
    setError(''); setBusy(true);
    try {
      const r = await api<{ signature: string }>('/api/sign', { method: 'POST', body: JSON.stringify({ algorithm: alg, private_key: keys.private_key, message }) });
      setSig(r.signature); setValid(null);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  async function verify(msg: string) {
    if (!keys || !sig) return;
    setError(''); setBusy(true);
    try {
      const r = await api<{ valid: boolean }>('/api/verify', { method: 'POST', body: JSON.stringify({ algorithm: alg, public_key: keys.public_key, message: msg, signature: sig }) });
      setValid(r.valid);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Digital Signature Lab</h1>
      <p className="text-sm text-slate-400 mb-4">Sign a document with ML-DSA, SLH-DSA, RSA-PSS or ECDSA — then verify it, and try the tamper test to see verification fail.</p>
      <div className="warn mb-4">Warning: never sign with a production private key here. Use freshly generated lab keys only.</div>
      {error && <div className="err mb-4">{error}</div>}

      <div className="glass p-5">
        <div className="flex flex-wrap gap-2 mb-3">
          <select className="input max-w-xs" value={alg} onChange={(e) => setAlg(e.target.value)}>
            <option>ML-DSA-44</option><option>ML-DSA-65</option><option>ML-DSA-87</option>
            <option value="SLH_DSA_PURE_SHA2_128S">SLH-DSA-SHA2-128s</option>
            <option value="SLH_DSA_PURE_SHA2_192S">SLH-DSA-SHA2-192s</option>
            <option value="SLH_DSA_PURE_SHAKE_128S">SLH-DSA-SHAKE-128s</option>
          </select>
          <button className="btn" disabled={busy} onClick={gen}>Generate keypair</button>
        </div>
        {keys && <>
          <label className="label">Document / message</label>
          <textarea className="input mb-3" rows={3} value={message} onChange={(e) => setMessage(e.target.value)} />
          <div className="flex flex-wrap gap-2">
            <button className="btn btn-secondary" disabled={busy} onClick={sign}>Sign document</button>
            {sig && <>
              <button className="btn btn-secondary" disabled={busy} onClick={() => verify(message)}>Verify signature</button>
              <button className="btn btn-secondary" disabled={busy} onClick={() => verify(message + ' (tampered)')}>Tamper test — verify altered text</button>
            </>}
          </div>
          {sig && <div className="mt-3"><label className="label">Signature (base64)</label><p className="mono bg-black/40 border border-sky-500/20 rounded-lg p-3">{sig}</p></div>}
          {valid !== null && <div className={valid ? 'ok mt-3' : 'err mt-3'}>Signature valid: {valid ? 'YES ✓' : 'NO ✗ — content or signature was changed'}</div>}
        </>}
      </div>
    </div>
  );
}
