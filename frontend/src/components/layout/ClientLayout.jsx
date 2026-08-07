import { useState, useRef, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Briefcase, CreditCard, MessageSquare, Star,
  LogOut, ChevronRight, User, HelpCircle,
  X, Mail, BookOpen, ShieldCheck, PanelLeftClose, PanelLeftOpen, Home, Search
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const NAV_LINKS = [
  { icon: Home,          label: 'Home',      path: '/client/home' },
  { icon: Briefcase,     label: 'Projects',  path: '/client/projects' },
  { icon: CreditCard,    label: 'Payments',  path: '/client/payments' },
  { icon: MessageSquare, label: 'Messages',  path: '/client/messages' },
  { icon: Star,          label: 'Reviews',   path: '/client/reviews' },
]

/* ── Help & Support Modal ────────────────────────────────────────────────── */
const HelpModal = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center text-indigo-600">
            <HelpCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Help & Support</h3>
            <p className="text-xs text-gray-500">Client Support Center</p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <div className="p-3.5 bg-gray-50 rounded-xl border border-gray-100 flex items-start gap-3">
            <Mail className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-gray-900">Contact Support</p>
              <p className="text-xs text-gray-500">Email us at <a href="mailto:support@freelanceflow.com" className="text-indigo-600 font-medium hover:underline">support@freelanceflow.com</a></p>
            </div>
          </div>

          <div className="p-3.5 bg-gray-50 rounded-xl border border-gray-100 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-accent-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-gray-900">Razorpay Escrow Protection</p>
              <p className="text-xs text-gray-500">Funds are held safely in escrow and only released when you approve delivered work.</p>
            </div>
          </div>

          <div className="p-3.5 bg-gray-50 rounded-xl border border-gray-100 flex items-start gap-3">
            <BookOpen className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-gray-900">AI Deliverable Reports</p>
              <p className="text-xs text-gray-500">Review structured weekly progress reports generated automatically from freelancer logs.</p>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 text-sm font-semibold rounded-xl transition-colors"
        >
          Got it
        </button>
      </div>
    </div>
  )
}

/* ── Profile Avatar ──────────────────────────────────────────────────────── */
const Avatar = ({ user, size = 'sm' }) => {
  const initials = [user?.first_name?.[0], user?.last_name?.[0]].filter(Boolean).join('').toUpperCase() || '?'
  const dim = size === 'lg' ? 'w-9 h-9 text-xs' : 'w-7 h-7 text-xs'
  return (
    <div className={`${dim} rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold flex-shrink-0`}>
      {initials}
    </div>
  )
}

/* ── Bottom Sidebar Profile Card (Opens Upwards) ─────────────────────────── */
const SidebarProfileCard = ({ collapsed, onOpenHelp }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const fullName = user?.first_name
    ? `${user.first_name} ${user.last_name || ''}`.trim()
    : user?.email?.split('@')[0] || 'Account'

  return (
    <div className="relative border-t border-gray-100 flex-shrink-0 mt-auto" ref={ref}>
      {/* Popover Menu Opening Upwards */}
      {open && (
        <div className={`absolute bottom-full mb-2 bg-white border border-gray-100 rounded-2xl shadow-xl z-50 overflow-hidden py-1 animate-in fade-in zoom-in-95 duration-100 ${
          collapsed ? 'left-2 w-48' : 'left-3 right-3'
        }`}>
          <button
            onClick={() => { navigate('/client/dashboard'); setOpen(false) }}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
          >
            <User className="w-4 h-4 text-gray-500" /> My Dashboard
          </button>
          <button
            onClick={() => { onOpenHelp(); setOpen(false) }}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          >
            <HelpCircle className="w-4 h-4 text-gray-500" /> Help & Support
          </button>
          <div className="border-t border-gray-100 my-1" />
          <button
            id="client-logout-btn"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-4 h-4 text-red-500" /> Sign Out
          </button>
        </div>
      )}

      <button
        id="client-profile-card-btn"
        onClick={() => setOpen(!open)}
        title={collapsed ? fullName : undefined}
        className={`w-full hover:bg-gray-50/80 transition-colors text-left group ${
          collapsed ? 'p-3 flex items-center justify-center' : 'p-4 flex items-center gap-3'
        }`}
      >
        <Avatar user={user} size="lg" />
        {!collapsed && (
          <>
            <div className="min-w-0 flex-1">
              <p className="font-bold text-sm text-gray-900 truncate group-hover:text-indigo-600 transition-colors">
                {fullName}
              </p>
              <p className="text-xs text-gray-500 font-medium capitalize">
                {user?.role?.toLowerCase() || 'Client'}
              </p>
            </div>
            <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${open ? '-rotate-90 text-indigo-600' : 'group-hover:text-gray-600'}`} />
          </>
        )}
      </button>
    </div>
  )
}

/* ── Client Layout ───────────────────────────────────────────────────────── */
export default function ClientLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const active = location.pathname
  const [showHelp, setShowHelp] = useState(false)

  // Persistent sidebar collapse state
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true')

  const toggleSidebar = () => {
    setCollapsed(prev => {
      const next = !prev
      localStorage.setItem('sidebar_collapsed', String(next))
      return next
    })
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className={`${collapsed ? 'w-20' : 'w-64'} bg-white border-r border-gray-100 h-screen sticky top-0 flex-shrink-0 flex flex-col justify-between z-20 transition-all duration-300 ease-in-out`}>
        <div className="flex flex-col flex-1 min-h-0">
          {/* Logo Header (Height: h-14 / 56px) */}
          <div className={`h-14 border-b border-gray-100 flex items-center flex-shrink-0 ${collapsed ? 'px-3 justify-center' : 'px-4 justify-between'}`}>
            {!collapsed ? (
              <>
                <button onClick={() => navigate('/client/dashboard')} className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Briefcase className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-base font-extrabold text-gray-900 tracking-tight truncate">FreelanceFlow</span>
                </button>
                <button
                  onClick={toggleSidebar}
                  title="Collapse sidebar"
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors flex-shrink-0"
                >
                  <PanelLeftClose className="w-5 h-5" />
                </button>
              </>
            ) : (
              <button
                onClick={toggleSidebar}
                title="Expand sidebar"
                className="p-2 rounded-xl bg-gray-50 text-gray-600 hover:bg-indigo-50 hover:text-indigo-600 transition-colors flex items-center justify-center"
              >
                <PanelLeftOpen className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Navigation links */}
          <nav className="p-3 space-y-1 overflow-y-auto flex-1">
            {NAV_LINKS.map(link => {
              const isActive = active === link.path || active.startsWith(link.path + '/')
              return (
                <button
                  key={link.path}
                  title={collapsed ? link.label : undefined}
                  onClick={() => navigate(link.path)}
                  className={`w-full flex items-center rounded-xl text-sm font-medium transition-colors ${
                    collapsed ? 'justify-center p-3' : 'gap-3 px-3 py-2.5'
                  } ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <link.icon className="w-5 h-5 flex-shrink-0" />
                  {!collapsed && <span>{link.label}</span>}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Profile Card at bottom of left sidebar (Opens Upward) */}
        <SidebarProfileCard collapsed={collapsed} onOpenHelp={() => setShowHelp(true)} />
      </aside>

      {/* ── Main Area ───────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-screen min-w-0">
        {/* Top Navbar Header (Height: h-14 / 56px) */}
        <header className="h-14 bg-white border-b border-gray-100 px-6 flex items-center justify-end flex-shrink-0 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-gray-400">FreelanceFlow Workplace</span>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>

      {/* Help Modal */}
      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
    </div>
  )
}
