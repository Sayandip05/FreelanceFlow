import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell, Check, CheckCheck, MessageSquare, Briefcase,
  DollarSign, Clock, Sparkles, X, ChevronRight, CheckCircle2
} from 'lucide-react'
import { useNotifications } from '../../context/NotificationContext'

const NotificationBell = () => {
  const navigate = useNavigate()
  // Pull live state from context (fed by WebSocket + REST)
  const { notifications, unreadCount, markRead, markAllRead, fetchNotifications, setPdfReadyUrl } = useNotifications() || {}
  const safeNotifications = notifications || []
  const safeUnreadCount = unreadCount || 0

  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)
  const closeTimerRef = useRef(null)


  // Auto open on hover & close when cursor moves away
  const handleMouseEnter = () => {
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current)
      closeTimerRef.current = null
    }
    setOpen(true)
    if (fetchNotifications) {
      fetchNotifications()
    }
  }

  const handleMouseLeave = () => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    closeTimerRef.current = setTimeout(() => {
      setOpen(false)
    }, 180)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  const handleMarkAllRead = async () => {
    if (markAllRead) markAllRead()
  }

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read && markRead) {
      markRead(notif.id)
    }

    setOpen(false)

    // Route based on notification type or action_url
    if (notif.data?.pdf_url && setPdfReadyUrl) {
      setPdfReadyUrl(notif.data.pdf_url)
    } else if (notif.action_url) {
      navigate(notif.action_url)
    } else if (notif.type === 'MESSAGE' || notif.notification_type === 'MESSAGE') {
      navigate('/messages')
    } else if (notif.type?.includes('CONTRACT') || notif.notification_type?.includes('CONTRACT')) {
      navigate('/contracts')
    } else if (notif.type?.includes('PAYMENT') || notif.notification_type?.includes('PAYMENT')) {
      navigate('/earnings')
    } else if (notif.type?.includes('BID') || notif.notification_type?.includes('BID')) {
      const isClient = notif.type?.includes('SUBMITTED') || notif.notification_type?.includes('SUBMITTED')
      navigate(isClient ? '/client/projects' : '/freelancer/bids')
    }
  }

  const getNotifIcon = (type) => {
    const t = (type || '').toUpperCase()
    if (t.includes('MESSAGE') || t.includes('CHAT')) return <MessageSquare className="w-4 h-4 text-indigo-600" />
    if (t.includes('PAYMENT') || t.includes('ESCROW')) return <DollarSign className="w-4 h-4 text-emerald-600" />
    if (t.includes('CONTRACT') || t.includes('BID')) return <Briefcase className="w-4 h-4 text-primary-600" />
    if (t.includes('WORKLOG') || t.includes('AI')) return <Sparkles className="w-4 h-4 text-purple-600" />
    return <Clock className="w-4 h-4 text-gray-500" />
  }

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return ''
    const diffMs = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diffMs / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  return (
    <div
      className="relative"
      ref={menuRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Bell Button */}
      <button
        type="button"
        id="notification-bell-btn"
        onClick={() => {
          setOpen(prev => !prev)
        }}
        className={`relative p-2 rounded-xl transition-all duration-200 flex items-center justify-center ${
          open
            ? 'bg-gray-100 text-gray-900 ring-2 ring-gray-900/10'
            : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
        }`}
        title="Notifications"
      >
        <Bell className="w-5 h-5" />
        {safeUnreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-[10px] font-black rounded-full flex items-center justify-center shadow-sm animate-pulse border-2 border-white">
            {safeUnreadCount > 9 ? '9+' : safeUnreadCount}
          </span>
        )}
      </button>

      {/* Popover Dropdown */}
      {open && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-100 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/70">
            <div className="flex items-center gap-2">
              <span className="text-sm font-extrabold text-gray-900">Notifications</span>
              {safeUnreadCount > 0 && (
                <span className="px-2 py-0.5 bg-red-50 text-red-600 border border-red-200 text-[10px] font-bold rounded-full">
                  {safeUnreadCount} unread
                </span>
              )}
            </div>
            {safeUnreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="text-[11px] font-bold text-primary-600 hover:text-primary-800 flex items-center gap-1 transition-colors"
              >
                <CheckCheck className="w-3.5 h-3.5" /> Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-96 overflow-y-auto divide-y divide-gray-50">
            {safeNotifications.length === 0 ? (
              <div className="py-12 px-4 text-center">
                <div className="w-10 h-10 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-2 text-gray-400">
                  <Bell className="w-5 h-5" />
                </div>
                <p className="text-xs font-bold text-gray-700">All caught up!</p>
                <p className="text-[11px] text-gray-400 mt-0.5">No new notifications right now</p>
              </div>
            ) : (
              safeNotifications.slice(0, 15).map(notif => {
                const isUnread = !notif.is_read
                return (
                  <div
                    key={notif.id}
                    onClick={() => handleNotificationClick(notif)}
                    className={`p-3.5 flex items-start gap-3 cursor-pointer transition-colors ${
                      isUnread ? 'bg-indigo-50/40 hover:bg-indigo-50/70' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-white border border-gray-100 shadow-xs flex-shrink-0 mt-0.5">
                      {getNotifIcon(notif.type || notif.notification_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className={`text-xs truncate ${isUnread ? 'font-extrabold text-gray-900' : 'font-semibold text-gray-700'}`}>
                          {notif.title || 'System Notification'}
                        </p>
                        <span className="text-[10px] text-gray-400 whitespace-nowrap flex-shrink-0">
                          {formatTimeAgo(notif.created_at)}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">
                        {notif.message || notif.content || notif.body || 'You have an update.'}
                      </p>
                    </div>
                    {isUnread && (
                      <span className="w-2 h-2 rounded-full bg-primary-600 mt-2 flex-shrink-0" />
                    )}
                  </div>
                )
              })
            )}
          </div>

          {/* Footer */}
          <div className="p-2.5 bg-gray-50 border-t border-gray-100 text-center">
            <span className="text-[11px] font-semibold text-gray-500">FreelanceFlow Notification Hub</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationBell
