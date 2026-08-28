import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export default function QuickToast({ toast, onClose }) {
  if (!toast) return null;

  const getIcon = () => {
    switch (toast.type) {
      case 'error':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'info':
        return <Info className="w-5 h-5 text-cyan-400" />;
      case 'success':
      default:
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-slideUp">
      <div className="flex items-center gap-3 p-4 rounded-xl glass-panel-glow border border-slate-700 bg-slate-900/95 text-white shadow-2xl max-w-md">
        {getIcon()}
        <div className="flex-1">
          <p className="text-xs font-mono font-bold text-white">{toast.title || 'System Notification'}</p>
          <p className="text-xs text-slate-300 mt-0.5">{toast.message}</p>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
