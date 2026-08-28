import React from 'react';
import { 
  Shield, 
  ShieldCheck, 
  Search, 
  UserPlus, 
  Fingerprint, 
  Lock, 
  CheckCircle2, 
  ArrowRight, 
  Activity, 
  Cpu, 
  FileCheck
} from 'lucide-react';

export default function HomePage({ onNavigate }) {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex flex-col justify-between overflow-hidden">
      {/* Cybersecurity Animated Graphic Elements */}
      <div className="absolute inset-0 pointer-events-none z-0">
        {/* Subtle Ambient Radial Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-blue-600/10 rounded-full blur-[100px]" />
        <div className="absolute top-10 left-10 w-[350px] h-[350px] bg-indigo-600/10 rounded-full blur-[100px]" />

        {/* Cybersecurity Hex / Network Grid Accents */}
        <svg className="absolute inset-0 w-full h-full opacity-15 stroke-cyan-500/30" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="cyber-net" width="80" height="80" patternUnits="userSpaceOnUse">
              <path d="M 80 0 L 0 0 0 80" fill="none" strokeWidth="0.75" />
              <circle cx="80" cy="0" r="1.5" fill="currentColor" />
              <circle cx="0" cy="80" r="1.5" fill="currentColor" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#cyber-net)" />
        </svg>
      </div>

      {/* Main Content Area */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-16 flex-1 flex flex-col items-center justify-center text-center">
        
        {/* Security Telemetry Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono mb-8 backdrop-blur-md shadow-glow-cyan animate-in fade-in slide-in-from-top-4 duration-500">
          <Shield className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-semibold tracking-wider uppercase">CYBERSECURITY IDENTITY VERIFICATION</span>
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
        </div>

        {/* Main Heading */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white mb-6 font-sans">
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-cyan-200">
            FAKE PROFILE DETECTOR
          </span>
        </h1>

        {/* Short Description */}
        <p className="max-w-2xl text-base sm:text-lg md:text-xl text-slate-300 mb-12 font-normal leading-relaxed">
          Detect potentially fake and impersonating profiles using profile analysis and similarity detection.
        </p>

        {/* Two Main Option Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 w-full max-w-4xl">
          
          {/* OPTION 1: INSTANT SEARCH */}
          <div className="group relative bg-slate-900/80 hover:bg-slate-900/95 border border-slate-800 hover:border-cyan-500/60 rounded-2xl p-7 sm:p-8 text-left transition-all duration-300 hover:shadow-glow-cyan flex flex-col justify-between backdrop-blur-md">
            <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-xl group-hover:bg-cyan-500/10 transition duration-300 pointer-events-none" />

            <div>
              <div className="w-14 h-14 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-6 group-hover:scale-105 transition-transform duration-300 shadow-sm">
                <Search className="w-7 h-7 stroke-[2.2]" />
              </div>

              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">Option 1</span>
              </div>

              <h2 className="text-2xl font-bold text-white mb-3 tracking-tight font-sans group-hover:text-cyan-300 transition-colors">
                INSTANT SEARCH
              </h2>

              <p className="text-slate-400 text-sm leading-relaxed mb-6">
                Check whether a username appears to be real or potentially fake using our demo profile data.
              </p>

              <div className="space-y-2 mb-6 text-xs text-slate-400 font-mono">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Demo database verification</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Impersonation &amp; risk factors</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => onNavigate('search')}
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm tracking-wide transition-all shadow-md hover:shadow-cyan-500/30 flex items-center justify-center gap-2 cursor-pointer group-hover:translate-y-[-1px]"
            >
              <span>Instant Search</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* OPTION 2: REGISTER & PROTECT */}
          <div className="group relative bg-slate-900/80 hover:bg-slate-900/95 border border-slate-800 hover:border-emerald-500/60 rounded-2xl p-7 sm:p-8 text-left transition-all duration-300 hover:shadow-glow-green flex flex-col justify-between backdrop-blur-md">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-xl group-hover:bg-emerald-500/10 transition duration-300 pointer-events-none" />

            <div>
              <div className="w-14 h-14 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-6 group-hover:scale-105 transition-transform duration-300 shadow-sm">
                <Fingerprint className="w-7 h-7 stroke-[2.2]" />
              </div>

              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">Option 2</span>
              </div>

              <h2 className="text-2xl font-bold text-white mb-3 tracking-tight font-sans group-hover:text-emerald-300 transition-colors">
                REGISTER &amp; PROTECT
              </h2>

              <p className="text-slate-400 text-sm leading-relaxed mb-6">
                Register your username and email to protect your profile.
              </p>

              <div className="space-y-2 mb-6 text-xs text-slate-400 font-mono">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Register genuine username &amp; email</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Identity vault protection</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => onNavigate('register')}
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm tracking-wide transition-all shadow-md hover:shadow-emerald-500/30 flex items-center justify-center gap-2 cursor-pointer group-hover:translate-y-[-1px]"
            >
              <span>Register</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

        </div>

        {/* Security Pillars Bar */}
        <div className="mt-14 pt-8 border-t border-slate-800/80 w-full max-w-4xl grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-slate-400 text-xs font-mono">
          <div className="flex items-center justify-center gap-2 py-1">
            <Lock className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>Identity Shield</span>
          </div>
          <div className="flex items-center justify-center gap-2 py-1">
            <Cpu className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>Similarity Analysis</span>
          </div>
          <div className="flex items-center justify-center gap-2 py-1">
            <FileCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Demo Data Verification</span>
          </div>
          <div className="flex items-center justify-center gap-2 py-1">
            <Activity className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Zero Tracking</span>
          </div>
        </div>

      </div>
    </div>
  );
}
