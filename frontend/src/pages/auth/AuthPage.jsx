import { useState } from 'react'
import { useNavigate, useLocation, Link, useSearchParams } from 'react-router-dom'
import {
  Briefcase, Mail, Lock, Eye, EyeOff, AlertCircle,
  User, CheckCircle, Sparkles
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import api from '../../api/axiosConfig'

/* ── Google SVG ──────────────────────────────────────────────────────────── */
const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
)

/* ── Tab button ──────────────────────────────────────────────────────────── */
const Tab = ({ active, onClick, children }) => (
  <button
    type="button"
    onClick={onClick}
    className={`flex-1 py-2.5 text-sm font-bold rounded-xl transition-all duration-200 ${
      active
        ? 'bg-gray-900 text-white shadow-sm'
        : 'text-gray-500 hover:text-gray-800'
    }`}
  >
    {children}
  </button>
)

/* ── AuthPage ────────────────────────────────────────────────────────────── */
const AuthPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { login, setUser } = useAuth()

  // If path is /register, default to register tab
  const defaultTab = location.pathname === '/register' ? 'register' : 'login'
  const [tab, setTab] = useState(defaultTab)

  // Shared
  const [error, setError] = useState(() => {
    const err = searchParams.get('error')
    if (err === 'oauth_failed') return 'Google sign-in failed. Please try again.'
    if (err === 'no_token') return 'Authentication error. Please try again.'
    return ''
  })
  const [googleLoading, setGoogleLoading] = useState(false)

  // Login state
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [loginLoading, setLoginLoading] = useState(false)
  const [showLoginPwd, setShowLoginPwd] = useState(false)

  // Register state
  const [regForm, setRegForm] = useState({
    firstName: '', lastName: '', email: '', password: '', confirmPassword: '',
    role: 'FREELANCER',
  })
  const [regLoading, setRegLoading] = useState(false)
  const [showRegPwd, setShowRegPwd] = useState(false)

  // Google role for OAuth
  const role = (searchParams.get('role') || regForm.role || 'FREELANCER').toUpperCase()

  /* ── Handlers ─────────────────────────────────────────────────────────── */
  const handleGoogleSignIn = async () => {
    setGoogleLoading(true)
    setError('')
    try {
      const resp = await api.get(`/users/auth/google/?role=${role}`)
      window.location.href = resp.data.auth_url
    } catch {
      setError('Could not connect to Google. Please try again.')
      setGoogleLoading(false)
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginLoading(true)
    setError('')
    try {
      const user = await login(loginForm.email, loginForm.password)
      navigate(user?.role === 'CLIENT' ? '/client/home' : '/freelancer/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    if (regForm.password !== regForm.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (regForm.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setRegLoading(true)
    try {
      await api.post('/users/register/', {
        email: regForm.email,
        password: regForm.password,
        password_confirm: regForm.confirmPassword,
        role: regForm.role,
        first_name: regForm.firstName,
        last_name: regForm.lastName,
      })
      // Auto-login after registration
      try {
        const user = await login(regForm.email, regForm.password)
        navigate(user?.role === 'CLIENT' ? '/client/onboarding' : '/freelancer/onboarding')
      } catch {
        // If auto-login fails, go to login tab
        setTab('login')
        setLoginForm({ email: regForm.email, password: '' })
        setError('')
      }
    } catch (err) {
      const data = err.response?.data
      let msg = 'Registration failed. Please try again.'
      if (data?.email) msg = `Email: ${Array.isArray(data.email) ? data.email[0] : data.email}`
      else if (data?.password) msg = `Password: ${Array.isArray(data.password) ? data.password[0] : data.password}`
      else if (data?.detail) msg = data.detail
      else if (data?.error) msg = data.error
      setError(msg)
    } finally {
      setRegLoading(false)
    }
  }

  /* ── Render ───────────────────────────────────────────────────────────── */
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-7">
          <Link to="/" className="inline-flex items-center gap-2.5 mb-5 group">
            <img src="/logo.png" alt="FreelanceFlow" className="w-11 h-11 object-contain transition-transform group-hover:scale-105" />
            <span className="text-2xl font-black text-gray-900 tracking-tight">
              Freelance<span className="text-indigo-600">Flow</span>
            </span>
          </Link>
          <h1 className="text-2xl font-extrabold text-gray-900">
            {tab === 'login' ? 'Welcome back' : 'Create your account'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {tab === 'login'
              ? "Sign in to your FreelanceFlow account"
              : "Join thousands of freelancers & clients"}
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-7">

          {/* Tab switcher */}
          <div className="flex gap-1.5 bg-gray-100 p-1 rounded-xl mb-6">
            <Tab active={tab === 'login'} onClick={() => { setTab('login'); setError('') }}>
              Sign In
            </Tab>
            <Tab active={tab === 'register'} onClick={() => { setTab('register'); setError('') }}>
              Create Account
            </Tab>
          </div>

          {/* Error banner */}
          {error && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-5">
              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Google button */}
          <button
            id={tab === 'login' ? 'google-signin-btn' : 'google-register-btn'}
            type="button"
            onClick={handleGoogleSignIn}
            disabled={googleLoading || loginLoading || regLoading}
            className="w-full flex items-center justify-center gap-2.5 py-2.5 px-4 border border-gray-200 rounded-xl text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-60 mb-5"
          >
            {googleLoading
              ? <span className="w-4 h-4 border-2 border-gray-300 border-t-indigo-500 rounded-full animate-spin" />
              : <GoogleIcon />
            }
            {googleLoading ? 'Redirecting…' : `Continue with Google`}
          </button>

          {/* Divider */}
          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-100" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-xs text-gray-400 font-medium uppercase tracking-wider">
                or with email
              </span>
            </div>
          </div>

          {/* ── LOGIN FORM ─────────────────────────────────────────────── */}
          {tab === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5" htmlFor="login-email">
                  Email address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="login-email"
                    type="email"
                    name="email"
                    value={loginForm.email}
                    onChange={e => setLoginForm({ ...loginForm, email: e.target.value })}
                    required
                    placeholder="you@example.com"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm text-gray-900 placeholder-gray-400"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-bold uppercase tracking-wider text-gray-600" htmlFor="login-password">
                    Password
                  </label>
                  <a href="#" className="text-xs text-gray-500 hover:text-gray-800 font-medium">
                    Forgot password?
                  </a>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="login-password"
                    type={showLoginPwd ? 'text' : 'password'}
                    name="password"
                    value={loginForm.password}
                    onChange={e => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                    placeholder="Enter your password"
                    className="w-full pl-10 pr-11 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm text-gray-900 placeholder-gray-400"
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowLoginPwd(!showLoginPwd)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showLoginPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                id="login-submit"
                type="submit"
                disabled={loginLoading || googleLoading}
                className="w-full bg-gray-900 hover:bg-black text-white py-2.5 rounded-xl font-bold text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed mt-2"
              >
                {loginLoading
                  ? <span className="flex items-center justify-center gap-2"><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Signing in…</span>
                  : 'Sign In'
                }
              </button>

              <p className="text-center text-xs text-gray-500 pt-1">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setTab('register'); setError('') }}
                  className="text-gray-900 font-bold hover:underline"
                >
                  Create one free
                </button>
              </p>
            </form>
          )}

          {/* ── REGISTER FORM ──────────────────────────────────────────── */}
          {tab === 'register' && (
            <form onSubmit={handleRegister} className="space-y-3.5">

              {/* Role picker */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-2">
                  I want to…
                </label>
                <div className="grid grid-cols-2 gap-2.5">
                  {[
                    { value: 'FREELANCER', label: 'Find Work', sub: 'Freelancer' },
                    { value: 'CLIENT',     label: 'Hire Talent', sub: 'Client' },
                  ].map(r => (
                    <button
                      key={r.value}
                      type="button"
                      onClick={() => setRegForm({ ...regForm, role: r.value })}
                      className={`flex flex-col items-start p-3 rounded-xl border-2 text-left transition-all ${
                        regForm.role === r.value
                          ? 'border-gray-900 bg-gray-900 text-white'
                          : 'border-gray-200 hover:border-gray-400 text-gray-700'
                      }`}
                    >
                      <span className="text-xs font-bold">{r.label}</span>
                      <span className={`text-[10px] ${regForm.role === r.value ? 'text-gray-300' : 'text-gray-500'}`}>{r.sub}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Name row */}
              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5" htmlFor="reg-first">
                    First name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      id="reg-first"
                      type="text"
                      value={regForm.firstName}
                      onChange={e => setRegForm({ ...regForm, firstName: e.target.value })}
                      placeholder="Jane"
                      className="w-full pl-10 pr-3 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm text-gray-900 placeholder-gray-400"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5" htmlFor="reg-last">
                    Last name
                  </label>
                  <input
                    id="reg-last"
                    type="text"
                    value={regForm.lastName}
                    onChange={e => setRegForm({ ...regForm, lastName: e.target.value })}
                    placeholder="Doe"
                    className="w-full px-3 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm text-gray-900 placeholder-gray-400"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5" htmlFor="reg-email">
                  Email address <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="reg-email"
                    type="email"
                    value={regForm.email}
                    onChange={e => setRegForm({ ...regForm, email: e.target.value })}
                    required
                    placeholder="you@example.com"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm text-gray-900 placeholder-gray-400"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5" htmlFor="reg-password">
                  Password <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="reg-password"
                    type={showRegPwd ? 'text' : 'password'}
                    value={regForm.password}
                    onChange={e => setRegForm({ ...regForm, password: e.target.value })}
                    required
                    placeholder="Min. 8 characters"
                    className="w-full pl-10 pr-11 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm text-gray-900 placeholder-gray-400"
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowRegPwd(!showRegPwd)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showRegPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm password */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5" htmlFor="reg-confirm">
                  Confirm password <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    id="reg-confirm"
                    type={showRegPwd ? 'text' : 'password'}
                    value={regForm.confirmPassword}
                    onChange={e => setRegForm({ ...regForm, confirmPassword: e.target.value })}
                    required
                    placeholder="Repeat password"
                    className="w-full pl-10 pr-11 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm text-gray-900 placeholder-gray-400"
                  />
                  {regForm.confirmPassword && regForm.password === regForm.confirmPassword && (
                    <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-500" />
                  )}
                </div>
              </div>

              <button
                id="register-submit"
                type="submit"
                disabled={regLoading || googleLoading}
                className="w-full bg-gray-900 hover:bg-black text-white py-2.5 rounded-xl font-bold text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed mt-1"
              >
                {regLoading
                  ? <span className="flex items-center justify-center gap-2"><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Creating account…</span>
                  : <span className="flex items-center justify-center gap-2"><Sparkles className="w-4 h-4" /> Create Account — It's Free</span>
                }
              </button>

              <p className="text-center text-xs text-gray-500 pt-1">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setTab('login'); setError('') }}
                  className="text-gray-900 font-bold hover:underline"
                >
                  Sign in
                </button>
              </p>

              <p className="text-center text-[10px] text-gray-400 leading-relaxed">
                By creating an account you agree to our{' '}
                <a href="#" className="underline hover:text-gray-600">Terms</a>
                {' '}and{' '}
                <a href="#" className="underline hover:text-gray-600">Privacy Policy</a>.
              </p>
            </form>
          )}
        </div>

        <p className="text-center text-sm text-gray-400 mt-5">
          <Link to="/" className="hover:text-gray-600 transition-colors">
            ← Back to home
          </Link>
        </p>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default AuthPage
