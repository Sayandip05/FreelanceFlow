import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import authAPI from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load user from token on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      authAPI.getProfile()
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await authAPI.login(email, password)
    const { access, refresh } = res.data
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    const profileRes = await authAPI.getProfile()
    setUser(profileRes.data)
    return profileRes.data
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }, [])

  const fetchUser = useCallback(async () => {
    try {
      const res = await authAPI.getProfile()
      setUser(res.data)
      return res.data
    } catch (e) {
      console.error('Failed to fetch user profile:', e)
      return null
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser, fetchUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

export default AuthContext
