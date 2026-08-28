export const getRiskMeta = (level, score) => {
  switch (level?.toUpperCase()) {
    case 'CRITICAL':
      return {
        level: 'CRITICAL',
        color: '#ef4444',
        bgColor: 'bg-red-500/10',
        textColor: 'text-red-400',
        borderColor: 'border-red-500/30',
        badgeBg: 'bg-red-500/20 text-red-300 border-red-500/40',
        glowClass: 'shadow-glow-red',
        description: 'Severe Impersonation / Malicious Phishing Risk'
      };
    case 'HIGH':
      return {
        level: 'HIGH',
        color: '#f97316',
        bgColor: 'bg-orange-500/10',
        textColor: 'text-orange-400',
        borderColor: 'border-orange-500/30',
        badgeBg: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
        glowClass: 'shadow-glow-amber',
        description: 'Substantial Identity Mimicry / High Risk'
      };
    case 'MEDIUM':
      return {
        level: 'MEDIUM',
        color: '#f59e0b',
        bgColor: 'bg-amber-500/10',
        textColor: 'text-amber-400',
        borderColor: 'border-amber-500/30',
        badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
        glowClass: 'shadow-glow-amber',
        description: 'Moderate Suspicious Indicators'
      };
    case 'LOW':
    default:
      return {
        level: 'LOW',
        color: '#10b981',
        bgColor: 'bg-emerald-500/10',
        textColor: 'text-emerald-400',
        borderColor: 'border-emerald-500/30',
        badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
        glowClass: 'shadow-glow-green',
        description: 'Authentic / Low Risk Profile'
      };
  }
};

export const formatNumber = (num) => {
  if (num === null || num === undefined) return '0';
  if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
  return num.toLocaleString();
};

export const formatTimeAgo = (dateString) => {
  if (!dateString) return 'Just now';
  const date = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return `${diffSec || 1}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
};
