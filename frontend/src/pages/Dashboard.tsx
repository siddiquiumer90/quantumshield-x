import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { KeyRound, PenLine, BadgeCheck, Activity, MessageSquare, FileLock, Users } from 'lucide-react';
import { api } from '../api';

type Dash = {
  total_operations: number; total_signatures: number; total_verifications: number;
  successful_verifications: number;
  algorithm_usage: { algorithm: string; count: number }[];
  recent_events: { id: number; operation: string; algorithm: string; username: string | null; success: boolean; created_at: string }[];
  active_algorithms: string[]; total_messages: number; total_files: number; total_users: number;
};

export default function Dashboard() {
  const [d, setD] = useState<Dash | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { api<Dash>('/api/dashboard').then(setD).catch((e) => setError(e.message)); }, []);

  if (error) return <div className="err">{error}</div>;
  if (!d) return <p className="text-slate-400">Loading dashboard…</p>;

  const cards = [
    { icon: Activity, label: 'Encryption operations', value: d.total_operations },
    { icon: PenLine, label: 'Signatures generated', value: d.total_signatures },
    { icon: BadgeCheck, label: 'Successful verifications', value: `${d.successful_verifications} / ${d.total_verifications}` },
    { icon: KeyRound, label: 'Active algorithms', value: d.active_algorithms.length },
    { icon: MessageSquare, label: 'Secure messages', value: d.total_messages },
    { icon: FileLock, label: 'Encrypted files', value: d.total_files },
    { icon: Users, label: 'Registered users', value: d.total_users },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Security Dashboard</h1>
      <p className="text-sm text-slate-400 mb-6">Every number below comes from the live database — nothing is hardcoded.</p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <div key={c.label} className="glass p-4">
              <Icon className="text-cyan-400" size={20} />
              <p className="text-2xl font-bold mt-2">{c.value}</p>
              <p className="text-xs text-slate-400">{c.label}</p>
            </div>
          );
        })}
      </div>

      <div className="grid lg:grid-cols-2 gap-4 mt-4">
        <div className="glass p-5">
          <h2 className="font-semibold mb-3">Algorithm usage</h2>
          {d.algorithm_usage.length === 0
            ? <p className="text-sm text-slate-400">No operations yet — generate a key in the Crypto Lab to see this chart fill in.</p>
            : <ResponsiveContainer width="100%" height={240}>
                <BarChart data={d.algorithm_usage}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="algorithm" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #164e63' }} />
                  <Bar dataKey="count">
                    {d.algorithm_usage.map((_, i) => <Cell key={i} fill={i % 2 ? '#7c3aed' : '#0284c7'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>}
        </div>
        <div className="glass p-5">
          <h2 className="font-semibold mb-3">Recent security events</h2>
          {d.recent_events.length === 0
            ? <p className="text-sm text-slate-400">No events yet.</p>
            : <table className="w-full text-sm">
                <thead><tr className="text-left text-slate-400"><th>Operation</th><th>Algorithm</th><th>User</th><th>Status</th></tr></thead>
                <tbody>
                  {d.recent_events.map((e) => (
                    <tr key={e.id} className="border-t border-white/5">
                      <td className="py-1.5">{e.operation}</td>
                      <td className="mono">{e.algorithm}</td>
                      <td>{e.username || '—'}</td>
                      <td>{e.success ? <span className="text-emerald-400">✓ ok</span> : <span className="text-red-400">✗ failed</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>}
          <p className="text-xs text-slate-500 mt-3">PQC migration readiness: run the assessment in the Documentation page's API list (POST /api/migration) or the Crypto Lab's hybrid section.</p>
        </div>
      </div>
    </div>
  );
}
