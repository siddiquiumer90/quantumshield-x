import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { api } from '../api';

export default function Auth() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(''); setBusy(true);
    try {
      const data = await api<{ username: string; role: string; token: string }>(
        `/api/auth/${mode}`, { method: 'POST', body: JSON.stringify({ username, password }) });
      localStorage.setItem('qs_token', data.token);
      localStorage.setItem('qs_user', JSON.stringify({ username: data.username, role: data.role }));
      nav('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally { setBusy(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="glass p-8 w-full max-w-md">
        <div className="flex items-center gap-2 mb-1">
          <Shield className="text-cyan-400" size={26} />
          <h1 className="text-xl font-bold">QUANTUMSHIELD X</h1>
        </div>
        <p className="text-sm text-slate-400 mb-6">Sign in to the post-quantum platform.</p>
        <div className="flex gap-2 mb-5">
          <button className={`btn flex-1 justify-center ${mode === 'login' ? '' : 'btn-secondary'}`} onClick={() => setMode('login')}>Log in</button>
          <button className={`btn flex-1 justify-center ${mode === 'register' ? '' : 'btn-secondary'}`} onClick={() => setMode('register')}>Register</button>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label">Username</label>
            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
          </div>
          {error && <div className="err">{error}</div>}
          <button className="btn w-full justify-center" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}
          </button>
        </form>
        <div className="warn mt-5">
          Demo accounts (demo-only, change them in production):<br />
          <span className="mono">user / demo123</span> · <span className="mono">admin / admin123</span>
        </div>
        <Link to="/" className="text-sm text-cyan-300 block mt-4">← Back to landing page</Link>
      </div>
    </div>
  );
}
