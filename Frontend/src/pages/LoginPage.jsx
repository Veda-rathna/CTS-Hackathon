import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  Lock,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  KeyRound,
  Info,
  RefreshCw,
} from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [errors, setErrors] = useState({});
  const [showDemoHelp, setShowDemoHelp] = useState(false);

  // Redirect destination after authentication (defaults to Dashboard "/")
  const from = location.state?.from?.pathname || '/';

  const validateForm = () => {
    const nextErrors = {};
    if (!username.trim()) {
      nextErrors.username = 'Provider username is required';
    }
    if (!password) {
      nextErrors.password = 'Provider password is required';
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const res = await login(username, password);
      if (res.success) {
        navigate(from, { replace: true });
      } else {
        setErrorMessage(
          res.error || 'Invalid provider credentials. Please verify your username and password.'
        );
      }
    } catch (err) {
      setErrorMessage('Authentication service temporarily unavailable. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col justify-between">
      {/* Top Application Brand Header */}
      <header className="h-16 bg-white/95 backdrop-blur-sm border-b border-slate-200/90 flex items-center justify-between px-5 sm:px-8 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-blue-500 flex items-center justify-center text-white shadow-md shadow-sky-900/20 ring-1 ring-slate-900/10">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-extrabold text-slate-900 tracking-tight">PA Intelligence</span>
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-sky-50 text-sky-700 border border-sky-200">
                v2.0
              </span>
            </div>
            <span className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">
              Enterprise UM Companion
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wider uppercase bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1.5 shadow-2xs">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-600" />
            <span>Provider Access</span>
          </span>
        </div>
      </header>

      {/* Main Authentication Canvas */}
      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-12">
        <div className="w-full max-w-[460px] healthcare-card p-6 sm:p-8 bg-white border border-slate-200/90 shadow-sm">
          {/* Card Header */}
          <div className="flex items-center gap-3 pb-4 mb-5 border-b border-slate-100">
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center flex-shrink-0 border border-sky-100">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
                Provider Sign In
              </h2>
              <p className="text-xs text-slate-500 leading-tight">
                Sign in with your authorized provider credentials to access the Prior Authorization platform.
              </p>
            </div>
          </div>

          {/* Error Message Box */}
          {errorMessage && (
            <div
              className="mb-5 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5 animate-fadeIn"
              role="alert"
            >
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div className="font-medium leading-relaxed">{errorMessage}</div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Username Field */}
            <div>
              <label
                htmlFor="provider-username"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Provider Username <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  id="provider-username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  autoFocus
                  placeholder="provider1@pa-demo.local"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (errors.username) setErrors((prev) => ({ ...prev, username: null }));
                  }}
                  disabled={isSubmitting}
                  className={`w-full pl-9 pr-3 py-2.5 rounded-lg border ${
                    errors.username
                      ? 'border-rose-400 bg-rose-50/40 text-rose-900'
                      : 'border-slate-200 text-slate-900 bg-white focus:border-sky-600'
                  } placeholder-slate-400 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-all`}
                  aria-invalid={!!errors.username}
                  aria-describedby={errors.username ? 'username-error' : undefined}
                />
              </div>
              {errors.username && (
                <p id="username-error" className="text-[11px] text-rose-600 font-medium mt-1">
                  {errors.username}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="provider-password"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Provider Password <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="provider-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errors.password) setErrors((prev) => ({ ...prev, password: null }));
                  }}
                  disabled={isSubmitting}
                  className={`w-full pl-9 pr-10 py-2.5 rounded-lg border ${
                    errors.password
                      ? 'border-rose-400 bg-rose-50/40 text-rose-900'
                      : 'border-slate-200 text-slate-900 bg-white focus:border-sky-600'
                  } placeholder-slate-400 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-all`}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p id="password-error" className="text-[11px] text-rose-600 font-medium mt-1">
                  {errors.password}
                </p>
              )}
            </div>

            {/* Sign In CTA */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-lg bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-sky-500/30 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Authenticating provider...</span>
                  </>
                ) : (
                  <span>Sign In</span>
                )}
              </button>
            </div>
          </form>

          {/* Access Note / Policy */}
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-start gap-2.5 text-[11px] text-slate-500 leading-relaxed">
            <ShieldCheck className="w-4 h-4 text-sky-700 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-700">Authorized Provider Access: </span>
              <span>
                This clinical review environment is restricted to authorized healthcare providers and clinical reviewers. Patient access is not supported.
              </span>
            </div>
          </div>
        </div>
      </main>

      {/* Minimal Enterprise Footer */}
      <footer className="w-full max-w-7xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500 border-t border-slate-200/90">
        <div>Prior Authorization Intelligence Enterprise System &copy; 2026. All rights reserved.</div>

        {/* Subtle Demo Info Popover Toggle */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowDemoHelp(!showDemoHelp)}
            className="text-slate-600 hover:text-sky-700 transition-colors flex items-center gap-1 underline underline-offset-4 decoration-slate-300 hover:decoration-sky-700 text-[11px] font-medium"
          >
            <Info className="w-3 h-3 text-slate-500" />
            <span>Demo environment info</span>
          </button>

          {showDemoHelp && (
            <div className="absolute bottom-7 right-0 sm:right-0 w-72 p-3.5 bg-white border border-slate-200 rounded-xl shadow-xl text-slate-700 text-[11px] space-y-2 z-30 animate-fadeIn">
              <div className="font-bold text-slate-900 flex items-center gap-1.5 pb-1.5 border-b border-slate-100">
                <KeyRound className="w-3.5 h-3.5 text-sky-700" />
                <span>Demo Reviewer Credentials</span>
              </div>
              <p className="text-[10px] text-slate-500">
                For hackathon evaluation, enter one of the authorized provider accounts:
              </p>
              <div className="space-y-1 font-mono text-[10px] bg-slate-50 p-2 rounded-lg border border-slate-200">
                <div>
                  <span className="text-slate-500">User: </span>
                  <span className="text-sky-800 font-semibold">provider1@pa-demo.local</span>
                </div>
                <div>
                  <span className="text-slate-500">Pass: </span>
                  <span className="text-slate-700 font-semibold">Provider@123</span>
                </div>
              </div>
              <div className="space-y-1 font-mono text-[10px] bg-slate-50 p-2 rounded-lg border border-slate-200">
                <div>
                  <span className="text-slate-500">User: </span>
                  <span className="text-sky-800 font-semibold">provider2@pa-demo.local</span>
                </div>
                <div>
                  <span className="text-slate-500">Pass: </span>
                  <span className="text-slate-700 font-semibold">Provider@456</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}
