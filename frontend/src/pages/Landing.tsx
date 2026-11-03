import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, KeyRound, MessagesSquare, FileLock, PenLine, Atom, BarChart3, ScrollText, ArrowRight } from 'lucide-react';

const FEATURES = [
  { icon: KeyRound, title: 'ML-KEM Key Encapsulation', text: 'FIPS 203 key generation, encapsulation and decapsulation — ML-KEM-512, 768 and 1024, running on audited liboqs.' },
  { icon: PenLine, title: 'ML-DSA & SLH-DSA Signatures', text: 'FIPS 204 and FIPS 205 digital signatures with real verification and tamper detection.' },
  { icon: MessagesSquare, title: 'Secure Messaging', text: 'User-to-user messages with ML-KEM key establishment, AES-256-GCM encryption and ML-DSA signatures. Stored as ciphertext only.' },
  { icon: FileLock, title: 'File Encryption', text: 'Upload, encrypt with an ML-KEM-wrapped file key, hash, sign and verify integrity — up to 10 MB.' },
  { icon: Atom, title: 'Quantum Threat Simulator', text: 'Shor and Grover explained as educational models, plus a Harvest Now, Decrypt Later estimator.' },
  { icon: BarChart3, title: 'Live Benchmarks', text: 'Algorithm comparison measured live on the server at request time — never hardcoded numbers.' },
  { icon: ScrollText, title: 'Hash-Chained Audit Log', text: 'Every action chained by hash, with a one-click chain verification endpoint.' },
];

export default function Landing() {
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-6 md:px-12 py-5">
        <span className="flex items-center gap-2 font-bold text-lg"><Shield className="text-cyan-400" /> QUANTUMSHIELD <span className="text-cyan-400">X</span></span>
        <div className="flex gap-3">
          <Link to="/learn" className="btn btn-secondary">Learn</Link>
          <Link to="/auth" className="btn">Open platform <ArrowRight size={16} /></Link>
        </div>
      </header>

      <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="px-6 md:px-12 pt-16 pb-12 text-center">
        <p className="text-cyan-300 tracking-widest text-xs uppercase">Post-Quantum Cryptography · FIPS 203 / 204 / 205</p>
        <h1 className="text-4xl md:text-6xl font-extrabold mt-4 leading-tight">
          Security that survives<br />
          <span className="bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">the quantum era.</span>
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto mt-5">
          QUANTUMSHIELD X is a working post-quantum cryptography platform: real ML-KEM, ML-DSA and
          SLH-DSA implementations, secure messaging, file encryption, and a live security dashboard —
          built for research, demonstration and hackathon presentation.
        </p>
        <div className="flex gap-3 justify-center mt-8">
          <Link to="/auth" className="btn">Launch the lab <ArrowRight size={16} /></Link>
          <Link to="/docs" className="btn btn-secondary">Read the docs</Link>
        </div>
        <p className="text-xs text-slate-500 mt-6">Demo logins: user / demo123 · admin / admin123 (demo-only accounts)</p>
      </motion.section>

      <section className="px-6 md:px-12 pb-20 grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-6xl mx-auto">
        {FEATURES.map((f) => {
          const Icon = f.icon;
          return (
            <div key={f.title} className="glass p-5">
              <Icon className="text-cyan-400" size={22} />
              <h3 className="font-semibold mt-3">{f.title}</h3>
              <p className="text-sm text-slate-400 mt-1">{f.text}</p>
            </div>
          );
        })}
        <div className="glass p-5">
          <Shield className="text-cyan-400" size={22} />
          <h3 className="font-semibold mt-3">Honest by design</h3>
          <p className="text-sm text-slate-400 mt-1">
            Private keys are never stored server-side. Dashboard numbers come only from the database.
            Simulations are labelled as educational models. Nothing here claims to be quantum-proof
            or independently certified.
          </p>
        </div>
      </section>
    </div>
  );
}
