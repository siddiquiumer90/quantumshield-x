import { useState } from 'react';

const TOPICS = [
  { t: 'What is cryptography?', b: 'Cryptography is the practice of protecting information so only intended recipients can read it. It gives us confidentiality (encryption), integrity (hashes and authenticated encryption), and authenticity (digital signatures).' },
  { t: 'What is quantum computing?', b: 'A quantum computer uses qubits, which can exist in superposition and be entangled. For a few specific problems — factoring and discrete logarithms — quantum algorithms are exponentially faster than classical ones. That is the whole threat in one sentence.' },
  { t: 'What is Post-Quantum Cryptography (PQC)?', b: 'PQC is classical cryptography (running on ordinary computers) designed to resist quantum attacks. It does not need a quantum computer to work — it is new maths that Shor’s algorithm cannot break. NIST standardised ML-KEM (FIPS 203), ML-DSA (FIPS 204) and SLH-DSA (FIPS 205).' },
  { t: 'RSA vs ECC vs PQC', b: 'RSA relies on factoring; ECC relies on discrete logarithms. Both fall to Shor’s algorithm. ML-KEM relies on lattice problems (Module-LWE); ML-DSA also on lattices; SLH-DSA relies only on hash functions. The price of PQC is larger keys and signatures.' },
  { t: 'ML-KEM explained', b: 'ML-KEM is a Key Encapsulation Mechanism: the sender uses your public key to produce a ciphertext and a shared secret; only your private key can decapsulate the same secret. That secret then keys AES-256-GCM for the actual data.' },
  { t: 'ML-DSA explained', b: 'ML-DSA is a lattice-based digital signature scheme. Sign with the private key, verify with the public key. Anyone can verify; only the key holder can sign. Tampering with the message or the signature makes verification fail.' },
  { t: 'SLH-DSA explained', b: 'SLH-DSA is hash-based: its security rests only on the strength of hash functions, not on lattices. It is stateless (no state to manage like older hash signatures) but has larger signatures and slower signing than ML-DSA.' },
  { t: "Shor's algorithm", b: 'Shor’s algorithm factors integers and solves discrete logarithms in polynomial time on a quantum computer, using period-finding via the quantum Fourier transform. That is why RSA and ECC must be replaced for long-lived secrets.' },
  { t: "Grover's algorithm", b: 'Grover’s algorithm gives only a quadratic speedup for searching: AES-256 drops to ~128-bit effective strength, AES-128 to ~64-bit. The fix is simple — use AES-256, not new algorithms.' },
  { t: 'Harvest Now, Decrypt Later', b: 'An attacker records encrypted traffic today and decrypts it years later when a quantum computer exists. Data that must stay secret for decades (medical, state, research) is already at risk if it is protected only by RSA/ECC today. Try the estimator on the Quantum Simulator page.' },
  { t: 'Quantum-safe migration strategies', b: '1) Inventory every system and its algorithms. 2) Protect long-secrecy data first. 3) Use hybrid modes (classical + PQC) during transition so a break of either side alone does not expose you. 4) Build crypto-agility — the ability to swap algorithms without rewriting the system.' },
  { t: 'Hybrid cryptography', b: 'Hybrid means combining a classical algorithm (X25519) with a post-quantum one (ML-KEM) and deriving one key from both secrets. The security assumption is explicit: the result is secure if EITHER component holds.' },
];

export default function LearningCenter() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Learning Center</h1>
      <p className="text-sm text-slate-400 mb-6">Short, plain explanations of every concept this platform demonstrates. Tap a topic to expand it.</p>
      <div className="space-y-3">
        {TOPICS.map((x, i) => (
          <div key={x.t} className="glass p-5">
            <button className="font-semibold text-left w-full" onClick={() => setOpen(open === i ? null : i)}>
              {i + 1}. {x.t} <span className="text-cyan-400 float-right">{open === i ? '−' : '+'}</span>
            </button>
            {open === i && <p className="text-sm text-slate-300 mt-2">{x.b}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
