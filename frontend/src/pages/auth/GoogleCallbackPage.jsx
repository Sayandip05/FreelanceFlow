import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import authAPI from '../../api/auth'

/**
 * GoogleCallbackPage
 * Landing page for the Google OAuth redirect.
 * Backend sends: /auth/google/callback?access=<jwt>&refresh=<jwt>&role=CLIENT|FREELANCER
 * On error:      /auth/google/callback?error=<reason>
 */
const GoogleCallbackPage = () => {
  const navigate = useNavigate()
  const { setUser } = useAuth()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const access  = params.get('access')  || params.get('access_token')
    const refresh = params.get('refresh') || params.get('refresh_token')
    const role    = params.get('role')
    const error   = params.get('error')

    if (error || !access) {
      navigate('/login?error=oauth_failed', { replace: true })
      return
    }

    // Persist tokens
    localStorage.setItem('access_token', access)
    if (refresh) localStorage.setItem('refresh_token', refresh)

    // Load the full user profile into AuthContext so protected pages work
    authAPI.getProfile()
      .then(res => {
        setUser(res.data)
        const destination = (res.data?.role || role) === 'CLIENT'
          ? '/client/dashboard'
          : '/freelancer/dashboard'
        navigate(destination, { replace: true })
      })
      .catch(() => {
        // Profile fetch failed — still navigate based on role param
        const destination = role === 'CLIENT' ? '/client/dashboard' : '/freelancer/dashboard'
        navigate(destination, { replace: true })
      })
  }, [navigate, setUser])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Briefcase className="w-9 h-9 text-white" />
        </div>
        <div className="flex items-center justify-center gap-3 mb-3">
          <div className="w-5 h-5 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-700 font-medium">Completing sign in...</p>
        </div>
        <p className="text-sm text-gray-400">You'll be redirected automatically</p>
      </div>
    </div>
  )
}

export default GoogleCallbackPage
