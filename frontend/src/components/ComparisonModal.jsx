import React from 'react';
import { X, ShieldCheck, AlertTriangle, ArrowRight, BadgeCheck, Users, Mail } from 'lucide-react';
import { formatNumber } from '../utils/riskHelpers';

export default function ComparisonModal({ isOpen, onClose, targetProfile, matchedProtected }) {
  if (!isOpen || !matchedProtected) return null;

  const defaultAvatar = (name) => `https://ui-avatars.com/api/?name=${encodeURIComponent(name || 'User')}&background=0d1527&color=00f0ff`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-3xl rounded-2xl glass-panel-glow bg-slate-950 border border-slate-700 p-6 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white font-mono">
                Identity Impersonation Analysis
              </h3>
              <p className="text-xs text-slate-400">
                Side-by-side contrast between scanned profile and authentic protected registry
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Side-by-Side Comparison Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {/* Authentic Identity Column */}
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono font-bold uppercase mb-3">
              <ShieldCheck className="w-4 h-4" />
              <span>Genuine Protected Identity</span>
            </div>

            <div className="flex items-center gap-3">
              <img
                src={matchedProtected.avatar_url || defaultAvatar(matchedProtected.display_name)}
                alt={matchedProtected.display_name}
                className="w-12 h-12 rounded-xl object-cover border border-emerald-500/50"
              />
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-white text-sm">{matchedProtected.display_name}</span>
                  <BadgeCheck className="w-4 h-4 text-cyan-400" />
                </div>
                <p className="text-xs font-mono text-emerald-400">@{matchedProtected.username}</p>
                {matchedProtected.email && (
                  <p className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                    <Mail className="w-3 h-3 text-slate-500" />
                    <span>{matchedProtected.email}</span>
                  </p>
                )}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-emerald-900/40 text-xs text-slate-300">
              <p className="font-mono text-[10px] uppercase text-emerald-400/80 mb-1">Registered Bio:</p>
              <p className="italic">{matchedProtected.bio || 'Official bio on record'}</p>
            </div>
          </div>

          {/* Scanned Candidate Column */}
          <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30">
            <div className="flex items-center gap-2 text-red-400 text-xs font-mono font-bold uppercase mb-3">
              <AlertTriangle className="w-4 h-4" />
              <span>Scanned Target Candidate</span>
            </div>

            <div className="flex items-center gap-3">
              <img
                src={targetProfile?.avatar_url || defaultAvatar(targetProfile?.display_name)}
                alt={targetProfile?.display_name}
                className="w-12 h-12 rounded-xl object-cover border border-red-500/50"
              />
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-white text-sm">{targetProfile?.display_name}</span>
                  {Boolean(targetProfile?.is_verified) ? (
                    <BadgeCheck className="w-4 h-4 text-cyan-400" />
                  ) : (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">Unverified</span>
                  )}
                </div>
                <p className="text-xs font-mono text-red-400">@{targetProfile?.username}</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Followers: <span className="font-mono font-bold text-white">{formatNumber(targetProfile?.followers_count || 0)}</span> | Following: <span className="font-mono font-bold text-white">{formatNumber(targetProfile?.following_count || 0)}</span>
                </p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-red-900/40 text-xs text-slate-300">
              <p className="font-mono text-[10px] uppercase text-red-400/80 mb-1">Scanned Profile Bio:</p>
              <p className="italic">{targetProfile?.bio || 'No bio provided'}</p>
            </div>
          </div>
        </div>

        {/* Impersonation Reasons List */}
        {matchedProtected.reasons && matchedProtected.reasons.length > 0 && (
          <div className="mt-5 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
            <h4 className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider mb-2">
              Detected Similarity Vectors:
            </h4>
            <ul className="space-y-1.5">
              {matchedProtected.reasons.map((r, i) => (
                <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-red-400 font-bold">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Close Action */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-mono text-xs font-semibold transition"
          >
            Dismiss Comparison
          </button>
        </div>
      </div>
    </div>
  );
}
