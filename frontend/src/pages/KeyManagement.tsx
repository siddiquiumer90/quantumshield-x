import { useState } from 'react';
import { api } from '../api';

export default function KeyManagement() {
  const [alg, setAlg] = useState('ML-KEM-768');
  const [keys, setKeys] = useState<{ public_key: string; private_key: string; public_key_bytes: number; private_key_bytes: number } | null>(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);

  async function gen() {
    setError(''); setInfo(''); setBusy(true);
    try {
      const k = await api<{ public_key: string; private_key: string; public_key_bytes: number; private_key_bytes: number }>('/api/keys/generate', { method: 'POST', body: JSON.stringify({ algorithm: alg }) });
      setKeys(k);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  function download(text: string, name: string) {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name; a.click();
    URL.revokeObjectURL(url);
  }

  async function publish(kind: 'kem' | 'dsa') {
    if (!keys) return;
    setError(''); setInfo(''); setBusy(true);
    try {
      await api('/api/auth/publish-keys', { method: 'POST', body: JSON.stringify(kind === 'kem' ? { kem_public_key: keys.public_key } : { dsa_public_key: keys.public_key }) });
      setInfo(`Public key published to your profile as the ${kind === 'kem' ? 'ML-KEM' : 'ML-DSA'} key. Others can now encrypt to you / verify you.`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Key Management</h1>
      <p className="text-sm text-slate-400 mb-4">Generate real keypairs. The private key is shown exactly once and is never stored on the server — download it now or it is gone.</p>
      <div className="warn mb-4">WARNING: the server does NOT store private keys and cannot recover them. If you lose the download, generate a fresh keypair.</div>
      {error && <div className="err mb-4">{error}</div>}
      {info && <div className="ok mb-4">{info}</div>}

      <div className="glass p-5">
        <div className="flex flex-wrap gap-2 mb-4">
          <select className="input max-w-xs" value={alg} onChange={(e) => setAlg(e.target.value)}>
            <optgroup label="ML-KEM (FIPS 203)"><option>ML-KEM-512</option><option>ML-KEM-768</option><option>ML-KEM-1024</option></optgroup>
            <optgroup label="ML-DSA / SLH-DSA (FIPS 204 / 205)"><option>ML-DSA-44</option><option>ML-DSA-65</option><option>ML-DSA-87</option><option value="SLH_DSA_PURE_SHA2_128S">SLH-DSA-SHA2-128s</option><option value="SLH_DSA_PURE_SHA2_192S">SLH-DSA-SHA2-192s</option><option value="SLH_DSA_PURE_SHAKE_128S">SLH-DSA-SHAKE-128s</option></optgroup>
            <optgroup label="Classical"><option>RSA-2048</option><option>ECC-P-256</option></optgroup>
          </select>
          <button className="btn" disabled={busy} onClick={gen}>Generate keypair</button>
        </div>
        {keys && <>
          <p className="text-sm text-slate-400 mb-3">Public key: {keys.public_key_bytes} bytes · Private key: {keys.private_key_bytes} bytes · Server storage: none</p>
          <label className="label">Public key</label>
          <p className="mono bg-black/40 border border-sky-500/20 rounded-lg p-3 mb-3">{keys.public_key}</p>
          <label className="label">Private key — one-time display</label>
          <p className="mono bg-black/40 border border-amber-500/30 rounded-lg p-3 mb-3">{keys.private_key}</p>
          <div className="flex flex-wrap gap-2">
            <button className="btn" onClick={() => download(keys.private_key, `${alg}-private-key.txt`)}>Download private key</button>
            <button className="btn btn-secondary" onClick={() => download(keys.public_key, `${alg}-public-key.txt`)}>Download public key</button>
            <button className="btn btn-secondary" onClick={() => publish('kem')}>Publish as my ML-KEM public key</button>
            <button className="btn btn-secondary" onClick={() => publish('dsa')}>Publish as my ML-DSA public key</button>
          </div>
          <p className="text-xs text-slate-500 mt-3">Publishing only ever sends the public key. Use the matching algorithm for each publish button (ML-KEM keys for messaging encryption, ML-DSA keys for signatures).</p>
        </>}
      </div>
    </div>
  );
}
