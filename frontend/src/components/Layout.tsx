import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Shield, LayoutDashboard, FlaskConical, MessagesSquare, FileLock, PenLine,
  Atom, BarChart3, KeyRound, ScrollText, GraduationCap, BookOpen, User, ShieldCheck, LogOut,
} from 'lucide-react';
import { API_BASE, getUser, logout } from '../api';

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/lab', label: 'Cryptography Lab', icon: FlaskConical },
  { to: '/messages', label: 'Secure Messaging', icon: MessagesSquare },
  { to: '/files', label: 'File Encryption', icon: FileLock },
  { to: '/signatures', label: 'Signature Lab', icon: PenLine },
  { to: '/simulator', label: 'Quantum Simulator', icon: Atom },
  { to: '/compare', label: 'Algorithm Comparison', icon: BarChart3 },
  { to: '/keys', label: 'Key Management', icon: KeyRound },
  { to: '/audit', label: 'Audit Logs', icon: ScrollText },
  { to: '/learn', label: 'Learning Center', icon: GraduationCap },
  { to: '/docs', label: 'Documentation', icon: BookOpen },
  { to: '/profile', label: 'Profile', icon: User },
  { to: '/admin', label: 'Admin', icon: ShieldCheck },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const user = getUser();
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(API_BASE + '/health')
      .then((r) => setOnline(r.ok))
      .catch(() => setOnline(false));
  }, []);

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 hidden md:flex flex-col border-r border-sky-500/15 bg-[#050d1f] p-4 gap-1">
        <Link to="/" className="flex items-center gap-2 px-2 py-3">
          <Shield className="text-cyan-400" size={26} />
          <span className="font-bold tracking-wide">QUANTUMSHIELD <span className="text-cyan-400">X</span></span>
        </Link>
        <div className="px-2 pb-2 text-xs flex items-center gap-2 text-slate-400">
          <span className={`inline-block w-2 h-2 rounded-full ${online ? 'bg-emerald-400' : 'bg-red-400'}`} />
          Backend {online === null ? 'checking…' : online ? 'online' : 'offline — start it on port 8000'}
        </div>
        {NAV.map((n) => {
          const Icon = n.icon;
          const active = loc.pathname === n.to;
          return (
            <Link key={n.to} to={n.to}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${active ? 'bg-sky-500/20 text-sky-200' : 'text-slate-300 hover:bg-white/5'}`}>
              <Icon size={17} /> {n.label}
            </Link>
          );
        })}
        <div className="mt-auto px-2 pt-4 border-t border-white/10">
          <p className="text-xs text-slate-400">Signed in as</p>
          <p className="text-sm font-semibold">{user?.username} <span className="text-cyan-400">({user?.role})</span></p>
          <button onClick={logout} className="btn btn-secondary mt-3 w-full justify-center">
            <LogOut size={15} /> Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-4 md:p-8 max-w-6xl mx-auto w-full">
        <div className="md:hidden flex items-center justify-between mb-4">
          <Link to="/" className="flex items-center gap-2 font-bold"><Shield className="text-cyan-400" /> QUANTUMSHIELD X</Link>
          <button onClick={logout} className="btn btn-secondary">Log out</button>
        </div>
        {children}
        <footer className="mt-12 text-xs text-slate-500">
          Demonstration platform for standardised post-quantum cryptography (FIPS 203 / 204 / 205).
          Not claimed to be quantum-proof or independently security-certified.
        </footer>
      </main>
    </div>
  );
}
