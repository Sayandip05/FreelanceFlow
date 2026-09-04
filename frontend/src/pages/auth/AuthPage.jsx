'use client'

import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link, useSearchParams } from 'react-router-dom'
import {
  Eye, EyeOff, ArrowLeft, AlertCircle, CheckCircle2, Briefcase, User, X
} from 'lucide-react'

import { useAuth } from '../../context/AuthContext'
import api from '../../api/axiosConfig'
import { authAPI } from '../../api/auth'
import OtpVerificationModal from '../../components/auth/OtpVerificationModal'

export default function AuthPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { login } = useAuth()

  // Determine initial tab from route or query params
  const defaultTab = (location.pathname === '/register' || searchParams.get('error') === 'please_signup_first') ? 'register' : 'login'
  const [tab, setTab] = useState(defaultTab)

  // Errors & Loading States
  const [error, setError] = useState(() => {
    const err = searchParams.get('error')
    if (err === 'please_signup_first') return 'No account found with this Google email. Please sign up first!'
    if (err === 'oauth_failed') return 'Google sign-in failed. Please try again.'
    if (err === 'no_token') return 'Authentication error. Please try again.'
    return ''
  })
  const [googleLoading, setGoogleLoading] = useState(false)
  const [loading, setLoading] = useState(false)

  // OTP Verification Modal State
  const [otpModalOpen, setOtpModalOpen] = useState(false)
  const [otpFlow, setOtpFlow] = useState('registration')
  const [otpEmail, setOtpEmail] = useState('')
  const [otpCooldown, setOtpCooldown] = useState(30)

  // Forgot Password Modal State
  const [forgotModalOpen, setForgotModalOpen] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotNotice, setForgotNotice] = useState('')

  // Login Form State
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
    rememberMe: false
  })
  const [showLoginPassword, setShowLoginPassword] = useState(false)

  // Register Form State
  const [regForm, setRegForm] = useState({
    firstName: '',
    lastName: '',
    email: searchParams.get('email') || '',
    password: '',
    confirmPassword: '',
    role: (searchParams.get('error') === 'please_signup_first' ? '' : (searchParams.get('role') || 'FREELANCER')).toUpperCase(),
  })
  const [showRegPassword, setShowRegPassword] = useState(false)

  // Reset Google loading state on page focus
  useEffect(() => {
    const handleResetLoading = () => setGoogleLoading(false)
    window.addEventListener('pageshow', handleResetLoading)
    window.addEventListener('focus', handleResetLoading)
    document.addEventListener('visibilitychange', handleResetLoading)

    return () => {
      window.removeEventListener('pageshow', handleResetLoading)
      window.removeEventListener('focus', handleResetLoading)
      document.removeEventListener('visibilitychange', handleResetLoading)
    }
  }, [])

  /* ── Google OAuth Sign-in ─────────────────────────────────────────────── */
  const handleGoogleSignIn = async () => {
    if (tab === 'register' && !regForm.role) {
      setError('Please select your role (Freelancer or Client) before signing up with Google.')
      return
    }
    setGoogleLoading(true)
    setError('')
    try {
      const currentRole = (tab === 'register' ? regForm.role : (searchParams.get('role') || 'FREELANCER')).toUpperCase()
      const currentMode = tab === 'register' ? 'register' : 'login'
      const resp = await api.get(`/users/auth/google/?role=${currentRole}&mode=${currentMode}`)
      if (resp.data?.auth_url) {
        window.location.href = resp.data.auth_url
        setTimeout(() => setGoogleLoading(false), 3000)
      } else {
        setGoogleLoading(false)
      }
    } catch (err) {
      console.error('Google Auth Init Error:', err)
      setError(err.response?.data?.detail || err.response?.data?.error || 'Could not connect to Google. Please try again.')
      setGoogleLoading(false)
    }
  }

  /* ── Email/Password Login ─────────────────────────────────────────────── */
  const handleLoginSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const user = await login(loginForm.email, loginForm.password)
      if (!user?.role) {
        setError('User role not found. Please try logging in again.')
        return
      }
      navigate(user.role === 'CLIENT' ? '/client/home' : '/freelancer/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  /* ── Email/Password Register (Initiate OTP) ─────────────────────────── */
  const handleRegisterSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!regForm.role) {
      setError('Please choose whether you want to Find Work (Freelancer) or Hire Talent (Client).')
      return
    }
    if (regForm.password !== regForm.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (regForm.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)
    try {
      const resp = await authAPI.initiateRegisterOtp(
        regForm.email,
        regForm.password,
        regForm.role,
        regForm.firstName,
        regForm.lastName
      )
      setOtpEmail(regForm.email)
      setOtpFlow('registration')
      setOtpCooldown(resp.data?.cooldown || 30)
      setOtpModalOpen(true)
    } catch (err) {
      const data = err.response?.data
      let msg = 'Registration failed. Please try again.'
      if (data?.email) msg = `Email: ${Array.isArray(data.email) ? data.email[0] : data.email}`
      else if (data?.password) msg = `Password: ${Array.isArray(data.password) ? data.password[0] : data.password}`
      else if (data?.detail) msg = data.detail
      else if (data?.error) msg = data.error
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  /* ── Forgot Password Request (Initiate OTP) ──────────────────────────── */
  const handleForgotPasswordSubmit = async (e) => {
    e.preventDefault()
    if (!forgotEmail) return
    setForgotLoading(true)
    setError('')
    try {
      const resp = await authAPI.initiatePasswordResetOtp(forgotEmail)
      setForgotModalOpen(false)
      setOtpEmail(forgotEmail)
      setOtpFlow('password_reset')
      setOtpCooldown(resp.data?.cooldown || 30)
      setOtpModalOpen(true)
    } catch (err) {
      const data = err.response?.data
      setError(data?.email || data?.detail || data?.error || 'Failed to send password reset code. Please check the email.')
    } finally {
      setForgotLoading(false)
    }
  }


  return (
    <div className="min-h-screen w-full bg-white flex">
      {/* ── Left Panel: Brand Asset & Graphic ───────────────────────────── */}
      <div className="hidden lg:block lg:w-[820px] max-w-[50vw] h-screen sticky top-0 relative overflow-hidden bg-[#e8f2fc] border-r border-gray-100">
        {/* Back to Home Button */}
        <div className="absolute top-6 left-6 z-20">
          <button
            onClick={() => navigate('/')}
            className="w-10 h-10 bg-white/90 backdrop-blur-md rounded-full flex items-center justify-center hover:bg-white hover:shadow-md transition-all border border-gray-200/80 text-gray-700 shadow-xs group"
            title="Back to home"
          >
            <ArrowLeft className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" />
          </button>
        </div>

        <img
          src="/images/sign up banner.png"
          alt="FreelanceFlow Visual"
          className="w-full h-full object-cover object-center select-none"
          onError={(e) => {
            e.target.src = "/images/home image.png"
          }}
        />
      </div>



      {/* ── Right Panel: Form Section ───────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center bg-white p-6 sm:p-10 lg:p-12 relative overflow-y-auto">
        {/* Mobile Back Button */}
        <div className="lg:hidden absolute top-6 left-6 z-10">
          <button
            onClick={() => navigate('/')}
            className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center hover:bg-gray-200 transition-all text-gray-700"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
        </div>

        <div className="w-full max-w-md py-6">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mb-2 tracking-tight">
              {tab === 'login' ? 'Welcome Back' : 'Create Account'}
            </h1>
            <p className="text-gray-600 text-sm">
              {tab === 'login' ? (
                <>
                  Don&apos;t have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setTab('register'); setError('') }}
                    className="text-blue-600 hover:text-blue-700 font-semibold"
                  >
                    Sign up
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setTab('login'); setError('') }}
                    className="text-blue-600 hover:text-blue-700 font-semibold"
                  >
                    Sign in
                  </button>
                </>
              )}
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-5 text-sm text-red-700">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <p className="leading-snug">{error}</p>
            </div>
          )}

          {/* Forgot Password Success Notice */}
          {forgotNotice && (
            <div className="flex items-start gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3 mb-5 text-sm text-green-700">
              <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
              <p className="leading-snug">{forgotNotice}</p>
            </div>
          )}

          {/* ── Role Selector (Only for Registration) ────────────────────── */}
          {tab === 'register' && (
            <div className="mb-5 space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                I want to:
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRegForm({ ...regForm, role: 'FREELANCER' })}
                  className={`p-3 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
                    regForm.role === 'FREELANCER'
                      ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-600/20 text-gray-900'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600 bg-white'
                  }`}
                >
                  <Briefcase className={`w-4 h-4 ${regForm.role === 'FREELANCER' ? 'text-blue-600' : 'text-gray-400'}`} />
                  <div>
                    <div className="text-xs font-bold">Find Work</div>
                    <div className="text-[10px] text-gray-500">As a Freelancer</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setRegForm({ ...regForm, role: 'CLIENT' })}
                  className={`p-3 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
                    regForm.role === 'CLIENT'
                      ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-600/20 text-gray-900'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600 bg-white'
                  }`}
                >
                  <User className={`w-4 h-4 ${regForm.role === 'CLIENT' ? 'text-blue-600' : 'text-gray-400'}`} />
                  <div>
                    <div className="text-xs font-bold">Hire Talent</div>
                    <div className="text-[10px] text-gray-500">As a Client</div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {/* ── Forms ────────────────────────────────────────────────────── */}
          {tab === 'login' ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              {/* Email */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                  placeholder="name@company.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                  required
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showLoginPassword ? 'text' : 'password'}
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    placeholder="Enter your password"
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-400 hover:text-gray-600 rounded-lg"
                  >
                    {showLoginPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between text-sm pt-1">
                <label className="flex items-center space-x-2 text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={loginForm.rememberMe}
                    onChange={(e) => setLoginForm({ ...loginForm, rememberMe: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="font-medium text-xs">Remember me</span>
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setForgotModalOpen(true)
                    setForgotEmail(loginForm.email)
                    setError('')
                  }}
                  className="text-xs text-blue-600 hover:text-blue-700 font-semibold"
                >
                  Forgot password?
                </button>

              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || googleLoading}
                className="w-full bg-black hover:bg-gray-800 disabled:opacity-50 text-white py-3.5 px-4 rounded-xl font-bold transition-all shadow-md active:scale-98 text-sm mt-2"
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              {/* First & Last Name */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={regForm.firstName}
                    onChange={(e) => setRegForm({ ...regForm, firstName: e.target.value })}
                    placeholder="Alex"
                    className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={regForm.lastName}
                    onChange={(e) => setRegForm({ ...regForm, lastName: e.target.value })}
                    placeholder="Morgan"
                    className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                    required
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={regForm.email}
                  onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                  placeholder="name@company.com"
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                  required
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                  Password (min 8 characters)
                </label>
                <div className="relative">
                  <input
                    type={showRegPassword ? 'text' : 'password'}
                    value={regForm.password}
                    onChange={(e) => setRegForm({ ...regForm, password: e.target.value })}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowRegPassword(!showRegPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-400 hover:text-gray-600 rounded-lg"
                  >
                    {showRegPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
                  Confirm Password
                </label>
                <input
                  type={showRegPassword ? 'text' : 'password'}
                  value={regForm.confirmPassword}
                  onChange={(e) => setRegForm({ ...regForm, confirmPassword: e.target.value })}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                  required
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || googleLoading}
                className="w-full bg-black hover:bg-gray-800 disabled:opacity-50 text-white py-3.5 px-4 rounded-xl font-bold transition-all shadow-md active:scale-98 text-sm mt-2"
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </button>
            </form>
          )}

          {/* ── Divider ──────────────────────────────────────────────────── */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase tracking-wider">
              <span className="px-3 bg-white text-gray-400 font-medium">or continue with</span>
            </div>
          </div>

          {/* ── Social Login Button ──────────────────────────────────────── */}
          <div>
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={googleLoading || loading}
              className="w-full flex items-center justify-center gap-3 py-3.5 px-4 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors shadow-2xs disabled:opacity-60 text-sm font-semibold text-gray-700 active:scale-98"
            >
              {googleLoading ? (
                <span className="w-5 h-5 border-2 border-gray-400 border-t-blue-600 rounded-full animate-spin" />
              ) : (
                <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
              )}
              <span>
                {googleLoading
                  ? 'Connecting to Google...'
                  : tab === 'login'
                    ? 'Sign in with Google'
                    : regForm.role
                      ? `Sign up with Google (${regForm.role === 'CLIENT' ? 'Client' : 'Freelancer'})`
                      : 'Sign up with Google'}
              </span>
            </button>
          </div>
        </div>
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
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-xl font-bold text-gray-900 mb-5">Forgot Password</h2>
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm shadow-2xs"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={forgotLoading || !forgotEmail}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 px-4 rounded-xl font-bold text-sm transition-all shadow-md active:scale-98"
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
        email={otpEmail}
        flow={otpFlow}
        initialCooldown={otpCooldown}
        onSuccess={(data) => {
          setOtpModalOpen(false)
          if (otpFlow === 'registration') {
            const user = data.user
            navigate(user?.role === 'CLIENT' ? '/client/onboarding' : '/freelancer/onboarding')
          } else {
            setForgotNotice('Password reset successfully! Please sign in with your new password.')
            setTab('login')
            setLoginForm((prev) => ({ ...prev, email: otpEmail }))
          }
        }}
      />
    </div>
  )
}

