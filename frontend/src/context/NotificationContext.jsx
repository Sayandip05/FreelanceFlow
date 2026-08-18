import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react'
import api from '../api/axiosConfig'
import { useAuth } from './AuthContext'

const NotificationContext = createContext(null)

/**
 * NotificationProvider
 *
 * - Fetches initial notifications via REST on mount
 * - Opens a WebSocket to ws/notifications/?token=... for real-time push
 * - Exposes: notifications, unreadCount, markRead, markAllRead, fetchNotifications
 */
export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)
  const { user } = useAuth()

  // ── REST fetch (used on mount and as WS fallback) ─────────────────────────
  const fetchNotifications = useCallback(async () => {
    if (!user) {
      setNotifications([])
      setUnreadCount(0)
      return
    }
    try {
      const [countRes, listRes] = await Promise.allSettled([
        api.get('/notifications/notifications/unread_count/'),
        api.get('/notifications/notifications/'),
      ])
      if (countRes.status === 'fulfilled') {
        setUnreadCount(countRes.value.data?.unread_count ?? 0)
      }
      if (listRes.status === 'fulfilled') {
        const raw = listRes.value.data
        setNotifications(Array.isArray(raw) ? raw : (raw?.results ?? []))
      }
    } catch {
      // Silently ignore — WS will keep us current
    }
  }, [user])

  // ── WebSocket connection ───────────────────────────────────────────────────
  const connectWS = useCallback(() => {
    if (!user) return
    const token =
      localStorage.getItem('access_token') ||
      sessionStorage.getItem('access_token') ||
      ''
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host =
      window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
    const url = `${protocol}//${host}/ws/notifications/?token=${token}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      // WS connected — initial notifications arrive via initial_notifications frame
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'initial_notifications') {
          // Merge server-delivered unread list with local state
          const incoming = data.notifications || []
          setNotifications((prev) => {
            const existingIds = new Set(prev.map((n) => n.id))
            const merged = [...incoming.filter((n) => !existingIds.has(n.id)), ...prev]
            return merged
          })
          setUnreadCount((prev) => Math.max(prev, incoming.length))
          return
        }

        if (data.type === 'new_notification') {
          const notif = data.notification
          setNotifications((prev) => {
            if (prev.some((n) => n.id === notif.id)) return prev
            return [notif, ...prev]
          })
          if (!notif.is_read) {
            setUnreadCount((prev) => prev + 1)
          }
          return
        }
      } catch {
        // Ignore malformed frames
      }
    }

    ws.onclose = () => {
      // Reconnect after 5 s if the token is still valid
      reconnectTimer.current = setTimeout(() => {
        const stillLoggedIn =
          localStorage.getItem('access_token') ||
          sessionStorage.getItem('access_token')
        if (stillLoggedIn) connectWS()
      }, 5000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [user])

  // ── Mark single notification read (optimistic) ────────────────────────────
  const markRead = useCallback(async (notifId) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notifId ? { ...n, is_read: true } : n))
    )
    setUnreadCount((prev) => Math.max(0, prev - 1))
    try {
      await api.post(`/notifications/notifications/${notifId}/mark_read/`)
    } catch {
      // Revert on error
      setNotifications((prev) =>
        prev.map((n) => (n.id === notifId ? { ...n, is_read: false } : n))
      )
      setUnreadCount((prev) => prev + 1)
    }
  }, [])

  // ── Mark all read ─────────────────────────────────────────────────────────
  const markAllRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
    setUnreadCount(0)
    try {
      await api.post('/notifications/notifications/mark_all_read/')
    } catch {
      // RE-fetch to restore consistent state
      fetchNotifications()
    }
  }, [fetchNotifications])

  // ── Bootstrap ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!user) {
      setNotifications([])
      setUnreadCount(0)
      return
    }

    fetchNotifications()
    connectWS()

    // Also re-fetch when user tabs back in (catch events missed while hidden)
    const handleFocus = () => fetchNotifications()
    window.addEventListener('focus', handleFocus)

    return () => {
      window.removeEventListener('focus', handleFocus)
      clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect on unmount
        wsRef.current.close()
      }
    }
  }, [user, fetchNotifications, connectWS])

  return (
    <NotificationContext.Provider
      value={{ notifications, unreadCount, markRead, markAllRead, fetchNotifications }}
    >
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  return useContext(NotificationContext)
}

export default NotificationContext
