import { useState, useRef, useEffect, useCallback } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Briefcase, CreditCard, MessageSquare, Star,
  LogOut, ChevronRight, User, HelpCircle,
  X, Mail, BookOpen, ShieldCheck, PanelLeftClose, PanelLeftOpen, Home, Search, FileText, ScrollText, Wallet
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import PrivacyPolicyModal from '../ui/PrivacyPolicyModal'
import NotificationBell from '../common/NotificationBell'
import { notificationsAPI } from '../../api/notifications'

// Map notification types → which sidebar section they belong to
const NOTIFICATION_SECTION_MAP = {
  BID_SUBMITTED:     '/client/projects',
  BID_ACCEPTED:      '/client/contracts',
  ESCROW_CREATED:    '/client/payments',
  PAYMENT_RELEASED:  '/client/payments',
  LOG_SUBMITTED:     '/client/contracts',
  REPORT_READY:      '/client/contracts',
  CLIENT_REPORT_READY: '/client/contracts',
  PROOF_READY:       '/client/contracts',
  MESSAGE_RECEIVED:  '/client/messages',
  REVIEW_RECEIVED:   '/client/reviews',
}

function useSidebarBadges() {
  const [badges, setBadges] = useState({})

  const fetchBadges = useCallback(async () => {
    try {
      const res = await notificationsAPI.getUnreadNotifications()
      const notifications = res.data?.results || res.data || []
      const counts = {}
      notifications.forEach(n => {
        const section = NOTIFICATION_SECTION_MAP[n.type]
        if (section) counts[section] = (counts[section] || 0) + 1
      })
      setBadges(counts)
    } catch {
      // silently ignore — badges are non-critical
    }
  }, [])

  useEffect(() => {
    fetchBadges()
    const interval = setInterval(fetchBadges, 30000) // refresh every 30s
    return () => clearInterval(interval)
  }, [fetchBadges])

  return badges
}

const NAV_LINKS = [
  { icon: Home,          label: 'Home',      path: '/client/home' },
  { icon: Briefcase,     label: 'Projects',  path: '/client/projects' },
  { icon: ScrollText,    label: 'Contracts', path: '/client/contracts' },
  { icon: CreditCard,    label: 'Payments',  path: '/client/payments' },
  { icon: Wallet,        label: 'Wallet',    path: '/client/wallet' },
  { icon: MessageSquare, label: 'Messages',  path: '/client/messages' },
  { icon: Star,          label: 'Reviews',   path: '/client/reviews' },
]

/* ── Help & Support Modal ────────────────────────────────────────────────── */
const HelpModal = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white/90 backdrop-blur-xl rounded-none border border-white/80 shadow-2xl w-full max-w-md p-6 relative animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 p-1 rounded-none hover:bg-black/5 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-none bg-indigo-50/80 border border-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0 shadow-2xs">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900">Client Help & Escrow Protection</h3>
            <p className="text-xs text-gray-500">Need assistance managing jobs, escrow, or contracts?</p>
          </div>
        </div>

        <div className="space-y-3 mb-6 text-xs text-gray-600">
          <div className="p-3.5 bg-white/60 backdrop-blur-md rounded-none flex items-start gap-3 border border-gray-200/70 hover:bg-white/80 transition-all shadow-2xs">
            <ShieldCheck className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-gray-900">Safe Razorpay Escrow</p>
              <p className="text-xs text-gray-500">Deposit funds per milestone. Payouts are only released after you inspect and approve deliverables.</p>
            </div>
          </div>
          <div className="p-3.5 bg-white/60 backdrop-blur-md rounded-none flex items-start gap-3 border border-gray-200/70 hover:bg-white/80 transition-all shadow-2xs">
            <Mail className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-gray-900">24/7 Platform Concierge</p>
              <p className="text-xs text-gray-500">Email our support at <span className="font-semibold text-indigo-600">support@freelanceflow.com</span> for instant arbitration and help.</p>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 text-sm font-semibold rounded-none transition-colors shadow-sm active:scale-[0.99]"
        >
          Close Help
        </button>
      </div>
    </div>
  )
}

/* ── Profile Avatar ──────────────────────────────────────────────────────── */
const Avatar = ({ user, size = 'sm' }) => {
  const initials = [user?.first_name?.[0], user?.last_name?.[0]].filter(Boolean).join('').toUpperCase() || '?'
  const dim = size === 'lg' ? 'w-9 h-9 text-xs' : 'w-7 h-7 text-xs'
  const avatarUrl = user?.role === 'FREELANCER' ? user?.freelancer_profile?.avatar : user?.client_profile?.avatar
  return (
    <div className={`${dim} rounded-full bg-slate-200 text-slate-700 border border-slate-300/60 flex items-center justify-center font-bold flex-shrink-0 overflow-hidden`}>
      {avatarUrl ? (
        <img src={avatarUrl} alt={initials} className="w-full h-full object-cover" />
      ) : (
        initials
      )}
    </div>
  )
}

/* ── Bottom Sidebar Profile Card (Opens Upwards) ─────────────────────────── */
const SidebarProfileCard = ({ collapsed, onOpenHelp, onOpenPrivacy }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = () => {
    setOpen(false)
    logout()
    navigate('/login')
  }

  const fullName = user?.first_name
    ? `${user.first_name} ${user.last_name || ''}`.trim()
    : user?.email?.split('@')[0] || 'Account'

  return (
    <div
      className="relative border-t border-gray-100 flex-shrink-0 mt-auto"
      ref={ref}
    >
      {/* Popover Menu Opening Upwards */}
      {open && (
        <div className={`absolute bottom-full mb-2 bg-white border border-gray-200 rounded-2xl shadow-xl z-50 overflow-hidden py-1.5 animate-in fade-in zoom-in-95 duration-100 ${
          collapsed ? 'left-2 w-52' : 'left-3 right-3'
        }`}>
          <button
            onClick={() => { setOpen(false); navigate('/client/dashboard') }}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors cursor-pointer text-left"
          >
            <User className="w-4 h-4 text-gray-500 shrink-0" />
            <span>My Dashboard</span>
          </button>
          <button
            onClick={() => { setOpen(false); onOpenHelp() }}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors cursor-pointer text-left"
          >
            <HelpCircle className="w-4 h-4 text-gray-500 shrink-0" />
            <span>Help & Support</span>
          </button>
          <button
            onClick={() => { setOpen(false); onOpenPrivacy() }}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors cursor-pointer text-left"
          >
            <FileText className="w-4 h-4 text-gray-500 shrink-0" />
            <span>Privacy Policy</span>
          </button>
          <div className="border-t border-gray-100 my-1" />
          <button
            id="logout-btn"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer text-left"
          >
            <LogOut className="w-4 h-4 text-rose-500 shrink-0" />
            <span>Sign out</span>
          </button>
        </div>
      )}

      {/* Trigger Button */}
      <button
        onClick={() => setOpen(prev => !prev)}
        className={`w-full h-16 flex items-center transition-colors hover:bg-gray-50 text-left cursor-pointer ${
          collapsed ? 'justify-center px-3' : 'gap-3 px-4'
        }`}
        title={collapsed ? fullName : undefined}
      >
        <Avatar user={user} />
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-gray-900 truncate leading-tight">{fullName}</p>
            <p className="text-[11px] text-gray-400 truncate capitalize leading-tight">Client Account</p>
          </div>
        )}
        {!collapsed && <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${open ? '-rotate-90 text-primary-600' : ''}`} />}
      </button>
    </div>
  )
}

/* ── Client Layout Component ─────────────────────────────────────────────── */
export default function ClientLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const active = location.pathname
  const badges = useSidebarBadges()

  const [showHelp, setShowHelp] = useState(false)
  const [showPrivacy, setShowPrivacy] = useState(false)
  const [privacyMode, setPrivacyMode] = useState('view')
  const { user, logout } = useAuth()

  const handlePrivacyAccept = () => {
    if (user?.id) localStorage.setItem(`privacy_accepted_${user.id}`, 'true')
    setShowPrivacy(false)
  }

  const handlePrivacyDecline = () => {
    logout()
    navigate('/login')
  }

  const openPrivacyView = () => {
    setPrivacyMode('view')
    setShowPrivacy(true)
  }

  // Persistent sidebar collapse state (only toggled on click)
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true')
  const isExpanded = !collapsed

  const toggleSidebar = () => {
    setCollapsed(prev => {
      const next = !prev
      localStorage.setItem('sidebar_collapsed', String(next))
      return next
    })
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 w-full">
      {/* ── Sidebar (Fixed height, never scrolls) ── */}
      <aside
        className={`${isExpanded ? 'w-64' : 'w-20'} bg-white border-r border-gray-100 h-full flex-shrink-0 flex flex-col justify-between z-30 transition-all duration-300 ease-in-out select-none`}
      >
        <div className="flex flex-col flex-1 min-h-0">
          {/* Logo Header (Height: h-14 / 56px) */}
          <div className={`h-14 border-b border-gray-100 flex items-center flex-shrink-0 ${!isExpanded ? 'px-3 justify-center' : 'px-4 justify-between'}`}>
            {isExpanded ? (
              <>
                <button onClick={() => navigate('/client/dashboard')} className="flex items-center gap-2.5 min-w-0">
                  <img src="/logo.png" alt="FreelanceFlow" className="w-8 h-8 object-contain flex-shrink-0" />
                  <span className="text-base font-extrabold text-gray-900 tracking-tight truncate">
                    Freelance<span className="text-indigo-600">Flow</span>
                  </span>
                </button>
                <button
                  onClick={toggleSidebar}
                  title={collapsed ? "Pin sidebar open" : "Collapse sidebar"}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors flex-shrink-0"
                >
                  <PanelLeftClose className="w-5 h-5" />
                </button>
              </>
            ) : (
              <button
                onClick={toggleSidebar}
                title="Expand sidebar"
                className="p-1 rounded-xl hover:bg-gray-50 transition-colors flex items-center justify-center"
              >
                <img src="/logo.png" alt="FreelanceFlow" className="w-8 h-8 object-contain" />
              </button>
            )}
          </div>

          {/* Navigation links with unified spacious spacing */}
          <nav className="p-3 space-y-2 overflow-y-auto flex-1">
            {NAV_LINKS.map(link => {
              const isActive = active === link.path || active.startsWith(link.path + '/')
              const badgeCount = badges[link.path] || 0
              return (
                <button
                  key={link.path}
                  title={!isExpanded ? link.label : undefined}
                  onClick={() => navigate(link.path)}
                  className={`w-full h-11 flex items-center rounded-xl text-sm font-semibold transition-all duration-150 ${
                    !isExpanded ? 'justify-center px-0' : 'gap-3.5 px-3.5'
                  } ${
                    isActive
                      ? 'bg-gray-100 text-gray-900 font-bold'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <div className="relative w-5 h-5 flex-shrink-0">
                    <link.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-gray-900' : 'text-gray-500'}`} />
                    {badgeCount > 0 && !isExpanded && (
                      <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 bg-gray-100 text-gray-700 text-[10px] font-bold rounded-full border border-gray-200/80 flex items-center justify-center leading-none">
                        {badgeCount > 99 ? '99+' : badgeCount}
                      </span>
                    )}
                  </div>
                  {isExpanded && <span className="truncate">{link.label}</span>}
                  {isExpanded && badgeCount > 0 && (
                    <span className="ml-auto min-w-[20px] h-5 px-1.5 bg-gray-100 text-gray-700 text-[11px] font-bold rounded-full border border-gray-200/80 flex items-center justify-center leading-none flex-shrink-0">
                      {badgeCount > 99 ? '99+' : badgeCount}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Profile Card at bottom of left sidebar (Opens Upward) */}
        <SidebarProfileCard collapsed={!isExpanded} onOpenHelp={() => setShowHelp(true)} onOpenPrivacy={openPrivacyView} />
      </aside>

      {/* ── Main Area (Independent smooth scrolling container) ─────────────── */}
      <div className={`flex-1 flex flex-col min-w-0 ${location.pathname.includes('/messages') ? 'h-full overflow-hidden' : 'h-full overflow-y-auto'}`}>
        {/* Top Navbar Header (Sticky at top of scroll view) */}
        <header className="h-14 bg-white/95 backdrop-blur-md border-b border-gray-100 px-6 flex items-center justify-between flex-shrink-0 sticky top-0 z-20 shadow-xs">
          <div className="flex items-center gap-2">
            {/* Left header title / context */}
          </div>
          <div className="flex items-center gap-4">
            <NotificationBell />
            <div className="h-4 w-px bg-gray-200" />
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="FreelanceFlow" className="w-5 h-5 object-contain" />
              <span className="text-xs font-semibold text-gray-500">FreelanceFlow Workplace</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className={`flex-1 ${location.pathname.includes('/messages') ? 'p-0 overflow-hidden flex flex-col' : 'p-4 sm:p-6 lg:p-8'}`}>
          <Outlet />
        </main>
      </div>

      {/* Help Modal */}
      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}

      {/* Privacy Policy Modal */}
      {showPrivacy && (
        <PrivacyPolicyModal
          mode={privacyMode}
          onAccept={handlePrivacyAccept}
          onDecline={handlePrivacyDecline}
          onClose={() => setShowPrivacy(false)}
        />
      )}
    </div>
  )
}
