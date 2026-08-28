import React, { useState, useEffect } from 'react';
import { 
  UserCheck, 
  ShieldCheck, 
  Plus, 
  Radio, 
  Mail, 
  AlertTriangle, 
  RefreshCw, 
  Check, 
  Search,
  Lock,
  ToggleLeft,
  ToggleRight,
  BadgeCheck,
  Trash2
} from 'lucide-react';
import { registerUser, getProtectedUsers, toggleMonitoring, runSurveillance, deleteProtectedUser } from '../api/client';
import { formatNumber, formatTimeAgo } from '../utils/riskHelpers';

export default function ProtectedPage({ onToast, onNavigateToMonitoring }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [form, setForm] = useState({
    username: '',
    display_name: '',
    email: '',
    bio: '',
    avatar_url: '',
    follower_count: 50000
  });

  useEffect(() => {
    fetchProtectedUsers();
  }, []);

  const fetchProtectedUsers = async () => {
    setLoading(true);
    try {
      const res = await getProtectedUsers();
      setUsers(res.protected_users || []);
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to load protected identities.' });
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await registerUser(form);
      onToast && onToast({
        type: 'success',
        title: 'Identity Protected',
        message: res.message
      });
      if (res.initial_alerts_found > 0) {
        onToast && onToast({
          type: 'warning',
          title: 'Immediate Threat Detected',
          message: `Found ${res.initial_alerts_found} existing suspicious profile(s) mimicking your account!`
        });
      }
      setForm({
        username: '',
        display_name: '',
        email: '',
        bio: '',
        avatar_url: '',
        follower_count: 50000
      });
      setShowRegisterForm(false);
      fetchProtectedUsers();
    } catch (err) {
      console.error(err);
      onToast && onToast({
        type: 'error',
        title: 'Registration Error',
        message: err.response?.data?.message || 'Could not register identity.'
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (userId, currentState) => {
    try {
      const newState = !currentState;
      await toggleMonitoring(userId, newState);
      setUsers(users.map(u => u.id === userId ? { ...u, is_monitoring_active: newState ? 1 : 0 } : u));
      onToast && onToast({
        type: 'info',
        message: `Monitoring ${newState ? 'activated' : 'deactivated'} for user.`
      });
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to update monitoring state.' });
    }
  };

  const handleQuickSurveillance = async (username) => {
    try {
      const res = await runSurveillance(username);
      onToast && onToast({
        type: res.new_alerts_count > 0 ? 'warning' : 'success',
        title: 'Surveillance Check',
        message: res.message
      });
      fetchProtectedUsers();
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Surveillance cycle failed.' });
    }
  };

  const handleDeleteProtected = async (userId, username) => {
    if (!window.confirm(`Remove @${username} from the protected identity vault?`)) return;
    try {
      await deleteProtectedUser(userId);
      setUsers(users.filter(u => u.id !== userId));
      onToast && onToast({
        type: 'info',
        message: `@${username} removed from protected identity vault.`
      });
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to delete protected identity.' });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 sm:p-8 rounded-3xl glass-panel-glow border border-slate-800">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs mb-3">
            <Lock className="w-3.5 h-3.5" />
            <span>Cryptographic & Verified Identity Vault</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Protected Identity Registry
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
            Register your official social identity to enable automated anti-impersonation surveillance, fake account detection, and instant security alerts.
          </p>
        </div>

        <button
          onClick={() => setShowRegisterForm(!showRegisterForm)}
          className="flex-shrink-0 flex items-center gap-2 px-5 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-mono font-bold text-xs shadow-glow-cyan transition"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>{showRegisterForm ? 'Close Registration Form' : 'Register New Identity'}</span>
        </button>
      </div>

      {/* Registration Modal / Dropdown Form */}
      {showRegisterForm && (
        <form onSubmit={handleRegister} className="p-6 sm:p-8 rounded-3xl glass-panel border border-cyan-500/40 shadow-glow-cyan space-y-5 animate-slideUp">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <h3 className="font-mono font-bold text-white text-base">
              New Official Identity Registration
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-mono text-slate-400 uppercase">Official Handle (@username) *</label>
              <input
                type="text"
                required
                placeholder="e.g. jensen_huang"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value.replace(/^@/, '') })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-mono text-slate-400 uppercase">Display Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Jensen Huang"
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-mono text-slate-400 uppercase">Registered Security Email *</label>
              <input
                type="email"
                required
                placeholder="e.g. security@nvidia.corp"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-mono text-slate-400 uppercase">Avatar URL</label>
              <input
                type="url"
                placeholder="https://example.com/avatar.jpg"
                value={form.avatar_url}
                onChange={(e) => setForm({ ...form, avatar_url: e.target.value })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-mono text-slate-400 uppercase">Baseline Follower Count</label>
              <input
                type="number"
                value={form.follower_count}
                onChange={(e) => setForm({ ...form, follower_count: parseInt(e.target.value) || 0 })}
                className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-mono text-slate-400 uppercase">Official Verified Bio</label>
            <textarea
              rows={2}
              placeholder="e.g. Founder & CEO of NVIDIA. AI and accelerated computing."
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowRegisterForm(false)}
              className="px-5 py-2.5 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs font-mono transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-7 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 text-black font-mono font-bold text-xs shadow-glow-cyan transition flex items-center gap-2"
            >
              {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              <span>Confirm & Activate Protection</span>
            </button>
          </div>
        </form>
      )}

      {/* Protected Users List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="font-mono font-bold text-white text-sm uppercase tracking-wider">
              Enrolled Authentic Accounts ({users.length})
            </h3>
          </div>
          <button
            onClick={fetchProtectedUsers}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {users.map((user) => {
            const isMonitoring = Boolean(user.is_monitoring_active);
            const defaultAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.display_name)}&background=0d1527&color=10b981`;
            return (
              <div
                key={user.id}
                className="p-5 rounded-2xl glass-panel border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <img
                        src={user.avatar_url || defaultAvatar}
                        alt={user.display_name}
                        className="w-12 h-12 rounded-xl object-cover border border-emerald-500/40 bg-slate-900"
                        onError={(e) => { e.target.src = defaultAvatar; }}
                      />
                      <div>
                        <div className="flex items-center gap-1.5">
                          <h4 className="font-bold text-white text-sm">{user.display_name}</h4>
                          <BadgeCheck className="w-4 h-4 text-cyan-400" />
                        </div>
                        <p className="text-xs font-mono text-emerald-400">@{user.username}</p>
                      </div>
                    </div>

                    {/* Monitoring Switch */}
                    <button
                      onClick={() => handleToggle(user.id, isMonitoring)}
                      title="Toggle Continuous Impersonation Surveillance"
                      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-mono font-bold transition ${
                        isMonitoring
                          ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-glow-green'
                          : 'bg-slate-900 text-slate-500 border-slate-800'
                      }`}
                    >
                      <Radio className={`w-3 h-3 ${isMonitoring ? 'animate-pulse text-emerald-400' : ''}`} />
                      <span>{isMonitoring ? 'SURVEILLANCE ON' : 'DISABLED'}</span>
                    </button>
                  </div>

                  {user.bio && (
                    <p className="text-xs text-slate-300 mt-3 line-clamp-2 italic">
                      "{user.bio}"
                    </p>
                  )}

                  <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs font-mono">
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="flex items-center gap-1.5">
                        <Mail className="w-3.5 h-3.5 text-slate-500" />
                        <span className="truncate max-w-[170px]">{user.email}</span>
                      </span>
                      <span className="text-white font-bold">{formatNumber(user.follower_count || 0)} followers</span>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-slate-500 text-[11px]">Enrolled: {formatTimeAgo(user.created_at)}</span>
                      {user.unread_alerts > 0 ? (
                        <button
                          onClick={onNavigateToMonitoring}
                          className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30 text-[10px] font-bold animate-pulse"
                        >
                          {user.unread_alerts} Active Alert(s)
                        </button>
                      ) : (
                        <span className="text-emerald-400 text-[10px]">No Active Threats</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center gap-2">
                  <button
                    onClick={() => handleQuickSurveillance(user.username)}
                    className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-xs font-mono transition"
                  >
                    <Search className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Immediate Threat Sweep</span>
                  </button>
                  <button
                    onClick={() => handleDeleteProtected(user.id, user.username)}
                    title="Unenroll protected identity"
                    className="p-2 rounded-xl bg-slate-900 hover:bg-red-500/20 text-slate-500 hover:text-red-400 border border-slate-800 hover:border-red-500/30 text-xs transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
