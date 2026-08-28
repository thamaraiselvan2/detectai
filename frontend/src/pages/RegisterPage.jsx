import React, { useState } from 'react';
import { 
  Fingerprint, 
  ArrowLeft, 
  ShieldCheck, 
  AlertCircle, 
  User, 
  Mail, 
  Lock,
  CheckCircle2
} from 'lucide-react';
import { registerUser } from '../api/client';
import SuccessModal from '../components/SuccessModal';

export default function RegisterPage({ onBackToHome }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [registeredData, setRegisteredData] = useState({ username: '', email: '' });

  // Basic email validation regex
  const validateEmail = (val) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const newErrors = {};

    const cleanUsername = username.trim().replace(/^@/, '');
    const cleanEmail = email.trim();

    if (!cleanUsername) {
      newErrors.username = 'Please enter a username.';
    }

    if (!cleanEmail) {
      newErrors.email = 'Please enter your email.';
    } else if (!validateEmail(cleanEmail)) {
      newErrors.email = 'Please enter a valid email address.';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      // Call backend registration endpoint
      await registerUser({
        username: cleanUsername,
        email: cleanEmail,
        display_name: cleanUsername
      });

      // Set registered record and trigger success popup
      setRegisteredData({ username: cleanUsername, email: cleanEmail });
      setShowSuccessModal(true);

      // Reset form fields
      setUsername('');
      setEmail('');
    } catch (err) {
      console.error('Registration error:', err);
      if (err.response?.status === 409) {
        setErrors({
          form: `Username '@${cleanUsername}' is already registered as a protected identity.`
        });
      } else {
        setErrors({
          form: err.response?.data?.message || 'Failed to complete registration. Please try again.'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      
      {/* Navigation / Back Button */}
      <button
        onClick={onBackToHome}
        className="inline-flex items-center gap-2 text-sm font-mono text-emerald-400 hover:text-emerald-300 transition-colors mb-6 group cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span>Back to Home</span>
      </button>

      {/* Page Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <Fingerprint className="w-3.5 h-3.5" />
          <span>IDENTITY PROTECTION</span>
        </div>
        
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight font-sans mb-3">
          REGISTER &amp; PROTECT YOUR PROFILE
        </h1>
        
        <p className="text-slate-400 text-sm sm:text-base max-w-lg mx-auto">
          Register your username and email to record your genuine identity in the security protection vault.
        </p>
      </div>

      {/* Registration Card Form */}
      <div className="bg-slate-900/90 border border-slate-800 focus-within:border-emerald-500/50 rounded-2xl p-6 sm:p-8 shadow-xl backdrop-blur-md transition-all">
        
        {/* Form-level error */}
        {errors.form && (
          <div className="mb-6 p-3.5 rounded-xl bg-red-950/40 border border-red-800/60 flex items-center gap-2 text-xs font-mono text-red-300">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errors.form}</span>
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-6">
          
          {/* Field 1: Username */}
          <div>
            <label 
              htmlFor="register-username" 
              className="block text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-2"
            >
              Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <span className="font-mono text-emerald-400 font-bold text-sm">@</span>
              </div>
              <input
                type="text"
                id="register-username"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  if (errors.username) setErrors(prev => ({ ...prev, username: null }));
                }}
                placeholder="enter the username"
                className={`w-full pl-9 pr-4 py-3.5 rounded-xl bg-slate-950/80 border text-white placeholder-slate-400 font-mono text-sm sm:text-base focus:outline-none focus:ring-2 transition-all ${
                  errors.username 
                    ? 'border-red-500/80 focus:ring-red-500/30' 
                    : 'border-slate-800 focus:ring-emerald-500/30 focus:border-emerald-500'
                }`}
              />
            </div>
            {errors.username && (
              <p className="mt-1.5 text-xs font-mono text-red-400 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{errors.username}</span>
              </p>
            )}
          </div>

          {/* Field 2: Email ID */}
          <div>
            <label 
              htmlFor="register-email" 
              className="block text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-2"
            >
              Email ID
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Mail className="w-4 h-4 text-emerald-400" />
              </div>
              <input
                type="email"
                id="register-email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors(prev => ({ ...prev, email: null }));
                }}
                placeholder="enter your email"
                className={`w-full pl-10 pr-4 py-3.5 rounded-xl bg-slate-950/80 border text-white placeholder-slate-400 font-mono text-sm sm:text-base focus:outline-none focus:ring-2 transition-all ${
                  errors.email 
                    ? 'border-red-500/80 focus:ring-red-500/30' 
                    : 'border-slate-800 focus:ring-emerald-500/30 focus:border-emerald-500'
                }`}
              />
            </div>
            {errors.email && (
              <p className="mt-1.5 text-xs font-mono text-red-400 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{errors.email}</span>
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm tracking-wide transition-all shadow-md hover:shadow-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer pt-3.5 pb-3.5"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                <span>Registering...</span>
              </>
            ) : (
              <>
                <Fingerprint className="w-4 h-4 stroke-[2.2]" />
                <span>Register</span>
              </>
            )}
          </button>
        </form>

        {/* Protection Note */}
        <div className="mt-6 pt-5 border-t border-slate-800 text-xs text-slate-400 flex items-start gap-2.5">
          <Lock className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <span>
            Registering binds your username and email as a genuine profile identity reference in the detection vault.
          </span>
        </div>

      </div>

      {/* Success Popup Modal */}
      <SuccessModal
        isOpen={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        username={registeredData.username}
        email={registeredData.email}
      />

    </div>
  );
}
