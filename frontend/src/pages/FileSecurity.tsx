import { useEffect, useState } from 'react';
import { API_BASE, api, apiForm, getToken } from '../api';

type F = { id: number; original_name: string; size_bytes: number; sha256: string; sha3_256: string; signed: boolean; created_at: string };

export default function FileSecurity() {
  const [file, setFile] = useState<File | null>(null);
  const [kemPub, setKemPub] = useState('');
  const [files, setFiles] = useState<F[]>([]);
  const [kemPriv, setKemPriv] = useState('');
  const [signPriv, setSignPriv] = useState('');
  const [signPub, setSignPub] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);

  const load = () => api<F[]>('/api/files/list').then(setFiles).catch(() => {});
  useEffect(() => { load(); }, []);

  async function upload() {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { setError('File exceeds the 10 MB limit.'); return; }
    setError(''); setInfo(''); setBusy(true);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('kem_public_key', kemPub);
      const r = await apiForm<{ id: number; sha256: string; sha3_256: string }>('/api/files/upload', form);
      setInfo(`File #${r.id} encrypted and stored. SHA-256: ${r.sha256.slice(0, 24)}…`);
      load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Upload failed'); }
    finally { setBusy(false); }
  }

  async function download(f: F) {
    setError(''); setBusy(true);
    try {
      const res = await fetch(API_BASE + `/api/files/${f.id}/decrypt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
        body: JSON.stringify({ kem_private_key: kemPriv }),
      });
      if (!res.ok) throw new Error((await res.json() as { detail?: string }).detail || 'Decrypt failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = f.original_name; a.click();
      URL.revokeObjectURL(url);
      setInfo(`Decrypted ${f.original_name} — check your downloads.`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Decrypt failed'); }
    finally { setBusy(false); }
  }

  async function act(f: F, kind: 'verify-integrity' | 'sign' | 'verify-signature-with-key') {
    setError(''); setInfo(''); setBusy(true);
    try {
      const body: Record<string, string> = { kem_private_key: kemPriv };
      if (kind === 'sign') { body['signing_private_key'] = signPriv; body['signing_public_key'] = signPub; body['algorithm'] = 'ML-DSA-65'; }
      const r = await api<Record<string, unknown>>(`/api/files/${f.id}/${kind}`, { method: 'POST', body: JSON.stringify(body) });
      if (kind === 'verify-integrity') setInfo(`Integrity match: ${r['match'] ? 'YES ✓' : 'NO ✗'}`);
      if (kind === 'sign') setInfo('File signed with ML-DSA-65 ✓');
      if (kind === 'verify-signature-with-key') setInfo(`Signature valid: ${r['valid'] ? 'YES ✓' : 'NO ✗'}`);
      load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Action failed'); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">File Encryption</h1>
      <p className="text-sm text-slate-400 mb-4">Uploads capped at 10 MB. Allowed: PDF, TXT, DOCX, PNG, ZIP. Files are stored encrypted only; the original is never stored.</p>
      <div className="warn mb-4">Warning: only encrypt files you own and are allowed to share. Private keys pasted here are used in memory only and never stored.</div>
      {error && <div className="err mb-4">{error}</div>}
      {info && <div className="ok mb-4">{info}</div>}

      <div className="glass p-5 mb-4">
        <h2 className="font-semibold mb-3">Upload & encrypt</h2>
        <input type="file" className="input mb-3" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <label className="label">Recipient ML-KEM-768 public key (base64)</label>
        <textarea className="input mono mb-3" rows={2} value={kemPub} onChange={(e) => setKemPub(e.target.value)} />
        <button className="btn" disabled={busy || !file || !kemPub} onClick={upload}>Encrypt & upload</button>
      </div>

      <div className="glass p-5">
        <h2 className="font-semibold mb-3">Your files — actions need your ML-KEM private key</h2>
        <label className="label">Your ML-KEM-768 private key (base64)</label>
        <textarea className="input mono mb-3" rows={2} value={kemPriv} onChange={(e) => setKemPriv(e.target.value)} />
        <label className="label">ML-DSA-65 private key (for signing)</label>
        <textarea className="input mono mb-3" rows={2} value={signPriv} onChange={(e) => setSignPriv(e.target.value)} />
        <label className="label">ML-DSA-65 public key (stored as the signer key)</label>
        <textarea className="input mono mb-3" rows={2} value={signPub} onChange={(e) => setSignPub(e.target.value)} />
        {files.length === 0 && <p className="text-sm text-slate-400">No files yet.</p>}
        {files.map((f) => (
          <div key={f.id} className="border-t border-white/10 py-3">
            <p className="text-sm"><b>{f.original_name}</b> · {(f.size_bytes / 1024).toFixed(1)} KB · {f.signed ? 'signed ✓' : 'unsigned'}</p>
            <p className="mono text-slate-500">SHA-256: {f.sha256}</p>
            <p className="mono text-slate-500">SHA3-256: {f.sha3_256}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              <button className="btn btn-secondary" disabled={busy || !kemPriv} onClick={() => download(f)}>Decrypt & download</button>
              <button className="btn btn-secondary" disabled={busy || !kemPriv} onClick={() => act(f, 'verify-integrity')}>Verify integrity</button>
              <button className="btn btn-secondary" disabled={busy || !kemPriv || !signPriv || !signPub} onClick={() => act(f, 'sign')}>Sign file</button>
              <button className="btn btn-secondary" disabled={busy || !kemPriv} onClick={() => act(f, 'verify-signature-with-key')}>Verify signature</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
