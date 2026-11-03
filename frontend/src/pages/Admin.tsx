import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Admin() {
  const [users, setUsers] = useState<{ id: number; username: string; role: string; kem_key_published: boolean; dsa_key_published: boolean; created_at: string }[] | null>(null);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api<typeof users>('/api/admin/users').then(setUsers).catch((e) => setError(e.message));
    api<typeof stats>('/api/admin/stats').then(setStats).catch(() => {});
  }, []);

  if (error) return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <div className="err">Access denied: {error}. This page requires the admin role (demo: admin / admin123).</div>
    </div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Admin Dashboard</h1>
      <p className="text-sm text-slate-400 mb-4">Admin-only area. Password hashes are never returned by any endpoint.</p>
      {stats && <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
        {Object.entries(stats).map(([k, v]) => (
          <div key={k} className="glass p-4"><p className="text-2xl font-bold">{v}</p><p className="text-xs text-slate-400">{k}</p></div>
        ))}
      </div>}
      <div className="glass p-5">
        <h2 className="font-semibold mb-3">Users</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-400"><th>ID</th><th>Username</th><th>Role</th><th>ML-KEM key</th><th>ML-DSA key</th><th>Created</th></tr></thead>
          <tbody>
            {(users || []).map((u) => (
              <tr key={u.id} className="border-t border-white/5">
                <td className="py-2">{u.id}</td>
                <td>{u.username}</td>
                <td>{u.role}</td>
                <td>{u.kem_key_published ? 'yes ✓' : 'no'}</td>
                <td>{u.dsa_key_published ? 'yes ✓' : 'no'}</td>
                <td>{u.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
