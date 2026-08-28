import React from 'react';
import { 
  BadgeCheck, 
  Calendar, 
  Users, 
  UserCheck, 
  Image as ImageIcon, 
  Search,
  ExternalLink,
  Sparkles
} from 'lucide-react';
import { formatNumber } from '../utils/riskHelpers';

export default function ProfileCard({ profile, onScan, isSelected = false, compact = false }) {
  if (!profile) return null;

  const defaultAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(profile.display_name || profile.username)}&background=0d1527&color=00f0ff`;
  const avatar = profile.avatar_url && profile.avatar_url.trim() !== '' ? profile.avatar_url : defaultAvatar;

  return (
    <div className={`rounded-2xl glass-panel border transition-all duration-300 ${
      isSelected 
        ? 'border-cyan-500/60 shadow-glow-cyan bg-cyan-950/20' 
        : 'border-slate-800/80 hover:border-slate-700/90'
    } p-4 sm:p-5 flex flex-col justify-between`}>
      {/* Header Info */}
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="relative">
              <img
                src={avatar}
                alt={profile.display_name}
                className="w-12 h-12 rounded-xl object-cover border border-slate-700 bg-slate-900"
                onError={(e) => { e.target.src = defaultAvatar; }}
              />
              {Boolean(profile.is_verified) && (
                <div className="absolute -bottom-1 -right-1 bg-cyan-500 rounded-full p-0.5 text-black">
                  <BadgeCheck className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h4 className="font-semibold text-white text-sm sm:text-base leading-tight">
                  {profile.display_name}
                </h4>
                {Boolean(profile.is_verified) && (
                  <BadgeCheck className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                )}
              </div>
              <p className="text-xs font-mono text-cyan-400/90">
                @{profile.username}
              </p>
            </div>
          </div>
        </div>

        {/* Bio */}
        {profile.bio && (
          <p className="text-xs text-slate-300 mt-3 line-clamp-2 leading-relaxed">
            {profile.bio}
          </p>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-800/60 text-center">
          <div className="p-1.5 rounded-lg bg-slate-900/40">
            <p className="text-[10px] uppercase font-mono text-slate-400">Followers</p>
            <p className="text-xs font-mono font-bold text-white mt-0.5">
              {formatNumber(profile.followers_count || profile.follower_count || 0)}
            </p>
          </div>
          <div className="p-1.5 rounded-lg bg-slate-900/40">
            <p className="text-[10px] uppercase font-mono text-slate-400">Following</p>
            <p className="text-xs font-mono font-bold text-white mt-0.5">
              {formatNumber(profile.following_count || 0)}
            </p>
          </div>
          <div className="p-1.5 rounded-lg bg-slate-900/40">
            <p className="text-[10px] uppercase font-mono text-slate-400">Posts</p>
            <p className="text-xs font-mono font-bold text-white mt-0.5">
              {formatNumber(profile.posts_count || 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      {onScan && (
        <button
          onClick={() => onScan(profile)}
          className="mt-4 w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-cyan-500/15 hover:bg-cyan-500 text-cyan-300 hover:text-black border border-cyan-500/30 hover:border-cyan-400 font-mono text-xs font-semibold transition-all duration-200 shadow-sm"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Analyze Identity Risk</span>
        </button>
      )}
    </div>
  );
}
