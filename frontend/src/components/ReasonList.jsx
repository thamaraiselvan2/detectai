import React from 'react';
import { 
  AlertCircle, 
  Users, 
  FileText, 
  Hash, 
  ShieldCheck, 
  Flame, 
  Info 
} from 'lucide-react';

export default function ReasonList({ factors = [] }) {
  const getCategoryIcon = (category) => {
    switch (category?.toLowerCase()) {
      case 'identity impersonation & typosquatting':
        return <Flame className="w-4 h-4 text-red-400" />;
      case 'behavioral & engagement':
        return <Users className="w-4 h-4 text-amber-400" />;
      case 'bio & phishing indicators':
        return <FileText className="w-4 h-4 text-orange-400" />;
      case 'username patterns':
        return <Hash className="w-4 h-4 text-cyan-400" />;
      default:
        return <Info className="w-4 h-4 text-emerald-400" />;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'high':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'medium':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'low':
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    }
  };

  if (!factors || factors.length === 0) {
    return (
      <div className="p-4 rounded-xl glass-panel border border-slate-800 text-center text-slate-400 text-sm">
        No specific risk factors triggered. Profile appears authentic.
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {factors.map((factor, index) => (
        <div
          key={index}
          className="p-3.5 rounded-xl glass-panel border border-slate-800/90 hover:border-slate-700 transition-all duration-200 flex items-start justify-between gap-3"
        >
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800 mt-0.5 flex-shrink-0">
              {getCategoryIcon(factor.category)}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono font-semibold text-slate-300">
                  {factor.category}
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${getSeverityBadge(factor.severity)}`}>
                  {factor.severity}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {factor.description}
              </p>
            </div>
          </div>

          <div className="flex-shrink-0">
            <span className={`text-xs font-mono font-bold px-2 py-1 rounded-md ${
              factor.points > 0 
                ? 'bg-red-500/10 text-red-400 border border-red-500/20' 
                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            }`}>
              {factor.points > 0 ? `+${factor.points}` : '0'} pts
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
