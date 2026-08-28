import React, { useState } from 'react';
import { 
  Search, 
  ShieldCheck, 
  ShieldAlert, 
  AlertCircle, 
  ArrowLeft, 
  CheckCircle2, 
  XCircle, 
  Users, 
  Calendar, 
  Info,
  HelpCircle
} from 'lucide-react';
import { checkProfile } from '../api/client';

export default function InstantSearchPage({ onBackToHome }) {
  const [usernameInput, setUsernameInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Pre-configured demo profiles for quick testing convenience
  const quickDemoExamples = [
    { handle: 'elonmusk', label: 'Authentic Official' },
    { handle: 'elonmusk_official', label: 'Crypto Phishing Clone' },
    { handle: 'elon_muskk', label: 'Typosquat Handle' },
    { handle: 'satya_nadella_support', label: 'Helpdesk Spoof' },
    { handle: 'crypto_profit_bot99', label: 'Spam Follower Bot' },
    { handle: 'alex_tech_dev', label: 'Everyday Developer' },
  ];

  const handleSearch = async (targetHandle) => {
    const query = (targetHandle !== undefined ? targetHandle : usernameInput).trim();
    if (!query) {
      setErrorMsg('Please enter a username to check.');
      return;
    }

    setErrorMsg('');
    setLoading(true);
    setResult(null);
    setNotFound(false);

    try {
      // Calls the backend endpoint to search demo profile records
      const cleanHandle = query.replace(/^@/, '').trim();
      const res = await checkProfile({ username: cleanHandle, demo_only: true });

      if (res.status === 'success' && res.found_in_demo && res.profile) {
        setResult({
          profile: res.profile,
          analysis: res.analysis,
          classification: res.classification,
          riskScore: res.risk_score,
          reasons: res.reasons,
          similarProfiles: res.similar_profiles || []
        });
      } else if (res.status === 'not_found' || !res.found_in_demo) {
        setNotFound(true);
      } else {
        setErrorMsg('The detection server returned an invalid profile result. Please try again.');
      }
    } catch (err) {
      console.error('Error checking profile:', err);
      // In case of 404 or backend not found
      if (err.response && err.response.status === 404) {
        setNotFound(true);
      } else {
        setErrorMsg(err.response?.data?.message || 'Failed to connect to detection server. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  const isReal = result?.classification === 'REAL';
  const statusText = result?.classification || '';

  // Format understandable reasons
  const getSimpleReasons = () => {
    if (!result) return [];
    return result.reasons?.length ? result.reasons : ['No significant risk signals were found in the demo database.'];
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      
      {/* Navigation / Back Button */}
      <button
        onClick={onBackToHome}
        className="inline-flex items-center gap-2 text-sm font-mono text-cyan-400 hover:text-cyan-300 transition-colors mb-6 group cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span>Back to Home</span>
      </button>

      {/* Page Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono mb-3">
          <Search className="w-3.5 h-3.5" />
          <span>DEMO DATASET LOOKUP</span>
        </div>
        
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight font-sans mb-3">
          Instant Profile Search
        </h1>
        
        <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto">
          Verify usernames against the existing demo database to evaluate profile authenticity and potential impersonation.
        </p>
      </div>

      {/* Search Input Card */}
      <div className="bg-slate-900/90 border border-slate-800 focus-within:border-cyan-500/50 rounded-2xl p-4 sm:p-6 shadow-xl mb-8 backdrop-blur-md transition-all">
        <form onSubmit={(e) => { e.preventDefault(); handleSearch(); }} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
              <span className="font-mono text-cyan-400 text-base font-bold">@</span>
            </div>
            <input
              type="text"
              id="username-search-input"
              value={usernameInput}
              onChange={(e) => {
                setUsernameInput(e.target.value);
                if (errorMsg) setErrorMsg('');
              }}
              onKeyDown={handleKeyDown}
              placeholder="enter the username"
              className="w-full pl-9 pr-4 py-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500 font-mono text-sm sm:text-base transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="py-3.5 px-8 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm tracking-wide transition-all shadow-md hover:shadow-cyan-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer shrink-0"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                <span>Checking...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4 stroke-[2.5]" />
                <span>Check</span>
              </>
            )}
          </button>
        </form>

        {/* Validation Error */}
        {errorMsg && (
          <div className="mt-3 flex items-center gap-2 text-xs font-mono text-red-400 animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Quick Demo Examples */}
        <div className="mt-5 pt-4 border-t border-slate-800/80">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2 font-mono">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Try an existing demo username:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {quickDemoExamples.map((item) => (
              <button
                key={item.handle}
                type="button"
                onClick={() => {
                  setUsernameInput(item.handle);
                  handleSearch(item.handle);
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-cyan-500/15 text-slate-300 hover:text-cyan-300 border border-slate-700/60 hover:border-cyan-500/40 text-xs font-mono transition-colors cursor-pointer"
              >
                @{item.handle}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* RESULT 1: Profile Found */}
      {result && (
        <div className={`rounded-2xl border p-6 sm:p-8 backdrop-blur-md shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300 ${
          isReal 
            ? 'bg-slate-900/90 border-emerald-500/40 shadow-glow-green' 
            : 'bg-slate-900/90 border-red-500/40 shadow-glow-red'
        }`}>
          
          {/* Header Status & Username */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div className="flex items-start gap-4">
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 border ${
                isReal 
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' 
                  : 'bg-red-500/20 text-red-400 border-red-500/40'
              }`}>
                {isReal ? (
                  <ShieldCheck className="w-8 h-8 stroke-[2.2]" />
                ) : (
                  <ShieldAlert className="w-8 h-8 stroke-[2.2]" />
                )}
              </div>

              <div>
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block mb-1">
                  Profile Status
                </span>
                <span className={`text-xl sm:text-2xl font-bold font-mono tracking-tight ${
                  isReal ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {statusText} / {result.riskScore}/100
                </span>
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-sm font-mono text-cyan-300 font-semibold">
                    Username: @{result.profile?.username}
                  </span>
                  {result.profile?.is_verified ? (
                    <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 text-[10px] font-mono">
                      VERIFIED
                    </span>
                  ) : null}
                </div>
              </div>
            </div>

            {/* Quick Profile Summary Badge */}
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-xs font-mono text-slate-300 space-y-1">
              <div><span className="text-slate-400">Display Name:</span> {result.profile?.display_name || 'N/A'}</div>
              <div><span className="text-slate-400">Followers:</span> {result.profile?.followers_count?.toLocaleString() ?? 0}</div>
              <div><span className="text-slate-400">Account Age:</span> {result.profile?.account_age_days ? `${result.profile.account_age_days} days` : 'N/A'}</div>
            </div>
          </div>

          {/* Profile Bio (if exists) */}
          {result.profile?.bio && (
            <div className="py-4 border-b border-slate-800 text-xs sm:text-sm text-slate-300">
              <span className="text-slate-400 font-mono block text-xs mb-1">Bio / Profile Description:</span>
              <p className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 italic">
                "{result.profile.bio}"
              </p>
            </div>
          )}

          {/* Reasons Section */}
          <div className="pt-6">
            <h3 className="text-sm font-mono uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
              <span>Reasons:</span>
            </h3>

            <div className="space-y-2.5">
              {getSimpleReasons().map((reason, idx) => (
                <div 
                  key={idx}
                  className={`flex items-start gap-3 p-3 rounded-xl border text-xs sm:text-sm ${
                    isReal 
                      ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-200' 
                      : 'bg-red-950/20 border-red-800/40 text-red-200'
                  }`}
                >
                  {isReal ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  )}
                  <span className="leading-relaxed">{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {result.similarProfiles?.length > 0 && (
            <div className="pt-6 mt-6 border-t border-slate-800">
              <h3 className="text-sm font-mono uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                <Users className="w-4 h-4 text-cyan-400" />
                <span>Similar profiles in demo database</span>
              </h3>
              <div className="space-y-2.5">
                {result.similarProfiles.map((profile) => (
                  <div key={profile.id} className="flex items-center justify-between gap-3 p-3 rounded-xl border border-slate-800 bg-slate-950/50">
                    <div className="flex items-center gap-3 min-w-0">
                      {profile.avatar_url ? <img src={profile.avatar_url} alt="" className="w-9 h-9 rounded-full object-cover shrink-0" /> : <div className="w-9 h-9 rounded-full bg-slate-800 shrink-0" />}
                      <div className="min-w-0">
                        <div className="text-sm text-cyan-300 font-mono truncate">@{profile.username}</div>
                        <div className="text-xs text-slate-400 truncate">{profile.display_name}</div>
                      </div>
                    </div>
                    <span className="text-xs font-mono text-slate-300 shrink-0">{profile.similarity_score}% match</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}

      {/* RESULT 2: Not Found in Demo Data */}
      {notFound && (
        <div className="bg-slate-900/90 border border-slate-700/70 rounded-2xl p-6 sm:p-8 backdrop-blur-md text-center shadow-xl animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="w-14 h-14 rounded-2xl bg-slate-800 border border-slate-700 mx-auto flex items-center justify-center text-slate-400 mb-4">
            <HelpCircle className="w-7 h-7" />
          </div>

          <h3 className="text-xl font-bold text-white mb-2 font-mono">
            Profile not found in demo data.
          </h3>

          <p className="text-sm text-slate-400 max-w-md mx-auto mb-6 leading-relaxed">
            The username you entered is not present in our current demo database. Unknown profiles are not automatically flagged as fake.
          </p>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 max-w-md mx-auto text-left text-xs font-mono text-slate-400">
            <div className="font-semibold text-cyan-400 mb-2">Available Demo Accounts to Test:</div>
            <ul className="space-y-1">
              <li>• <button onClick={() => { setUsernameInput('elonmusk'); handleSearch('elonmusk'); }} className="text-cyan-300 hover:underline">@elonmusk</button> (Authentic / Real)</li>
              <li>• <button onClick={() => { setUsernameInput('elonmusk_official'); handleSearch('elonmusk_official'); }} className="text-cyan-300 hover:underline">@elonmusk_official</button> (Phishing Clone / Fake)</li>
              <li>• <button onClick={() => { setUsernameInput('elon_muskk'); handleSearch('elon_muskk'); }} className="text-cyan-300 hover:underline">@elon_muskk</button> (Typosquat / Fake)</li>
              <li>• <button onClick={() => { setUsernameInput('satya_nadella_support'); handleSearch('satya_nadella_support'); }} className="text-cyan-300 hover:underline">@satya_nadella_support</button> (Spoofed Helpdesk / Fake)</li>
              <li>• <button onClick={() => { setUsernameInput('alex_tech_dev'); handleSearch('alex_tech_dev'); }} className="text-cyan-300 hover:underline">@alex_tech_dev</button> (Benign Developer / Real)</li>
            </ul>
          </div>
        </div>
      )}

    </div>
  );
}
