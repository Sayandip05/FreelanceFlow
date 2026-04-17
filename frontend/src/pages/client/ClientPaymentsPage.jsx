import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Briefcase, LayoutDashboard, CreditCard, MessageSquare, Star,
  Wallet, ArrowUpRight, ArrowDownLeft, Clock, CheckCircle, Shield
} from 'lucide-react'
import { paymentsAPI } from '../../api/payments'

const Sidebar = ({ active }) => {
  const navigate = useNavigate()
  const links = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/client/dashboard' },
    { icon: Briefcase, label: 'Projects', path: '/client/projects' },
    { icon: CreditCard, label: 'Payments', path: '/client/payments' },
    { icon: MessageSquare, label: 'Messages', path: '/client/messages' },
    { icon: Star, label: 'Reviews', path: '/client/reviews' },
  ]
  return (
    <aside className="w-64 bg-white border-r border-gray-100 min-h-screen flex-shrink-0">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-gray-900">FreelanceFlow</span>
        </div>
      </div>
      <nav className="p-4 space-y-1">
        {links.map((link) => (
          <button key={link.path} onClick={() => navigate(link.path)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
              active === link.path ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}>
            <link.icon className="w-5 h-5" />{link.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}

const STATUS_CONFIG = {
  ESCROWED: { label: 'In Escrow', color: 'bg-blue-100 text-blue-700', icon: Shield },
  RELEASED: { label: 'Released', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  PENDING: { label: 'Pending', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  REFUNDED: { label: 'Refunded', color: 'bg-gray-100 text-gray-600', icon: ArrowDownLeft },
}

const ClientPaymentsPage = () => {
  const navigate = useNavigate()
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPayments = async () => {
      try {
        const res = await paymentsAPI.getPayments()
        setPayments(res.data?.results || res.data || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchPayments()
  }, [])

  const totalEscrowed = payments.filter(p => p.status === 'ESCROWED').reduce((s, p) => s + parseFloat(p.total_amount || 0), 0)
  const totalSpent = payments.filter(p => p.status === 'RELEASED').reduce((s, p) => s + parseFloat(p.total_amount || 0), 0)
  const totalCount = payments.length

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active="/client/payments" />
      <div className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
          <p className="text-gray-600 mt-1">Manage escrow and payment history</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Total Spent</p>
              <div className="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center">
                <Wallet className="w-4 h-4 text-green-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">${totalSpent.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">In Escrow</p>
              <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-blue-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">${totalEscrowed.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Transactions</p>
              <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center">
                <CreditCard className="w-4 h-4 text-primary-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">{totalCount}</p>
          </div>
        </div>

        {/* Payment List */}
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Transaction History</h2>
          </div>
          {loading ? (
            <div className="p-6 space-y-3">
              {[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}
            </div>
          ) : payments.length === 0 ? (
            <div className="py-16 text-center">
              <CreditCard className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600 mb-2">No payment history yet</p>
              <p className="text-sm text-gray-400">Payments will appear here once you fund an escrow</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {payments.map(payment => {
                const config = STATUS_CONFIG[payment.status] || STATUS_CONFIG.PENDING
                const Icon = config.icon
                return (
                  <div key={payment.id} className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-primary-50 rounded-full flex items-center justify-center flex-shrink-0">
                        <ArrowUpRight className="w-5 h-5 text-primary-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          Contract #{payment.contract}
                        </p>
                        <p className="text-sm text-gray-500">
                          {new Date(payment.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1 ${config.color}`}>
                        <Icon className="w-3.5 h-3.5" /> {config.label}
                      </span>
                      <p className="font-semibold text-gray-900 w-24 text-right">
                        ${parseFloat(payment.total_amount || 0).toLocaleString()}
                      </p>
                      {payment.status === 'ESCROWED' && (
                        <button
                          onClick={() => navigate(`/client/contracts/${payment.contract}`)}
                          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                        >
                          Release
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Info Banner */}
        <div className="mt-6 flex items-start gap-3 bg-blue-50 border border-blue-100 rounded-xl p-4">
          <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-blue-800">Escrow Protection</p>
            <p className="text-sm text-blue-600 mt-0.5">Funds are held securely in escrow and only released when you approve the delivered work.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ClientPaymentsPage
