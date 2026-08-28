import React from 'react';
import { getRiskMeta } from '../utils/riskHelpers';
import { AlertTriangle, CheckCircle2, ShieldAlert, ShieldX } from 'lucide-react';

export default function RiskGauge({ score = 0, level = 'LOW', size = 200 }) {
  const meta = getRiskMeta(level, score);
  
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  // Score percentage from 0 to 100
  const progress = Math.min(Math.max(score, 0), 100);
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const getRiskIcon = () => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return <ShieldX className="w-6 h-6 text-red-400 animate-bounce" />;
      case 'HIGH':
        return <ShieldAlert className="w-6 h-6 text-orange-400" />;
      case 'MEDIUM':
        return <AlertTriangle className="w-6 h-6 text-amber-400" />;
      case 'LOW':
      default:
        return <CheckCircle2 className="w-6 h-6 text-emerald-400" />;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        {/* Outer Glow Halo */}
        <div 
          className="absolute inset-4 rounded-full blur-xl opacity-30 transition-all duration-700"
          style={{ backgroundColor: meta.color }}
        />

        {/* SVG Radial Gauge */}
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 180 180">
          {/* Background Track */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke="#1e293b"
            strokeWidth="12"
            fill="transparent"
            strokeDasharray="4 4"
          />
          {/* Active Progress Arc */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke={meta.color}
            strokeWidth="12"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Inner Content Badge */}
        <div className="absolute flex flex-col items-center justify-center text-center">
          <div className="flex items-baseline gap-0.5">
            <span className="text-4xl sm:text-5xl font-mono font-extrabold tracking-tight text-white">
              {score}
            </span>
            <span className="text-sm font-mono text-slate-400">/100</span>
          </div>
          <span className="text-[11px] font-mono uppercase tracking-widest text-slate-400 mt-0.5">
            RISK SCORE
          </span>
        </div>
      </div>

      {/* Risk Tier Badge */}
      <div className={`mt-3 flex items-center gap-2 px-4 py-1.5 rounded-full border text-xs font-mono font-bold uppercase tracking-wider ${meta.badgeBg}`}>
        {getRiskIcon()}
        <span>{level} RISK LEVEL</span>
      </div>
    </div>
  );
}
