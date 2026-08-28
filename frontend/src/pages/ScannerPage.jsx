import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Sparkles, 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  Users, 
  History, 
  RefreshCw, 
  ExternalLink,
  Sliders,
  ChevronRight,
  Info,
  CheckCircle2
} from 'lucide-react';
import RiskGauge from '../components/RiskGauge';
import ReasonList from '../components/ReasonList';
import ComparisonModal from '../components/ComparisonModal';
import { checkProfile, getCheckHistory, getDemoProfiles } from '../api/client';
import { formatNumber, formatTimeAgo, getRiskMeta } from '../utils/riskHelpers';

export default function ScannerPage({ onToast, initialTarget }) {
  const [usernameInput, setUsernameInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [demoProfiles, setDemoProfiles] = useState([]);
  const [history, setHistory] = useState([]);
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);

  // Custom Profile Form state
  const [customForm, setCustomForm] = useState({
    username: '',
    display_name: '',
    bio: '',
    avatar_url: '',
    followers_count: 12,
    following_count: 950,
    posts_count: 0,
    account_age_days: 3,
    is_verified: false
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (initialTarget) {
      if (typeof initialTarget === 'object') {
        setUsernameInput(initialTarget.username || '');
        handleScan(initialTarget);
      } else if (typeof initialTarget === 'string') {
        setUsernameInput(initialTarget);
        handleScan(initialTarget);
      }
    }
  }, [initialTarget]);

  const loadInitialData = async () => {
    try {
      const [demoRes, historyRes] = await Promise.all([
        getDemoProfiles(),
        getCheckHistory(5)
      ]);
      setDemoProfiles(demoRes.profiles || []);
      setHistory(historyRes.history || []);
    } catch (err) {
      console.error('Failed to load initial scanner data', err);
    }
  };

  const handleScan = async (targetPayload) => {
    setLoading(true);
    try {
      const payload = typeof targetPayload === 'string' 
        ? { username: targetPayload }
        : targetPayload;

      const res = await checkProfile(payload);
      setScanResult(res);
      // Refresh history
      const histRes = await getCheckHistory(5);
      setHistory(histRes.history || []);
      
      onToast && onToast({
        type: res.analysis.risk_score >= 60 ? 'warning' : 'success',
        title: 'Scan Completed',
        message: `Profile @${res.profile.username} evaluated: ${res.analysis.risk_level} RISK (${res.analysis.risk_score}/100)`
      });
    } catch (err) {
      console.error(err);
      onToast && onToast({
        type: 'error',
        title: 'Scan Failed',
        message: err.response?.data?.message || 'Could not analyze profile. Ensure backend server is running.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (!customForm.username) {
      onToast && onToast({ type: 'warning', message: 'Please enter a username.' });
      return;
    }
    handleScan(customForm);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl glass-panel-glow p-6 sm:p-8 border border-slate-800">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI & Rule-Based Behavioral Identity Verification</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Instant Profile & Impersonation Scanner
          </h1>
          <p className="text-sm sm:text-base text-slate-300 mt-2 leading-relaxed">
            Detect typosquatting, bot signatures, follower anomalies, and unauthorized identity clones across social platforms with 100% explainable scoring.
          </p>
        </div>
      </div>

      {/* Mode Switcher & Search Bar */}
      <div className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-900/80 border border-slate-800">
            <button
              onClick={() => setIsCustomMode(false)}
              className={`px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition ${
                !isCustomMode
                  ? 'bg-cyan-500 text-black font-bold shadow-glow-cyan'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Quick Handle Scanner
            </button>
            <button
              onClick={() => setIsCustomMode(true)}
              className={`px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition ${
                isCustomMode
                  ? 'bg-cyan-500 text-black font-bold shadow-glow-cyan'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Custom Attribute Inspector
            </button>
          </div>

          <div className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Try sample test handles below or input any handle</span>
          </div>
        </div>

        {/* Standard Search Bar */}
        {!isCustomMode ? (
          <div className="p-2 rounded-2xl glass-panel border border-slate-800 flex flex-col sm:flex-row items-center gap-2">
            <div className="relative flex-1 w-full">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Enter social handle (e.g. elonmusk_official, satya_nadella_support, alex_tech_dev)..."
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && usernameInput.trim() && handleScan(usernameInput.trim())}
                className="w-full bg-slate-950/60 border border-slate-800/80 rounded-xl pl-12 pr-4 py-3 text-sm text-white placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500 transition"
              />
            </div>
            <button
              onClick={() => usernameInput.trim() && handleScan(usernameInput.trim())}
              disabled={loading || !usernameInput.trim()}
              className="w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-mono font-bold text-sm shadow-glow-cyan transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing Profile...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Execute Risk Scan</span>
                </>
              )}
            </button>
          </div>
        ) : (
          /* Custom Profile Attribute Form */
          <form onSubmit={handleCustomSubmit} className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Username Handle *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. elon_musk_giveaways"
                  value={customForm.username}
                  onChange={(e) => setCustomForm({ ...customForm, username: e.target.value })}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Display Name</label>
                <input
                  type="text"
                  placeholder="e.g. Elon Musk"
                  value={customForm.display_name}
                  onChange={(e) => setCustomForm({ ...customForm, display_name: e.target.value })}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Followers Count</label>
                <input
                  type="number"
                  value={customForm.followers_count}
                  onChange={(e) => setCustomForm({ ...customForm, followers_count: parseInt(e.target.value) || 0 })}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Following Count</label>
                <input
                  type="number"
                  value={customForm.following_count}
                  onChange={(e) => setCustomForm({ ...customForm, following_count: parseInt(e.target.value) || 0 })}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Posts Count</label>
                <input
                  type="number"
                  value={customForm.posts_count}
                  onChange={(e) => setCustomForm({ ...customForm, posts_count: parseInt(e.target.value) || 0 })}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Account Age (Days)</label>
                <input
                  type="number"
                  value={customForm.account_age_days}
                  onChange={(e) => setCustomForm({ ...customForm, account_age_days: parseInt(e.target.value) || 1 })}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-mono text-slate-400 uppercase">Bio / Description</label>
              <textarea
                rows={2}
                placeholder="e.g. Official Crypto Giveaway! DM for promo. Send ETH."
                value={customForm.bio}
                onChange={(e) => setCustomForm({ ...customForm, bio: e.target.value })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-mono text-slate-300">
                <input
                  type="checkbox"
                  checked={customForm.is_verified}
                  onChange={(e) => setCustomForm({ ...customForm, is_verified: e.target.checked })}
                  className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                />
                <span>Platform Verified Badge Present</span>
              </label>

              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 rounded-xl bg-cyan-500 text-black font-mono font-bold text-xs shadow-glow-cyan hover:bg-cyan-400 transition"
              >
                {loading ? 'Evaluating Model...' : 'Scan Custom Profile'}
              </button>
            </div>
          </form>
        )}

        {/* Quick Test Seed Chips */}
        <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
          <span className="text-slate-500 font-semibold">Quick Test Targets:</span>
          {demoProfiles.slice(0, 6).map((demo) => (
            <button
              key={demo.id}
              onClick={() => {
                setUsernameInput(demo.username);
                handleScan(demo);
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-cyan-400 transition flex items-center gap-1"
            >
              <span>@{demo.username}</span>
            </button>
          ))}
        </div>
      </div>

      {/* SCAN RESULTS DISPLAY */}
      {scanResult && (
        <div className="space-y-6 animate-slideUp">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Risk Gauge & Quick Recommendation */}
            <div className="lg:col-span-5 rounded-3xl glass-panel-glow border border-slate-800 p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase text-slate-400">Security Score Card</span>
                  <span className="text-xs font-mono text-cyan-400">ID #{scanResult.profile.id || 'LIVE-SCAN'}</span>
                </div>

                <RiskGauge 
                  score={scanResult.analysis.risk_score} 
                  level={scanResult.analysis.risk_level} 
                />

                {/* Recommendation Banner */}
                <div className="mt-4 p-4 rounded-2xl bg-slate-950/80 border border-slate-800">
                  <div className="flex items-start gap-2.5">
                    <ShieldAlert className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                        Security Advisory
                      </h4>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                        {scanResult.analysis.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Impersonation Match Highlight & Comparison Button */}
              {scanResult.analysis.primary_match && (
                <div className="mt-6 pt-4 border-t border-slate-800/80">
                  <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                      <div>
                        <p className="text-xs font-bold text-white font-mono">
                          Impersonation Target Detected
                        </p>
                        <p className="text-[11px] text-red-300">
                          Matches protected user <strong className="text-white">@{scanResult.analysis.primary_match.username}</strong>
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => setIsCompareOpen(true)}
                      className="px-3 py-1.5 rounded-lg bg-red-500 text-white hover:bg-red-600 font-mono text-xs font-bold transition flex items-center gap-1 shadow-glow-red flex-shrink-0"
                    >
                      <span>Compare</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: Profile Summary & Factored Breakdown */}
            <div className="lg:col-span-7 space-y-6">
              {/* Scanned Profile Header Card */}
              <div className="p-5 rounded-3xl glass-panel border border-slate-800 flex items-start justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3.5">
                  <img
                    src={scanResult.profile.avatar_url || `https://ui-avatars.com/api/?name=${scanResult.profile.display_name}&background=0d1527&color=00f0ff`}
                    alt={scanResult.profile.display_name}
                    className="w-14 h-14 rounded-2xl object-cover border border-slate-700 bg-slate-900"
                  />
                  <div>
                    <h3 className="text-lg font-bold text-white leading-tight">
                      {scanResult.profile.display_name}
                    </h3>
                    <p className="text-xs font-mono text-cyan-400">@{scanResult.profile.username}</p>
                    {scanResult.profile.bio && (
                      <p className="text-xs text-slate-300 mt-1 max-w-md italic">"{scanResult.profile.bio}"</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 font-mono text-xs">
                  <div className="text-right">
                    <p className="text-[10px] text-slate-400 uppercase">Followers</p>
                    <p className="font-bold text-white">{formatNumber(scanResult.profile.followers_count || 0)}</p>
                  </div>
                  <div className="text-right border-l border-slate-800 pl-3">
                    <p className="text-[10px] text-slate-400 uppercase">Following</p>
                    <p className="font-bold text-white">{formatNumber(scanResult.profile.following_count || 0)}</p>
                  </div>
                  <div className="text-right border-l border-slate-800 pl-3">
                    <p className="text-[10px] text-slate-400 uppercase">Posts</p>
                    <p className="font-bold text-white">{formatNumber(scanResult.profile.posts_count || 0)}</p>
                  </div>
                </div>
              </div>

              {/* Contributing Reasons & Transparent Factor Breakdown */}
              <div className="p-6 rounded-3xl glass-panel border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
                      Explainable Risk Attribution ({scanResult.analysis.factors.length} Signals)
                    </h3>
                  </div>
                  <span className="text-xs font-mono text-slate-400">Math Verified</span>
                </div>

                <ReasonList factors={scanResult.analysis.factors} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side Impersonation Modal */}
      {scanResult && scanResult.analysis.primary_match && (
        <ComparisonModal
          isOpen={isCompareOpen}
          onClose={() => setIsCompareOpen(false)}
          targetProfile={scanResult.profile}
          matchedProtected={scanResult.analysis.primary_match}
        />
      )}

      {/* Recent Scan History */}
      {history.length > 0 && (
        <div className="p-6 rounded-3xl glass-panel border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
                Recent Detection History
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">Last 5 Scans</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {history.map((item) => {
              const meta = getRiskMeta(item.risk_level, item.risk_score);
              return (
                <div
                  key={item.id}
                  onClick={() => handleScan(item.target_username)}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition flex items-center justify-between gap-2"
                >
                  <div className="truncate">
                    <p className="text-xs font-mono font-bold text-white truncate">@{item.target_username}</p>
                    <p className="text-[10px] text-slate-400">{formatTimeAgo(item.created_at)}</p>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${meta.badgeBg}`}>
                    {item.risk_score}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
