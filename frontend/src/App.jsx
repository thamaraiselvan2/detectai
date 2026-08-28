import React, { useState } from 'react';
import Navbar from './components/Navbar';
import SecuritySplash from './components/SecuritySplash';
import HomePage from './pages/HomePage';
import InstantSearchPage from './pages/InstantSearchPage';
import RegisterPage from './pages/RegisterPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');

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

        {/* Main Content Body */}
        <main className="relative z-10 flex-1 flex flex-col">
          {activeTab === 'home' && (
            <HomePage onNavigate={(tab) => setActiveTab(tab)} />
          )}
          
          {activeTab === 'search' && (
            <InstantSearchPage onBackToHome={() => setActiveTab('home')} />
          )}
          
          {activeTab === 'register' && (
            <RegisterPage onBackToHome={() => setActiveTab('home')} />
          )}
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
