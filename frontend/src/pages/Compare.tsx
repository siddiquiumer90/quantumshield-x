import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { api } from '../api';

type Row = { algorithm: string; family: string; keygen_ms: number; encaps_ms: number; public_key_bytes: number | null; private_key_bytes: number | null; ciphertext_bytes: number | null; signature_bytes: number | null };

export default function Compare() {
  const [rows, setRows] = useState<Row[]>([]);
  const [note, setNote] = useState('');
  const [measuredAt, setMeasuredAt] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true); setError('');
    try {
      const r = await api<{ results: Row[]; note: string; measured_at: string }>('/api/benchmark');
      setRows(r.results); setNote(r.note); setMeasuredAt(r.measured_at);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }
  useEffect(() => { load(); }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Algorithm Comparison</h1>
      <p className="text-sm text-slate-400 mb-4">{note} Measured at: {measuredAt} · <button className="text-cyan-300 underline" disabled={busy} onClick={load}>Re-measure live</button></p>
      {error && <div className="err mb-4">{error}</div>}
      {busy && rows.length === 0 && <p className="text-slate-400">Measuring… (SLH-DSA takes a moment)</p>}

      {rows.length > 0 && <>
        <div className="glass p-5 mb-4">
          <h2 className="font-semibold mb-3">Key generation time (ms, log-friendly values shown raw)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="algorithm" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #164e63' }} />
              <Bar dataKey="keygen_ms">
                {rows.map((_, i) => <Cell key={i} fill={i % 2 ? '#7c3aed' : '#0284c7'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="glass p-5 mb-4">
          <h2 className="font-semibold mb-3">Encaps / sign time (ms)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="algorithm" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #164e63' }} />
              <Bar dataKey="encaps_ms">
                {rows.map((_, i) => <Cell key={i} fill={i % 2 ? '#7c3aed' : '#0284c7'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="glass p-5">
          <h2 className="font-semibold mb-3">Key, ciphertext & signature sizes (bytes)</h2>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-slate-400"><th>Algorithm</th><th>Family</th><th>Public key</th><th>Private key</th><th>Ciphertext</th><th>Signature</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.algorithm} className="border-t border-white/5">
                  <td className="py-2 font-semibold">{r.algorithm}</td>
                  <td>{r.family}</td>
                  <td>{r.public_key_bytes ?? '—'}</td>
                  <td>{r.private_key_bytes ?? '—'}</td>
                  <td>{r.ciphertext_bytes ?? '—'}</td>
                  <td>{r.signature_bytes ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-slate-500 mt-3">Takeaway: post-quantum keys and signatures are much larger than RSA/ECC — that size cost is the real migration trade-off, and it is why hybrid modes exist.</p>
        </div>
      </>}
    </div>
  );
}
