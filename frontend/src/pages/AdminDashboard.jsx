import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  ShieldAlert, 
  ShieldCheck, 
  Radio, 
  History, 
  RefreshCw, 
  RotateCcw, 
  AlertTriangle, 
  Eye, 
  Users, 
  FileText,
  Search,
  Filter
} from 'lucide-react';
import { getAdminStats, getAdminLogs, resetDemoDb } from '../api/client';
import { formatNumber, formatTimeAgo, getRiskMeta } from '../utils/riskHelpers';

export default function AdminDashboard({ onToast }) {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRiskFilter, setSelectedRiskFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLogDetail, setSelectedLogDetail] = useState(null);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedRiskFilter, searchQuery]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [statsRes, logsRes] = await Promise.all([
        getAdminStats(),
        getAdminLogs(selectedRiskFilter, searchQuery)
      ]);
      setStats(statsRes.stats || null);
      setLogs(logsRes.logs || []);
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to load SOC analytics.' });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset database to default seed state? This will clear all custom alerts and re-seed demo data.')) return;
    setResetting(true);
    try {
      const res = await resetDemoDb();
      onToast && onToast({
        type: 'success',
        title: 'Environment Reset',
        message: res.message
      });
      fetchDashboardData();
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to reset environment.' });
    } finally {
      setResetting(false);
    }
  };

  const totalScans = stats?.total_checks || 0;
  const dist = stats?.risk_distribution || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
  const totalDist = (dist.LOW + dist.MEDIUM + dist.HIGH + dist.CRITICAL) || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* SOC Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 sm:p-8 rounded-3xl glass-panel-glow border border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs mb-3">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Security Operations Center (SOC) Analytics</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Threat Intelligence & Admin Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
            Real-time telemetry, model score attribution metrics, impersonation target frequency, and system audit trails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchDashboardData}
            className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-mono transition"
            title="Refresh Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleReset}
            disabled={resetting}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 font-mono text-xs font-bold transition disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Demo DB</span>
          </button>
        </div>
      </div>

      {/* Top Telemetry KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-5">
        <div className="p-5 rounded-2xl glass-panel border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-slate-400">Total Scans Executed</span>
            <History className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-mono font-extrabold text-white mt-3">
            {formatNumber(totalScans)}
          </p>
          <span className="text-[10px] font-mono text-cyan-400/80 mt-1">Full Audit Trails Logged</span>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-slate-400">Critical / High Threats</span>
            <ShieldAlert className="w-4 h-4 text-red-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-mono font-extrabold text-red-400 mt-3">
            {formatNumber(dist.CRITICAL + dist.HIGH)}
          </p>
          <span className="text-[10px] font-mono text-red-400/80 mt-1">Impersonators & Spammers</span>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-slate-400">Protected Enrolled</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-mono font-extrabold text-emerald-400 mt-3">
            {stats?.total_protected_users || 0}
          </p>
          <span className="text-[10px] font-mono text-emerald-400/80 mt-1">
            {stats?.active_monitored_users || 0} under live surveillance
          </span>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-slate-400">Active Alert Queue</span>
            <Radio className="w-4 h-4 text-orange-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-mono font-extrabold text-orange-400 mt-3">
            {stats?.unread_alerts || 0}
          </p>
          <span className="text-[10px] font-mono text-orange-400/80 mt-1">
            {stats?.resolved_alerts || 0} resolved incidents
          </span>
        </div>
      </div>

      {/* Middle Grid: Risk Distribution & Top Targets */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Risk Distribution Breakdown */}
        <div className="lg:col-span-6 p-6 rounded-3xl glass-panel border border-slate-800 space-y-4">
          <h3 className="font-mono font-bold text-white text-sm uppercase tracking-wider">
            Risk Tier Distribution
          </h3>

          <div className="space-y-3 pt-2">
            {[
              { label: 'CRITICAL RISK (80-100)', count: dist.CRITICAL, color: 'bg-red-500', text: 'text-red-400' },
              { label: 'HIGH RISK (60-79)', count: dist.HIGH, color: 'bg-orange-500', text: 'text-orange-400' },
              { label: 'MEDIUM RISK (30-59)', count: dist.MEDIUM, color: 'bg-amber-500', text: 'text-amber-400' },
              { label: 'LOW RISK (0-29)', count: dist.LOW, color: 'bg-emerald-500', text: 'text-emerald-400' }
            ].map((tier, i) => {
              const pct = Math.round((tier.count / totalDist) * 100) || 0;
              return (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className={tier.text}>{tier.label}</span>
                    <span className="text-slate-300 font-bold">{tier.count} ({pct}%)</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${tier.color} transition-all duration-700`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Targeted Protected Users */}
        <div className="lg:col-span-6 p-6 rounded-3xl glass-panel border border-slate-800 space-y-4">
          <h3 className="font-mono font-bold text-white text-sm uppercase tracking-wider">
            Top Targeted Genuine Identities
          </h3>

          <div className="space-y-2.5 pt-2">
            {stats?.top_impersonated_targets?.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No impersonation attempts recorded yet.</p>
            ) : (
              stats?.top_impersonated_targets?.map((target, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-xs font-bold text-slate-500">#{idx + 1}</span>
                    <div>
                      <p className="text-xs font-bold text-white">{target.display_name}</p>
                      <p className="text-[11px] font-mono text-emerald-400">@{target.username}</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-lg bg-red-500/15 text-red-400 border border-red-500/30 text-xs font-mono font-bold">
                    {target.impersonation_count} Impersonator Clones
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="p-6 rounded-3xl glass-panel border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-cyan-400" />
            <h3 className="font-mono font-bold text-white text-sm uppercase tracking-wider">
              Detection Audit History ({logs.length})
            </h3>
          </div>

          <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
            {/* Risk filter */}
            <select
              value={selectedRiskFilter}
              onChange={(e) => setSelectedRiskFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Risk Levels</option>
              <option value="CRITICAL">Critical Risk</option>
              <option value="HIGH">High Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="LOW">Low Risk</option>
            </select>

            {/* Search */}
            <input
              type="text"
              placeholder="Search target handle..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-300 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Logs Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="py-3 px-3">Target Username</th>
                <th className="py-3 px-3">Risk Rating</th>
                <th className="py-3 px-3">Matched Protected User</th>
                <th className="py-3 px-3">Primary Factors</th>
                <th className="py-3 px-3">Scanned Time</th>
                <th className="py-3 px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {logs.map((log) => {
                const meta = getRiskMeta(log.risk_level, log.risk_score);
                return (
                  <tr key={log.id} className="hover:bg-slate-900/50 transition">
                    <td className="py-3 px-3 font-bold text-white">
                      @{log.target_username}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded font-bold ${meta.badgeBg}`}>
                        {log.risk_score}/100 ({log.risk_level})
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {log.protected_username ? (
                        <span className="text-emerald-400">@{log.protected_username}</span>
                      ) : (
                        <span className="text-slate-500">None (Standalone)</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-400 max-w-xs truncate">
                      {log.factors && log.factors.length > 0 
                        ? log.factors[0].description 
                        : 'Standard authentic profile'}
                    </td>
                    <td className="py-3 px-3 text-slate-500">
                      {formatTimeAgo(log.created_at)}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => setSelectedLogDetail(log)}
                        className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-400 border border-slate-800 hover:border-cyan-500/40 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Log Detail Inspector Modal */}
      {selectedLogDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-2xl rounded-2xl glass-panel-glow bg-slate-950 border border-slate-700 p-6 shadow-2xl overflow-y-auto max-h-[85vh]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                <h3 className="font-mono font-bold text-white text-base">
                  Audit Scan Record #{selectedLogDetail.id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedLogDetail(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 space-y-4 font-mono text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800">
                <div>
                  <p className="text-slate-500">Target Scanned Handle:</p>
                  <p className="text-white font-bold text-sm">@{selectedLogDetail.target_username}</p>
                </div>
                <div>
                  <p className="text-slate-500">Risk Assessment:</p>
                  <p className="font-bold text-sm text-cyan-400">
                    {selectedLogDetail.risk_score}/100 ({selectedLogDetail.risk_level})
                  </p>
                </div>
              </div>

              {selectedLogDetail.recommendation && (
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
                  <p className="text-slate-500 uppercase text-[10px]">Advisory Output:</p>
                  <p className="mt-1">{selectedLogDetail.recommendation}</p>
                </div>
              )}

              <div>
                <p className="text-slate-400 font-bold uppercase text-[11px] mb-2">
                  Contributing Factors Breakdown:
                </p>
                <div className="space-y-2">
                  {selectedLogDetail.factors?.map((f, i) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex justify-between gap-2">
                      <div>
                        <span className="font-bold text-slate-200">{f.category}:</span>
                        <p className="text-slate-400 mt-0.5">{f.description}</p>
                      </div>
                      <span className="text-red-400 font-bold flex-shrink-0">+{f.points} pts</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={() => setSelectedLogDetail(null)}
                className="px-5 py-2 rounded-xl bg-cyan-500 text-black font-mono text-xs font-bold"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
