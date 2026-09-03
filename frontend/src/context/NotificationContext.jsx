import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react'
import api from '../api/axiosConfig'
import { useAuth } from './AuthContext'
import { getWebSocketUrl } from '../utils/websocket'

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
  const [pdfReadyUrl, setPdfReadyUrl] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

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
    const url = getWebSocketUrl('/ws/notifications/', { token })
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
          
          if (notif.type === 'receipt_pdf_ready') {
            setPdfReadyUrl(notif.pdf_url);
            toast.success('Your official payment receipt is ready for download!', 'Receipt Generated')
            return; // Don't add to standard notifications list
          }
          
          if (notif.type === 'receipt_pdf_error') {
            toast.error(`Receipt generation failed: ${notif.error}`, 'Receipt Error');
            return;
          }
          
          setNotifications((prev) => {
            if (prev.some((n) => n.id === notif.id)) return prev
            return [notif, ...prev]
          })
          if (!notif.is_read) {
            setUnreadCount((prev) => prev + 1)
          }

          // Show in-app interactive notification toast
          const clickHandler = notif.action_url
            ? () => {
                if (notif.action_url.startsWith('http')) {
                  window.open(notif.action_url, '_blank')
                } else {
                  navigate(notif.action_url)
                }
              }
            : null

          toast.notification(
            notif.body || notif.message || notif.title,
            notif.title || 'New Notification',
            clickHandler
          )
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
    <NotificationContext.Provider value={{ notifications, unreadCount, markRead, markAllRead, fetchNotifications, setPdfReadyUrl }}>
      {children}
      {/* PDF Ready Toast Overlay */}
      {pdfReadyUrl && (() => {
        const toastUrl = typeof pdfReadyUrl === 'object' ? pdfReadyUrl?.url : pdfReadyUrl;
        const toastTitle = typeof pdfReadyUrl === 'object' ? (pdfReadyUrl?.title || 'Document Ready!') : 'Receipt Ready!';
        const toastBody = typeof pdfReadyUrl === 'object' ? (pdfReadyUrl?.body || 'Your PDF has been generated.') : 'Your PDF has been generated.';

        if (!toastUrl) return null;

        return (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-[9999] animate-in fade-in duration-200">
            <div className="bg-white border border-gray-100 shadow-2xl rounded-3xl p-6 max-w-md w-full animate-in zoom-in-95 duration-150 space-y-4 text-center">
              <div className="w-14 h-14 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 mx-auto border border-emerald-100 shadow-xs">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </div>
              <div>
                <h3 className="font-extrabold text-gray-900 text-lg">{toastTitle}</h3>
                <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{toastBody}</p>
              </div>
              <div className="pt-2 flex gap-3">
                <button 
                  onClick={() => setPdfReadyUrl(null)} 
                  className="flex-1 py-2.5 px-4 border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-bold rounded-xl transition-colors"
                >
                  Dismiss
                </button>
                <a 
                  href={toastUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  onClick={() => setPdfReadyUrl(null)}
                  className="flex-1 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition-colors text-center shadow-sm flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download PDF
                </a>
              </div>
            </div>
          </div>
        );
      })()}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  return useContext(NotificationContext)
}

export default NotificationContext
