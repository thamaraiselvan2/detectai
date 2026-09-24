import React, { useState } from 'react';
import Navbar from './components/Navbar';
import SecuritySplash from './components/SecuritySplash';
import HomePage from './pages/HomePage';
import InstantSearchPage from './pages/InstantSearchPage';
import RegisterPage from './pages/RegisterPage';
import MonitoringPage from './pages/MonitoringPage';
import SandboxPage from './pages/SandboxPage';
import ScannerPage from './pages/ScannerPage';
import AdminDashboard from './pages/AdminDashboard';
import ProtectedPage from './pages/ProtectedPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [toast, setToast] = useState(null);
  const [scannerTarget, setScannerTarget] = useState(null);

  const showToast = (notification, type = 'info') => {
    const nextToast = typeof notification === 'object'
      ? notification
      : { message: notification, type };

    setToast({
      message: nextToast.message || '',
      type: nextToast.type || 'info'
    });
    setTimeout(() => setToast(null), 3500);
  };

  const scanTarget = (target) => {
    setScannerTarget(target);
    setActiveTab('scanner');
  };

  return (
    <>
      <SecuritySplash />
      <div className="min-h-screen bg-cyber-bg text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
        {/* Dynamic Cyber Grid Background */}
        <div className="fixed inset-0 cyber-grid opacity-35 pointer-events-none z-0" />

        {/* Main Sticky Navbar */}
        <div className="relative z-20">
          <Navbar 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
          />
        </div>

        {/* Global Toast Notification */}
        {toast && (
          <div className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl shadow-xl text-sm font-mono font-semibold border transition-all animate-in slide-in-from-bottom-4 fade-in duration-300 ${
            toast.type === 'success' ? 'bg-emerald-900/90 border-emerald-500/50 text-emerald-200' :
            toast.type === 'error'   ? 'bg-red-900/90 border-red-500/50 text-red-200' :
            'bg-slate-800/90 border-cyan-500/40 text-cyan-200'
          }`}>
            {toast.message}
          </div>
        )}

        {/* Main Content Body */}
        <main className="relative z-10 flex-1 flex flex-col">
          {activeTab === 'home'       && <HomePage onNavigate={(tab) => setActiveTab(tab)} />}
          {activeTab === 'search'     && <InstantSearchPage onBackToHome={() => setActiveTab('home')} />}
          {activeTab === 'register'   && <RegisterPage onBackToHome={() => setActiveTab('home')} />}
          {activeTab === 'monitoring' && <MonitoringPage onToast={showToast} />}
          {activeTab === 'sandbox'    && <SandboxPage onScanTarget={scanTarget} onToast={showToast} />}
          {activeTab === 'scanner'    && <ScannerPage initialTarget={scannerTarget} onToast={showToast} />}
          {activeTab === 'protected'  && <ProtectedPage onNavigateToMonitoring={() => setActiveTab('monitoring')} onToast={showToast} />}
          {activeTab === 'admin'      && <AdminDashboard onToast={showToast} />}
        </main>

        {/* Security Product Footer */}
        <footer className="relative z-10 border-t border-slate-800/80 bg-slate-950/80 py-5 text-center text-xs font-mono text-slate-400">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p>© 2026 FAKE PROFILE DETECTOR • Identity Protection System</p>
            <p className="text-[11px] text-slate-400">
              Cybersecurity Verification &amp; Profile Similarity Analysis
            </p>
          </div>
        </footer>
      </div>
    </>
  );
}
