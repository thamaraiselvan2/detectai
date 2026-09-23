import React, { useState } from 'react';
import { 
  Shield, 
  Search, 
  Fingerprint, 
  Home,
  Radio,
  Box,
  ScanLine,
  Users,
  BarChart3,
  Menu,
  X
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const primaryItems = [
    { id: 'home',     label: 'Home',          icon: Home },
    { id: 'search',   label: 'Instant Search', icon: Search },
    { id: 'register', label: 'Register',       icon: Fingerprint },
  ];

  const secondaryItems = [
    { id: 'monitoring', label: 'Monitoring',  icon: Radio },
    { id: 'sandbox',    label: 'Sandbox',     icon: Box },
    { id: 'scanner',    label: 'Scanner',     icon: ScanLine },
    { id: 'protected',  label: 'Protected',   icon: Users },
    { id: 'admin',      label: 'Admin',       icon: BarChart3 },
  ];

  const allItems = [...primaryItems, ...secondaryItems];

  const btnClass = (isActive) =>
    `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer ${
      isActive
        ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan font-semibold'
        : 'text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent'
    }`;

  return (
    <header className="sticky top-0 z-50 bg-slate-950/85 border-b border-slate-800/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <div 
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => setActiveTab('home')}
          >
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 shadow-glow-cyan">
              <Shield className="w-5 h-5 text-slate-950 stroke-[2.5]" />
              <div className="absolute -inset-0.5 bg-cyan-400 rounded-xl blur opacity-30 group-hover:opacity-60 transition duration-300 pointer-events-none" />
            </div>
            <div>
              <span className="font-mono font-extrabold text-base sm:text-lg tracking-wider text-white">
                FAKE PROFILE <span className="text-cyan-400">DETECTOR</span>
              </span>
              <p className="text-[10px] text-slate-400 font-mono tracking-tight hidden sm:block">
                Identity Verification &amp; Impersonation Defense
              </p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1">
            {primaryItems.map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setActiveTab(id)} className={btnClass(activeTab === id)}>
                <Icon className={`w-4 h-4 ${activeTab === id ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{label}</span>
              </button>
            ))}
            <div className="w-px h-6 bg-slate-700/60 mx-2" />
            {secondaryItems.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                title={label}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer ${
                  activeTab === id
                    ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${activeTab === id ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span className="hidden xl:inline">{label}</span>
              </button>
            ))}
          </nav>

          {/* Right: Status pill + mobile toggle */}
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-mono text-slate-300">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span>SYSTEM READY</span>
            </div>
            <button
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              onClick={() => setMobileOpen(p => !p)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="lg:hidden border-t border-slate-800/60 py-3 grid grid-cols-2 gap-1.5 sm:grid-cols-3">
            {allItems.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => { setActiveTab(id); setMobileOpen(false); }}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
                  activeTab === id
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}
