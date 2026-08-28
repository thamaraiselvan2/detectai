import React from 'react';
import { ShieldCheck, CheckCircle2, X } from 'lucide-react';

export default function SuccessModal({ isOpen, onClose, username, email }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-slate-900 border border-cyan-500/40 rounded-2xl p-6 shadow-glow-cyan text-slate-100 overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute -right-12 -top-12 w-36 h-36 bg-cyan-500/15 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -left-12 -bottom-12 w-36 h-36 bg-emerald-500/15 rounded-full blur-2xl pointer-events-none" />

        {/* Close Icon Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition p-1.5 rounded-lg hover:bg-slate-800"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Content */}
        <div className="flex flex-col items-center text-center pt-2 pb-4">
          <div className="relative mb-4">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-emerald-400 shadow-glow-green">
              <ShieldCheck className="w-8 h-8 stroke-[2.2]" />
            </div>
            <div className="absolute -bottom-1 -right-1 bg-emerald-500 text-slate-950 p-1 rounded-full">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>

          <h3 className="text-xl font-bold text-white tracking-wide mb-2 font-mono">
            Registered Successfully
          </h3>
          
          <p className="text-sm text-slate-300 mb-6 leading-relaxed">
            Your profile has been successfully registered. Your identity is now recorded in the protection registry.
          </p>

          {username && (
            <div className="w-full bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 mb-6 text-left font-mono text-xs space-y-1.5">
              <div className="flex justify-between items-center text-slate-400">
                <span>Protected Handle:</span>
                <span className="text-cyan-400 font-semibold">@{username.replace(/^@/, '')}</span>
              </div>
              {email && (
                <div className="flex justify-between items-center text-slate-400">
                  <span>Registered Email:</span>
                  <span className="text-slate-200">{email}</span>
                </div>
              )}
              <div className="flex justify-between items-center text-slate-400 pt-1 border-t border-slate-800/80">
                <span>Status:</span>
                <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Active &amp; Protected
                </span>
              </div>
            </div>
          )}

          {/* OK / Close Button */}
          <button
            onClick={onClose}
            className="w-full py-3 px-6 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm tracking-wide transition-all shadow-lg hover:shadow-cyan-500/25 active:scale-[0.99] cursor-pointer"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
