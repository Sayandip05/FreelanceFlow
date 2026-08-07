import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function FreelancerRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'FREELANCER') return <Navigate to="/client/dashboard" replace />

  const profile = user.freelancer_profile
  const isOnboarded = profile?.is_onboarded || (Boolean(profile?.city) && (profile?.skills?.length || 0) > 0)

  if (!isOnboarded && location.pathname !== '/freelancer/onboarding') {
    return <Navigate to="/freelancer/onboarding" replace />
  }

  return <Outlet />
}
