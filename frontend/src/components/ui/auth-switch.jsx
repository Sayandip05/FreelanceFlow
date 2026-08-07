import { useNavigate, useLocation } from 'react-router-dom'
import { cn } from '../../lib/utils'

export const AuthSwitch = ({ activeTab = 'login' }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const search = location.search

  return (
    <div className={cn("flex items-center bg-gray-100/90 p-1.5 rounded-2xl mb-6 border border-gray-200/60 shadow-inner")}>
      <button
        type="button"
        id="switch-to-login"
        onClick={() => navigate(`/login${search}`)}
        className={cn(
          "flex-1 py-2.5 text-xs font-bold rounded-xl transition-all duration-200 text-center tracking-wide",
          activeTab === 'login'
            ? "bg-white text-gray-900 shadow-sm"
            : "text-gray-500 hover:text-gray-900"
        )}
      >
        Sign In
      </button>
      <button
        type="button"
        id="switch-to-register"
        onClick={() => navigate(`/register${search}`)}
        className={cn(
          "flex-1 py-2.5 text-xs font-bold rounded-xl transition-all duration-200 text-center tracking-wide",
          activeTab === 'register'
            ? "bg-white text-gray-900 shadow-sm"
            : "text-gray-500 hover:text-gray-900"
        )}
      >
        Create Account
      </button>
    </div>
  )
}

export default AuthSwitch
