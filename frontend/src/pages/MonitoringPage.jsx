import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  ShieldAlert, 
  AlertTriangle, 
  Mail, 
  CheckCircle, 
  RefreshCw, 
  Filter, 
  Send, 
  Check, 
  ExternalLink,
  ChevronRight,
  Eye,
  Lock,
  ArrowRight
} from 'lucide-react';
import { getAlerts, updateAlertStatus, dispatchEmailAlert, runSurveillance } from '../api/client';
import { formatNumber, formatTimeAgo, getRiskMeta } from '../utils/riskHelpers';

export default function MonitoringPage({ onToast }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [emailModalData, setEmailModalData] = useState(null);

  useEffect(() => {
    fetchAlerts();
  }, [filterStatus]);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await getAlerts(filterStatus);
      setAlerts(res.alerts || []);
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to load security alerts.' });
    } finally {
      setLoading(false);
    }
  };

  const handleRunSurveillance = async () => {
    setScanning(true);
    try {
      const res = await runSurveillance();
      onToast && onToast({
        type: res.new_alerts_count > 0 ? 'warning' : 'success',
        title: 'Surveillance Sweep Complete',
        message: res.message
      });
      fetchAlerts();
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Surveillance check failed.' });
    } finally {
      setScanning(false);
    }
  };

  const handleStatusUpdate = async (alertId, newStatus) => {
    try {
      await updateAlertStatus(alertId, newStatus);
      setAlerts(alerts.map(a => a.id === alertId ? { ...a, status: newStatus } : a));
      onToast && onToast({
        type: 'info',
        message: `Alert marked as ${newStatus}.`
      });
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Could not update alert status.' });
    }
  };

  const handleSendEmail = async (alertId) => {
    try {
      const res = await dispatchEmailAlert(alertId);
      setEmailModalData(res.email_details);
      setAlerts(alerts.map(a => a.id === alertId ? { ...a, email_dispatched: 1 } : a));
      onToast && onToast({
        type: 'success',
        title: 'Email Dispatched',
        message: `Notification sent to registered email: ${res.email_details.recipient}`
      });
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to dispatch email.' });
    }
  };

  const unreadCount = alerts.filter(a => a.status === 'UNREAD').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Surveillance Operations Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 sm:p-8 rounded-3xl glass-panel-glow border border-slate-800">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-xs mb-3">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Continuous Anti-Impersonation Surveillance</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Active Threat & Impersonation Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
            Real-time security radar monitoring the social environment for clone handles, typosquatting vectors, and unauthorized duplicate identities.
          </p>
        </div>

        <button
          onClick={handleRunSurveillance}
          disabled={scanning}
          className="flex-shrink-0 flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-400 hover:to-orange-400 text-white font-mono font-bold text-xs shadow-glow-red transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          <span>{scanning ? 'Sweeping Social Grid...' : 'Run Automated Surveillance Sweep'}</span>
        </button>
      </div>

      {/* Filter Tabs & Stats Bar */}
      <div className="flex items-center justify-between flex-wrap gap-4 p-4 rounded-2xl glass-panel border border-slate-800">
        <div className="flex items-center gap-2 flex-wrap">
          {[
            { id: '', label: 'All Incidents', count: alerts.length },
            { id: 'UNREAD', label: 'Unread Threats', count: unreadCount, badgeColor: 'bg-red-500' },
            { id: 'ACKNOWLEDGED', label: 'Acknowledged', count: alerts.filter(a => a.status === 'ACKNOWLEDGED').length },
            { id: 'RESOLVED', label: 'Resolved', count: alerts.filter(a => a.status === 'RESOLVED').length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterStatus(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition ${
                filterStatus === tab.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <span>{tab.label}</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                tab.badgeColor ? `${tab.badgeColor} text-white` : 'bg-slate-800 text-slate-300'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        <button
          onClick={fetchAlerts}
          className="text-xs font-mono text-slate-400 hover:text-white flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Alerts Stream List */}
      <div className="space-y-4">
        {alerts.length === 0 ? (
          <div className="p-12 text-center rounded-3xl glass-panel border border-slate-800 space-y-3">
            <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto" />
            <h3 className="text-base font-mono font-bold text-white">No Threat Incidents Found</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              All monitored identities are safe. Run a surveillance sweep or create a lookalike test profile in the Sandbox to test detection.
            </p>
          </div>
        ) : (
          alerts.map((alert) => {
            const meta = getRiskMeta(alert.risk_level, alert.risk_score);
            const isUnread = alert.status === 'UNREAD';

            return (
              <div
                key={alert.id}
                className={`p-6 rounded-3xl glass-panel border transition-all duration-200 ${
                  isUnread 
                    ? 'border-red-500/40 bg-red-950/10 shadow-glow-red' 
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Alert Header */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                  <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-xl border ${meta.badgeBg}`}>
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono font-bold text-white uppercase">
                          INCIDENT #{alert.id}
                        </span>
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${meta.badgeBg}`}>
                          {alert.risk_level} RISK ({alert.risk_score}/100)
                        </span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase ${
                          isUnread ? 'bg-red-500 text-white font-bold animate-pulse' : 'bg-slate-800 text-slate-400'
                        }`}>
                          {alert.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Detected: {formatTimeAgo(alert.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Quick Action Buttons */}
                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => handleSendEmail(alert.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold transition ${
                        alert.email_dispatched
                          ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                          : 'bg-slate-900 hover:bg-slate-800 text-cyan-300 border-cyan-500/30'
                      }`}
                    >
                      <Mail className="w-3.5 h-3.5" />
                      <span>{alert.email_dispatched ? 'Alert Dispatched' : 'Dispatch Email'}</span>
                    </button>

                    {alert.status !== 'RESOLVED' ? (
                      <button
                        onClick={() => handleStatusUpdate(alert.id, 'RESOLVED')}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-emerald-600 text-slate-200 hover:text-white font-mono text-xs font-semibold transition flex items-center gap-1"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Resolve Threat</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStatusUpdate(alert.id, 'UNREAD')}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-white font-mono text-xs transition"
                      >
                        Reopen
                      </button>
                    )}
                  </div>
                </div>

                {/* Impersonation Contrast Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  {/* Targeted Protected Account */}
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">
                      Protected Identity (Victim)
                    </span>
                    <div className="flex items-center gap-3 mt-2">
                      <img
                        src={alert.protected_avatar_url || `https://ui-avatars.com/api/?name=${alert.protected_display_name}&background=0d1527&color=10b981`}
                        alt={alert.protected_display_name}
                        className="w-10 h-10 rounded-xl object-cover border border-emerald-500/30"
                      />
                      <div className="truncate">
                        <p className="text-xs font-bold text-white">{alert.protected_display_name}</p>
                        <p className="text-xs font-mono text-emerald-400">@{alert.protected_username}</p>
                        <p className="text-[10px] text-slate-400 truncate">{alert.protected_email}</p>
                      </div>
                    </div>
                  </div>

                  {/* Suspicious Impersonator Clone Account */}
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-red-500/20">
                    <span className="text-[10px] font-mono text-red-400 uppercase font-bold">
                      Flagged Impersonator Handle
                    </span>
                    <div className="flex items-center gap-3 mt-2">
                      <img
                        src={alert.demo_avatar_url || `https://ui-avatars.com/api/?name=${alert.demo_display_name}&background=0d1527&color=ef4444`}
                        alt={alert.demo_display_name}
                        className="w-10 h-10 rounded-xl object-cover border border-red-500/30"
                      />
                      <div className="truncate">
                        <p className="text-xs font-bold text-white">{alert.demo_display_name}</p>
                        <p className="text-xs font-mono text-red-400">@{alert.demo_username}</p>
                        <p className="text-[10px] text-slate-400">
                          {formatNumber(alert.demo_followers_count || 0)} followers | {formatNumber(alert.demo_following_count || 0)} following
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Threat Reasons Summary */}
                <div className="mt-4 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
                  <span className="font-mono font-bold text-cyan-400 uppercase tracking-wider block mb-1">
                    Detection Vector:
                  </span>
                  <p className="leading-relaxed">{alert.reason_summary}</p>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Simulated Email Modal */}
      {emailModalData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-lg rounded-2xl glass-panel-glow bg-slate-950 border border-slate-700 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-cyan-400 font-mono text-sm font-bold">
                <Mail className="w-4 h-4" />
                <span>Security Dispatch Simulation</span>
              </div>
              <button
                onClick={() => setEmailModalData(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 space-y-3 font-mono text-xs">
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
                <p className="text-slate-500">To:</p>
                <p className="text-white font-bold">{emailModalData.recipient}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
                <p className="text-slate-500">Subject:</p>
                <p className="text-red-400 font-bold">{emailModalData.subject}</p>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 space-y-2 leading-relaxed">
                <p>⚠️ <strong>SECURITY ALERT:</strong> An account attempting unauthorized identity mimicry has been detected targeting your profile.</p>
                <p><strong>Flagged Handle:</strong> {emailModalData.flagged_account}</p>
                <p><strong>Calculated Threat Rating:</strong> {emailModalData.risk_level} ({emailModalData.risk_score}/100)</p>
                <p><strong>Reasons:</strong> {emailModalData.reasons}</p>
                <p className="text-slate-400 text-[11px] pt-2 border-t border-slate-800">
                  Automated alert triggered by Aegis.Guard Behavioral Anti-Impersonation Engine.
                </p>
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={() => setEmailModalData(null)}
                className="px-5 py-2 rounded-xl bg-cyan-500 text-black font-mono text-xs font-bold"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
