import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import { getToken } from './api';
import Landing from './pages/Landing';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import CryptoLab from './pages/CryptoLab';
import Messaging from './pages/Messaging';
import FileSecurity from './pages/FileSecurity';
import SignatureLab from './pages/SignatureLab';
import Simulator from './pages/Simulator';
import Compare from './pages/Compare';
import KeyManagement from './pages/KeyManagement';
import AuditLogs from './pages/AuditLogs';
import LearningCenter from './pages/LearningCenter';
import Documentation from './pages/Documentation';
import Profile from './pages/Profile';
import Admin from './pages/Admin';

function Guard({ children }: { children: React.ReactNode }) {
  if (!getToken()) return <Navigate to="/auth" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={<Auth />} />
      <Route path="/dashboard" element={<Guard><Dashboard /></Guard>} />
      <Route path="/lab" element={<Guard><CryptoLab /></Guard>} />
      <Route path="/messages" element={<Guard><Messaging /></Guard>} />
      <Route path="/files" element={<Guard><FileSecurity /></Guard>} />
      <Route path="/signatures" element={<Guard><SignatureLab /></Guard>} />
      <Route path="/simulator" element={<Guard><Simulator /></Guard>} />
      <Route path="/compare" element={<Guard><Compare /></Guard>} />
      <Route path="/keys" element={<Guard><KeyManagement /></Guard>} />
      <Route path="/audit" element={<Guard><AuditLogs /></Guard>} />
      <Route path="/learn" element={<Guard><LearningCenter /></Guard>} />
      <Route path="/docs" element={<Guard><Documentation /></Guard>} />
      <Route path="/profile" element={<Guard><Profile /></Guard>} />
      <Route path="/admin" element={<Guard><Admin /></Guard>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
