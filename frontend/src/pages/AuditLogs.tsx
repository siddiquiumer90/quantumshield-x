import { useEffect, useState } from 'react';
import { api } from '../api';

type Entry = { id: number; actor: string; action: string; details: string; prev_hash: string; entry_hash: string; created_at: string };

export default function AuditLogs() {
  const [rows, setRows] = useState<Entry[]>([]);
  const [chain, setChain] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => { api<Entry[]>('/api/audit/list').then(setRows).catch((e) => setError(e.message)); }, []);

  async function verify() {
    setBusy(true); setError('');
    try { setChain(await api('/api/audit/verify-chain')); }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Security Audit Logs</h1>
      <p className="text-sm text-slate-400 mb-4">Every entry is chained: each row hashes the previous row's hash, so editing or deleting any row breaks the chain.</p>
      {error && <div className="err mb-4">{error}</div>}
      <button className="btn mb-4" disabled={busy} onClick={verify}>Verify audit chain</button>
      {chain && <div className={chain['valid'] ? 'ok mb-4' : 'err mb-4'}>
        Chain valid: {String(chain['valid'])} · Checked {String(chain['checked'])} of {String(chain['total'])} entries
        {chain['broken_at_id'] ? ` · Broken at entry #${String(chain['broken_at_id'])}` : ''}
      </div>}
      <div className="glass p-5 overflow-auto">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-400"><th>#</th><th>Actor</th><th>Action</th><th>Details</th><th>Entry hash</th><th>When</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-white/5">
                <td className="py-2">{r.id}</td>
                <td>{r.actor}</td>
                <td>{r.action}</td>
                <td className="text-slate-300">{r.details}</td>
                <td className="mono">{r.entry_hash.slice(0, 16)}…</td>
                <td>{r.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="text-sm text-slate-400">No audit entries yet.</p>}
      </div>
    </div>
  );
}
