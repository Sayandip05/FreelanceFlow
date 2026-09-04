import { useState, useEffect, useCallback } from 'react'
import { Eye, EyeOff, AlertCircle, CheckCircle2, RefreshCw, X, ShieldCheck, ArrowLeft } from 'lucide-react'
import { OtpInput } from '../ui/otp-input'
import { authAPI } from '../../api/auth'

export default function OtpVerificationModal({
  isOpen,
  onClose,
  email,
  flow = 'registration', // 'registration' | 'password_reset'
  onSuccess,
  initialCooldown = 30,
}) {
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const [error, setError] = useState('')
  const [successNotice, setSuccessNotice] = useState('')
  const [countdown, setCountdown] = useState(initialCooldown)

  // Password reset specific fields
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Live countdown timer for 30s resend cooldown
  useEffect(() => {
    if (!isOpen) return
    setCountdown(initialCooldown)
    setOtp('')
    setError('')
    setSuccessNotice('')
    setNewPassword('')
    setConfirmPassword('')
  }, [isOpen, initialCooldown])

  useEffect(() => {
    if (countdown <= 0) return
    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [countdown])

  // Resend OTP
  const handleResendOtp = async () => {
    if (countdown > 0 || resendLoading) return
    setResendLoading(true)
    setError('')
    setSuccessNotice('')

    try {
      if (flow === 'registration') {
        await authAPI.resendRegisterOtp(email)
      } else {
        await authAPI.resendPasswordResetOtp(email)
      }
      setSuccessNotice('A new 6-digit code has been sent to your email.')
      setCountdown(30)
      setOtp('')
    } catch (err) {
      const data = err.response?.data
      setError(data?.detail || data?.error || 'Failed to resend code. Please try again.')
    } finally {
      setResendLoading(false)
    }
  }

  // Handle OTP Submit
  const handleVerify = async (e) => {
    if (e) e.preventDefault()
    if (!otp || otp.length !== 6) {
      setError('Please enter the full 6-digit code.')
      return
    }

    if (flow === 'password_reset') {
      if (!newPassword || newPassword.length < 8) {
        setError('New password must be at least 8 characters long.')
        return
      }
      if (newPassword !== confirmPassword) {
        setError('Passwords do not match.')
        return
      }
    }

    setLoading(true)
    setError('')
    setSuccessNotice('')

    try {
      if (flow === 'registration') {
        const resp = await authAPI.verifyRegisterOtp(email, otp)
        const { tokens, user } = resp.data
        if (tokens?.access) {
          localStorage.setItem('access_token', tokens.access)
          localStorage.setItem('refresh_token', tokens.refresh)
        }
        if (onSuccess) onSuccess({ user, tokens })
      } else {
        const resp = await authAPI.verifyPasswordResetOtp(email, otp, newPassword)
        if (onSuccess) onSuccess(resp.data)
      }
    } catch (err) {
      const data = err.response?.data
      const msg = data?.detail || data?.error || (typeof data === 'string' ? data : 'Verification failed. Please check the code and try again.')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 sm:p-8 overflow-hidden text-gray-900">
        
        {/* Close / Back Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
          title="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Shield Icon & Heading */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 text-blue-600 mb-3 shadow-sm">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            {flow === 'registration' ? 'Verify Your Email' : 'Reset Your Password'}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            We sent a 6-digit verification code to
          </p>
          <p className="text-sm font-semibold text-gray-800 break-all">
            {email}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">Code expires in 5 minutes</p>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="flex items-start gap-2.5 bg-red-50 border border-red-200 rounded-xl px-3.5 py-2.5 mb-4 text-xs sm:text-sm text-red-700">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <p className="leading-snug">{error}</p>
          </div>
        )}

        {/* Success Notification */}
        {successNotice && (
          <div className="flex items-start gap-2.5 bg-green-50 border border-green-200 rounded-xl px-3.5 py-2.5 mb-4 text-xs sm:text-sm text-green-700">
            <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
            <p className="leading-snug">{successNotice}</p>
          </div>
        )}

        {/* Animated OTP Input */}
        <div className="flex justify-center mb-6">
          <OtpInput
            value={otp}
            onChange={(val) => {
              setOtp(val)
              if (error) setError('')
            }}
            length={6}
            disabled={loading}
          />
        </div>

        {/* Password Reset Fields */}
        {flow === 'password_reset' && (
          <div className="space-y-3 mb-6">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                New Password (min 8 chars)
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  className="w-full px-3.5 py-2.5 pr-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                Confirm New Password
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-2xs"
                required
              />
            </div>
          </div>
        )}

        {/* Action Button */}
        <button
          type="button"
          onClick={handleVerify}
          disabled={loading || otp.length !== 6}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 px-4 rounded-xl font-bold transition-all shadow-md active:scale-98 text-sm flex items-center justify-center gap-2"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Verifying...
            </span>
          ) : flow === 'registration' ? (
            'Verify & Create Account'
          ) : (
            'Reset Password'
          )}
        </button>

        {/* Resend Cooldown Timer */}
        <div className="mt-5 text-center text-xs sm:text-sm text-gray-500">
          {countdown > 0 ? (
            <p>
              Didn't receive the code? Resend in{' '}
              <span className="font-bold text-gray-700 font-mono">
                00:{String(countdown).padStart(2, '0')}
              </span>
            </p>
          ) : (
            <div className="flex items-center justify-center gap-1.5">
              <span>Didn't receive the code?</span>
              <button
                type="button"
                onClick={handleResendOtp}
                disabled={resendLoading}
                className="text-blue-600 hover:text-blue-700 font-bold inline-flex items-center gap-1 transition-colors disabled:opacity-50"
              >
                {resendLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : null}
                Resend Code
              </button>
            </div>
          )}
        </div>

        {/* Back / Change email */}
        <div className="mt-4 pt-3 border-t border-gray-100 text-center">
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-gray-400 hover:text-gray-600 inline-flex items-center gap-1 transition-colors"
          >
            <ArrowLeft className="w-3 h-3" />
            Change email address
          </button>
        </div>

      </div>
    </div>
  )
}
