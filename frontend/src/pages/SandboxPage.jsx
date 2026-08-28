import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  Plus, 
  Search, 
  RefreshCw, 
  Trash2, 
  ShieldAlert, 
  Check, 
  Sparkles, 
  SlidersHorizontal,
  Bot,
  UserCheck,
  Zap
} from 'lucide-react';
import ProfileCard from '../components/ProfileCard';
import { getDemoProfiles, createDemoProfile, deleteDemoProfile } from '../api/client';

export default function SandboxPage({ onScanTarget, onToast }) {
  const [profiles, setProfiles] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);

  // New Demo Profile Form
  const [formData, setFormData] = useState({
    username: '',
    display_name: '',
    bio: '',
    avatar_url: '',
    followers_count: 5,
    following_count: 1400,
    posts_count: 0,
    account_age_days: 2,
    is_verified: false
  });

  useEffect(() => {
    fetchProfiles();
  }, [searchQuery]);

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const res = await getDemoProfiles(searchQuery);
      setProfiles(res.profiles || []);
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to load demo sandbox profiles.' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await createDemoProfile(formData);
      onToast && onToast({
        type: 'success',
        title: 'Profile Created in Sandbox',
        message: res.message
      });

      if (res.alert_triggered) {
        onToast && onToast({
          type: 'warning',
          title: '🚨 Anti-Impersonation Alert Fired!',
          message: `The newly created profile was automatically flagged as a threat (${res.immediate_analysis.risk_level} RISK)!`
        });
      }

      setFormData({
        username: '',
        display_name: '',
        bio: '',
        avatar_url: '',
        followers_count: 5,
        following_count: 1400,
        posts_count: 0,
        account_age_days: 2,
        is_verified: false
      });
      setShowCreateModal(false);
      fetchProfiles();
    } catch (err) {
      console.error(err);
      onToast && onToast({
        type: 'error',
        title: 'Creation Failed',
        message: err.response?.data?.message || 'Could not create demo profile.'
      });
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (profileId, username) => {
    if (!window.confirm(`Delete @${username} from sandbox?`)) return;
    try {
      await deleteDemoProfile(profileId);
      setProfiles(profiles.filter(p => p.id !== profileId));
      onToast && onToast({ type: 'info', message: `@${username} removed from sandbox.` });
    } catch (err) {
      console.error(err);
      onToast && onToast({ type: 'error', message: 'Failed to delete demo profile.' });
    }
  };

  // Quick Preset Attack Scenarios for College Demo / Presentations
  const loadPreset = (presetType) => {
    switch (presetType) {
      case 'elon_clone':
        setFormData({
          username: 'elonmusk_airdrop_official',
          display_name: 'Elon Musk Special Event',
          bio: 'CEO of Tesla. Celebrating Starship launch with a Free Bitcoin & Crypto Giveaway! DM for promo link.',
          avatar_url: 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150&auto=format&fit=crop&q=80',
          followers_count: 3,
          following_count: 2200,
          posts_count: 1,
          account_age_days: 1,
          is_verified: false
        });
        break;
      case 'satya_support':
        setFormData({
          username: 'satya_nadella_desk',
          display_name: 'Satya Nadella Official Support',
          bio: 'Microsoft executive team. WhatsApp only for recovery and technical claims.',
          avatar_url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
          followers_count: 8,
          following_count: 850,
          posts_count: 0,
          account_age_days: 2,
          is_verified: false
        });
        break;
      case 'spam_bot':
        setFormData({
          username: 'airdrop_rewards_bot2026',
          display_name: 'Guaranteed Profit Bot',
          bio: 'Guaranteed returns daily! Join our telegram group for free tokens and gifts.',
          avatar_url: '',
          followers_count: 1,
          following_count: 4500,
          posts_count: 0,
          account_age_days: 10,
          is_verified: false
        });
        break;
      case 'benign_user':
        setFormData({
          username: 'emily_frontend_coder',
          display_name: 'Emily Davis',
          bio: 'React and Tailwind developer building responsive web applications. Coffee lover 💻',
          avatar_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
          followers_count: 820,
          following_count: 310,
          posts_count: 64,
          account_age_days: 420,
          is_verified: false
        });
        break;
      default:
        break;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Sandbox Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 sm:p-8 rounded-3xl glass-panel-glow border border-slate-800">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs mb-3">
            <Layers className="w-3.5 h-3.5" />
            <span>Controlled Mock Social Media Environment (SocialSphere Sandbox)</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Social Media Simulation Network
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
            A safe, controlled environment simulating authentic personalities, typosquatting copycats, and malicious spam bots to demonstrate risk scoring without external API restrictions.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex-shrink-0 flex items-center gap-2 px-5 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-mono font-bold text-xs shadow-glow-cyan transition"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>Simulate New Profile</span>
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex items-center justify-between flex-wrap gap-4 p-4 rounded-2xl glass-panel border border-slate-800">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search demo platform profiles by username or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/70 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span>Total Sandbox Profiles: <strong className="text-cyan-400">{profiles.length}</strong></span>
        </div>
      </div>

      {/* Profiles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {profiles.map((profile) => (
          <div key={profile.id} className="relative group">
            <ProfileCard
              profile={profile}
              onScan={(p) => onScanTarget(p)}
            />
            <button
              onClick={() => handleDelete(profile.id, profile.username)}
              title="Remove from sandbox"
              className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-900/90 text-slate-500 hover:text-red-400 hover:bg-red-500/20 border border-slate-800 opacity-0 group-hover:opacity-100 transition duration-200"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      {/* Create Demo Profile Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-2xl rounded-3xl glass-panel-glow bg-slate-950 border border-slate-700 p-6 sm:p-8 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2 text-cyan-400">
                <Layers className="w-5 h-5" />
                <h3 className="font-mono font-bold text-white text-base">
                  Simulate New Profile in Sandbox
                </h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* Attack Scenario Presets */}
            <div className="mt-4 p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <span className="text-[11px] font-mono font-semibold text-slate-400 uppercase">
                ⚡ Quick Load Attack Scenario:
              </span>
              <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                <button
                  type="button"
                  onClick={() => loadPreset('elon_clone')}
                  className="px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 transition"
                >
                  Elon Giveaway Clone
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset('satya_support')}
                  className="px-2.5 py-1 rounded-lg bg-orange-500/10 text-orange-400 border border-orange-500/30 hover:bg-orange-500/20 transition"
                >
                  Satya Fake Support Desk
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset('spam_bot')}
                  className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 transition"
                >
                  Mass-Follow Spam Bot
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset('benign_user')}
                  className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition"
                >
                  Benign Developer
                </button>
              </div>
            </div>

            <form onSubmit={handleCreate} className="mt-5 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Username Handle *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. elon_musk_giveaways"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value.replace(/^@/, '') })}
                    className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Display Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Elon Musk"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Followers Count</label>
                  <input
                    type="number"
                    value={formData.followers_count}
                    onChange={(e) => setFormData({ ...formData, followers_count: parseInt(e.target.value) || 0 })}
                    className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Following Count</label>
                  <input
                    type="number"
                    value={formData.following_count}
                    onChange={(e) => setFormData({ ...formData, following_count: parseInt(e.target.value) || 0 })}
                    className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Posts Count</label>
                  <input
                    type="number"
                    value={formData.posts_count}
                    onChange={(e) => setFormData({ ...formData, posts_count: parseInt(e.target.value) || 0 })}
                    className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Account Age (Days)</label>
                  <input
                    type="number"
                    value={formData.account_age_days}
                    onChange={(e) => setFormData({ ...formData, account_age_days: parseInt(e.target.value) || 1 })}
                    className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Bio / Description</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Official page! Crypto Giveaway active. DM for collab."
                  value={formData.bio}
                  onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                  className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-mono text-slate-400 uppercase">Avatar URL</label>
                <input
                  type="url"
                  placeholder="https://example.com/avatar.jpg"
                  value={formData.avatar_url}
                  onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                  className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center gap-2 cursor-pointer text-xs font-mono text-slate-300">
                  <input
                    type="checkbox"
                    checked={formData.is_verified}
                    onChange={(e) => setFormData({ ...formData, is_verified: e.target.checked })}
                    className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Verified Platform Checkmark</span>
                </label>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 hover:text-white text-xs font-mono"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="px-6 py-2 rounded-xl bg-cyan-500 text-black font-mono font-bold text-xs shadow-glow-cyan hover:bg-cyan-400 transition"
                  >
                    {creating ? 'Spawning Profile...' : 'Spawn Demo Profile'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
