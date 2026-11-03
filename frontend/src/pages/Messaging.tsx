import { useEffect, useState } from 'react';
import { api } from '../api';

type Msg = { id: number; sender: string; recipient: string; kem_algorithm: string; kem_ciphertext: string; nonce: string; ciphertext: string; signature: string; created_at: string };

export default function Messaging() {
  const [recipient, setRecipient] = useState('');
  const [text, setText] = useState('');
  const [signKey, setSignKey] = useState('');
  const [inbox, setInbox] = useState<Msg[]>([]);
  const [sent, setSent] = useState<Msg[]>([]);
  const [decKey, setDecKey] = useState('');
  const [decrypted, setDecrypted] = useState<Record<number, string>>({});
  const [verified, setVerified] = useState<Record<number, boolean>>({});
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);

  const load = () => {
    api<Msg[]>('/api/messages/inbox').then(setInbox).catch(() => {});
    api<Msg[]>('/api/messages/sent').then(setSent).catch(() => {});
  };
  useEffect(load, []);

  async function send() {
    setError(''); setInfo(''); setBusy(true);
    try {
      const r = await api<{ id: number }>('/api/messages/send', { method: 'POST', body: JSON.stringify({ recipient_username: recipient, plaintext: text, signing_private_key: signKey }) });
      setInfo(`Message #${r.id} encrypted and stored (ciphertext only).`);
      setText(''); load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Send failed'); }
    finally { setBusy(false); }
  }

  async function decrypt(m: Msg) {
    setError(''); setBusy(true);
    try {
      const r = await api<{ plaintext: string }>(`/api/messages/${m.id}/decrypt`, { method: 'POST', body: JSON.stringify({ kem_private_key: decKey }) });
      setDecrypted((d) => ({ ...d, [m.id]: r.plaintext }));
    } catch (e) { setError(e instanceof Error ? e.message : 'Decrypt failed'); }
    finally { setBusy(false); }
  }

  async function verify(m: Msg) {
    const pt = decrypted[m.id];
    if (!pt) { setError('Decrypt the message first, then verify it.'); return; }
    setError(''); setBusy(true);
    try {
      const r = await api<{ valid: boolean }>('/api/messages/verify-text', { method: 'POST', body: JSON.stringify({ message_id: m.id, plaintext: pt }) });
      setVerified((v) => ({ ...v, [m.id]: r.valid }));
    } catch (e) { setError(e instanceof Error ? e.message : 'Verify failed'); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Secure Messaging</h1>
      <p className="text-sm text-slate-400 mb-4">ML-KEM-768 key establishment + AES-256-GCM + ML-DSA-65 signatures. Messages are stored as ciphertext only.</p>
      <div className="warn mb-4">Before sending: both users must publish public keys (Key Management page). Your ML-DSA private key is used in memory only for this send — it is never stored.</div>
      {error && <div className="err mb-4">{error}</div>}
      {info && <div className="ok mb-4">{info}</div>}

      <div className="glass p-5 mb-4">
        <h2 className="font-semibold mb-3">Send an encrypted message</h2>
        <label className="label">Recipient username</label>
        <input className="input mb-3" value={recipient} onChange={(e) => setRecipient(e.target.value)} placeholder="e.g. bob" />
        <label className="label">Message</label>
        <textarea className="input mb-3" rows={3} value={text} onChange={(e) => setText(e.target.value)} />
        <label className="label">Your ML-DSA-65 private key (base64, pasted from your one-time download)</label>
        <textarea className="input mono mb-3" rows={2} value={signKey} onChange={(e) => setSignKey(e.target.value)} />
        <button className="btn" disabled={busy || !recipient || !text || !signKey} onClick={send}>Encrypt & send</button>
      </div>

      <div className="glass p-5 mb-4">
        <h2 className="font-semibold mb-3">Inbox — decrypt with your ML-KEM private key</h2>
        <label className="label">Your ML-KEM-768 private key (base64)</label>
        <textarea className="input mono mb-3" rows={2} value={decKey} onChange={(e) => setDecKey(e.target.value)} />
        {inbox.length === 0 && <p className="text-sm text-slate-400">Inbox is empty.</p>}
        {inbox.map((m) => (
          <div key={m.id} className="border-t border-white/10 py-3">
            <p className="text-sm"><b>From:</b> {m.sender} · <b>{m.kem_algorithm}</b> · {m.created_at}</p>
            <p className="mono text-slate-500 mt-1">ciphertext: {m.ciphertext.slice(0, 80)}…</p>
            <div className="flex gap-2 mt-2">
              <button className="btn btn-secondary" disabled={busy || !decKey} onClick={() => decrypt(m)}>Decrypt</button>
              <button className="btn btn-secondary" disabled={busy} onClick={() => verify(m)}>Verify signature</button>
            </div>
            {decrypted[m.id] && <div className="ok mt-2">Decrypted: {decrypted[m.id]}</div>}
            {verified[m.id] !== undefined && <div className={verified[m.id] ? 'ok mt-2' : 'err mt-2'}>Signature valid: {verified[m.id] ? 'YES ✓' : 'NO ✗ — message may be tampered'}</div>}
          </div>
        ))}
      </div>

      <div className="glass p-5">
        <h2 className="font-semibold mb-3">Sent messages</h2>
        {sent.length === 0 && <p className="text-sm text-slate-400">Nothing sent yet.</p>}
        {sent.map((m) => (
          <p key={m.id} className="text-sm border-t border-white/10 py-2">To <b>{m.recipient}</b> · {m.kem_algorithm} · {m.created_at} · <span className="text-emerald-400">● encrypted</span></p>
        ))}
      </div>
    </div>
  );
}
