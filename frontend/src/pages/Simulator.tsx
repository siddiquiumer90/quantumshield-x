import { useEffect, useState } from 'react';
import { api } from '../api';

type Sim = {
  label: string;
  comparison: { algorithm: string; classical_security_bits: number; quantum_vulnerable: boolean; attack: string; pqc_replacement: string }[];
  shor: { title: string; idea: string; why_rsa_breaks: string; why_ecc_breaks: string; label: string };
  grover: { title: string; idea: string; label: string };
  hndl_note: string;
};

export default function Simulator() {
  const [s, setS] = useState<Sim | null>(null);
  const [error, setError] = useState('');
  // HNDL estimator state
  const [hAlg, setHAlg] = useState('RSA-2048');
  const [sec, setSec] = useState(20);
  const [mig, setMig] = useState(5);
  const [thr, setThr] = useState(10);
  const [hndl, setHndl] = useState<Record<string, unknown> | null>(null);

  useEffect(() => { api<Sim>('/api/simulator').then(setS).catch((e) => setError(e.message)); }, []);

  async function estimate() {
    setError('');
    try {
      const r = await api('/api/hndl', { method: 'POST', body: JSON.stringify({ algorithm: hAlg, secrecy_years: sec, migration_years: mig, threat_years_estimate: thr }) });
      setHndl(r as Record<string, unknown>);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
  }

  if (error) return <div className="err">{error}</div>;
  if (!s) return <p className="text-slate-400">Loading simulator…</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Quantum Threat Simulator</h1>
      <div className="warn mb-4">{s.label}</div>

      <div className="glass p-5 mb-4">
        <h2 className="font-semibold mb-3">Classical vs quantum comparison</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-400"><th>Algorithm</th><th>Classical bits</th><th>Quantum risk</th><th>PQC replacement</th></tr></thead>
          <tbody>
            {s.comparison.map((c) => (
              <tr key={c.algorithm} className="border-t border-white/5">
                <td className="py-2 font-semibold">{c.algorithm}</td>
                <td>{c.classical_security_bits}</td>
                <td>{c.quantum_vulnerable ? <span className="text-red-400">Vulnerable — {c.attack}</span> : <span className="text-emerald-400">{c.attack}</span>}</td>
                <td className="text-slate-300">{c.pqc_replacement}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-4">
        <div className="glass p-5">
          <h2 className="font-semibold mb-2">{s.shor.title}</h2>
          <p className="text-sm text-slate-300">{s.shor.idea}</p>
          <p className="text-sm text-slate-300 mt-2"><b>RSA:</b> {s.shor.why_rsa_breaks}</p>
          <p className="text-sm text-slate-300 mt-2"><b>ECC:</b> {s.shor.why_ecc_breaks}</p>
        </div>
        <div className="glass p-5">
          <h2 className="font-semibold mb-2">{s.grover.title}</h2>
          <p className="text-sm text-slate-300">{s.grover.idea}</p>
          <p className="text-sm text-slate-300 mt-2"><b>Harvest Now, Decrypt Later:</b> {s.hndl_note}</p>
        </div>
      </div>

      <div className="glass p-5">
        <h2 className="font-semibold mb-3">Harvest Now, Decrypt Later estimator — Mosca X+Y&gt;Z</h2>
        <p className="text-xs text-slate-500 mb-3">{s.label} Z is your assumption, not a prediction — change it to test sensitivity.</p>
        <div className="grid sm:grid-cols-4 gap-3 mb-3">
          <div><label className="label">Algorithm</label>
            <select className="input" value={hAlg} onChange={(e) => setHAlg(e.target.value)}>
              <option>RSA-2048</option><option>ECC-P-256</option><option>ML-KEM-768</option><option>AES-256-GCM</option>
            </select></div>
          <div><label className="label">Secrecy years (X)</label>
            <input className="input" type="number" value={sec} onChange={(e) => setSec(Number(e.target.value))} /></div>
          <div><label className="label">Migration years (Y)</label>
            <input className="input" type="number" value={mig} onChange={(e) => setMig(Number(e.target.value))} /></div>
          <div><label className="label">Threat estimate years (Z)</label>
            <input className="input" type="number" value={thr} onChange={(e) => setThr(Number(e.target.value))} /></div>
        </div>
        <button className="btn" onClick={estimate}>Estimate exposure</button>
        {hndl && <div className="mt-3">
          <p className="text-sm">X+Y = {String(hndl['x_plus_y'])} vs Z = {String(hndl['z_threat_years_estimate'])} → exposure: <b>{String(hndl['exposure_level'])}</b>, at risk: <b>{String(hndl['at_risk'])}</b></p>
          <p className="text-sm text-slate-300 mt-1">{String(hndl['verdict'])}</p>
        </div>}
      </div>
    </div>
  );
}
