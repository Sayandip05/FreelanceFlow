import { useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import { Briefcase, Mail, Lock, Eye, EyeOff, AlertCircle, CheckCircle2, ArrowLeft } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import api from '../../api/axiosConfig'
import { authAPI } from '../../api/auth'
import OtpVerificationModal from '../../components/auth/OtpVerificationModal'


/* ── Google "G" SVG Logo ──────────────────────────────────────────────────── */
const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
)


// Role comes from landing page query param
const LoginPage = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login } = useAuth()

  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)

  // Forgot password & OTP states
  const [forgotModalOpen, setForgotModalOpen] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotNotice, setForgotNotice] = useState('')
  const [otpModalOpen, setOtpModalOpen] = useState(false)
  const [otpCooldown, setOtpCooldown] = useState(30)

  const [error, setError] = useState(() => {
    const err = searchParams.get('error')
    if (err === 'oauth_failed') return 'Google sign-in failed. Please try again.'
    if (err === 'no_token') return 'Authentication error. Please try again.'
    return ''
  })

  const handleForgotPasswordSubmit = async (e) => {
    e.preventDefault()
    if (!forgotEmail) return
    setForgotLoading(true)
    setError('')
    try {
      const resp = await authAPI.initiatePasswordResetOtp(forgotEmail)
      setForgotModalOpen(false)
      setOtpCooldown(resp.data?.cooldown || 30)
      setOtpModalOpen(true)
    } catch (err) {
      const data = err.response?.data
      setError(data?.email || data?.detail || data?.error || 'Failed to send password reset code. Please check the email.')
    } finally {
      setForgotLoading(false)
    }
  }


  // Role comes from the landing page link e.g. /login?role=CLIENT
  const role = (searchParams.get('role') || 'CLIENT').toUpperCase()

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const user = await login(form.email, form.password)
      navigate(user?.role === 'CLIENT' ? '/client/home' : '/freelancer/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setGoogleLoading(true)
    setError('')
    try {
      const resp = await api.get(`/users/auth/google/?role=${role}`)
      window.location.href = resp.data.auth_url
    } catch (err) {
      console.error('Google Auth Init Error:', err)
      setError(err.response?.data?.detail || err.response?.data?.error || 'Could not connect to Google. Please try again.')
      setGoogleLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">

        {/* ── Logo ─────────────────────────────────────────────────────────── */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2.5 mb-6 group">
            <img src="/logo.png" alt="FreelanceFlow" className="w-11 h-11 object-contain transition-transform group-hover:scale-105" />
            <span className="text-2xl font-black text-gray-900 tracking-tight">
              Freelance<span className="text-primary-600">Flow</span>
            </span>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome back</h1>
          <p className="text-gray-500 text-sm">Sign in to your account to continue</p>
        </div>

        {/* ── Card ─────────────────────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">

          {/* Error banner */}
          {error && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-6">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Success banner */}
          {forgotNotice && (
            <div className="flex items-start gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3 mb-6">
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-700">{forgotNotice}</p>
            </div>
          )}

          {/* ── Google Sign-In Button ───────────────────────────────────────── */}
          <button
            id="google-signin-btn"
            type="button"
            onClick={handleGoogleSignIn}
            disabled={googleLoading || loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              width: '100%',
              padding: '11px 16px',
              border: '1.5px solid #e2e8f0',
              borderRadius: '12px',
              backgroundColor: '#fff',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151',
              transition: 'background 0.15s, box-shadow 0.15s',
              boxShadow: '0 1px 2px rgba(0,0,0,0.06)',
              marginBottom: '20px',
              opacity: (googleLoading || loading) ? 0.6 : 1,
            }}
            onMouseEnter={e => { if (!googleLoading && !loading) e.currentTarget.style.backgroundColor = '#f8fafc' }}
            onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#fff' }}
          >
            {googleLoading ? (
              <span
                style={{
                  width: 20, height: 20,
                  border: '2px solid #cbd5e1',
                  borderTopColor: '#6366f1',
                  borderRadius: '50%',
                  animation: 'spin 0.7s linear infinite',
                  flexShrink: 0,
                }}
              />
            ) : (
              <GoogleIcon />
            )}
            <span>{googleLoading ? 'Redirecting to Google…' : 'Continue with Google'}</span>
          </button>

          {/* ── Divider ─────────────────────────────────────────────────────── */}
          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-100" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-xs text-gray-400 font-medium tracking-wide uppercase">
                or sign in with email
              </span>
            </div>
          </div>

          {/* ── Email / Password Form ───────────────────────────────────────── */}
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5" htmlFor="login-email">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="login-email"
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                  placeholder="you@example.com"
                  className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900 placeholder-gray-400 text-sm"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-gray-700" htmlFor="login-password">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setForgotModalOpen(true)
                    setForgotEmail(form.email)
                    setError('')
                  }}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  placeholder="Enter your password"
                  className="w-full pl-11 pr-11 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900 placeholder-gray-400 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Sign In button */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading || googleLoading}
              className="w-full btn-primary py-3 text-sm font-semibold disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Signing in…
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Register link */}
          <p className="text-center text-sm text-gray-500 mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-600 hover:text-primary-700 font-semibold">
              Create one free
            </Link>
          </p>
        </div>

        {/* Back to home */}
        <p className="text-center text-sm text-gray-400 mt-5">
          <Link to="/" className="hover:text-gray-600 transition-colors">
            ← Back to home
          </Link>
        </p>
      </div>

      {/* ── Forgot Password Request Modal ── */}
      {forgotModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 sm:p-8 text-gray-900">
            <button
              type="button"
              onClick={() => setForgotModalOpen(false)}
              className="absolute top-5 right-5 p-1.5 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 rotate-180" />
            </button>
            <h2 className="text-xl font-bold text-gray-900 mb-6">Forgot Password</h2>
            <form onSubmit={handleForgotPasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 outline-none text-sm shadow-2xs"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={forgotLoading || !forgotEmail}
                className="w-full btn-primary py-3 px-4 rounded-xl font-bold text-sm transition-all shadow-md active:scale-98"
              >
                {forgotLoading ? 'Sending OTP...' : 'Send Reset Code'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── OTP Verification Modal ── */}
      <OtpVerificationModal
        isOpen={otpModalOpen}
        onClose={() => setOtpModalOpen(false)}
        email={forgotEmail}
        flow="password_reset"
        initialCooldown={otpCooldown}
        onSuccess={() => {
          setOtpModalOpen(false)
          setForgotNotice('Password reset successfully! Please sign in with your new password.')
          setForm((prev) => ({ ...prev, email: forgotEmail, password: '' }))
        }}
      />

      {/* Keyframe for spinner (only needed if Tailwind animate-spin isn't available inline) */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}


export default LoginPage
