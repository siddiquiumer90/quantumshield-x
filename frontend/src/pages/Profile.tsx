import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Profile() {
  const [me, setMe] = useState<{ username: string; role: string; kem_public_key: string | null; dsa_public_key: string | null; created_at: string } | null>(null);
  const [kemPub, setKemPub] = useState('');
  const [dsaPub, setDsaPub] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);

  const load = () => api<typeof me>('/api/auth/me').then(setMe).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function publish() {
    setError(''); setInfo(''); setBusy(true);
    try {
      await api('/api/auth/publish-keys', { method: 'POST', body: JSON.stringify({ kem_public_key: kemPub || undefined, dsa_public_key: dsaPub || undefined }) });
      setInfo('Public keys published.');
      load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  if (error) return <div className="err">{error}</div>;
  if (!me) return <p className="text-slate-400">Loading profile…</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">User Profile</h1>
      <div className="glass p-5 mb-4">
        <p className="text-sm"><b>Username:</b> {me.username}</p>
        <p className="text-sm"><b>Role:</b> {me.role}</p>
        <p className="text-sm"><b>Account created:</b> {me.created_at}</p>
        <p className="text-sm mt-2"><b>ML-KEM public key published:</b> {me.kem_public_key ? 'yes ✓' : 'no — generate one in Key Management and publish it here'}</p>
        <p className="text-sm"><b>ML-DSA public key published:</b> {me.dsa_public_key ? 'yes ✓' : 'no — generate one in Key Management and publish it here'}</p>
      </div>
      <div className="glass p-5">
        <h2 className="font-semibold mb-3">Publish public keys</h2>
        <p className="text-sm text-slate-400 mb-3">Only public keys are ever sent here. Private keys are never uploaded.</p>
        <label className="label">ML-KEM public key (base64)</label>
        <textarea className="input mono mb-3" rows={2} value={kemPub} onChange={(e) => setKemPub(e.target.value)} />
        <label className="label">ML-DSA public key (base64)</label>
        <textarea className="input mono mb-3" rows={2} value={dsaPub} onChange={(e) => setDsaPub(e.target.value)} />
        {info && <div className="ok mb-3">{info}</div>}
        <button className="btn" disabled={busy || (!kemPub && !dsaPub)} onClick={publish}>Publish</button>
      </div>
    </div>
  );
}
