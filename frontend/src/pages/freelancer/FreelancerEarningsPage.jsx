import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Search, FileText, Briefcase, DollarSign,
  MessageSquare, Clock, TrendingUp, ArrowUpRight, Calendar, CheckCircle
} from 'lucide-react'
import { paymentsAPI } from '../../api/payments'

const Sidebar = ({ active }) => {
  const navigate = useNavigate()
  const links = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/freelancer/dashboard' },
    { icon: Search, label: 'Browse Projects', path: '/freelancer/browse' },
    { icon: FileText, label: 'My Bids', path: '/freelancer/bids' },
    { icon: Briefcase, label: 'Contracts', path: '/freelancer/contracts' },
    { icon: Clock, label: 'Work Logs', path: '/freelancer/worklogs' },
    { icon: DollarSign, label: 'Earnings', path: '/freelancer/earnings' },
    { icon: MessageSquare, label: 'Messages', path: '/freelancer/messages' },
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

const FreelancerEarningsPage = () => {
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPayments = async () => {
      try {
        const res = await paymentsAPI.getPaymentHistory()
        setPayments(res.data?.results || res.data || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchPayments()
  }, [])

  const releasedPayments = payments.filter(p => p.status === 'RELEASED')
  const totalEarned = releasedPayments.reduce((s, p) => {
    const net = parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
    return s + net
  }, 0)
  const pendingAmount = payments
    .filter(p => p.status === 'ESCROWED')
    .reduce((s, p) => s + parseFloat(p.total_amount * 0.9 || 0), 0)

  // Monthly summary (simple grouping)
  const monthlyData = releasedPayments.reduce((acc, p) => {
    const month = new Date(p.created_at).toLocaleString('default', { month: 'long', year: 'numeric' })
    const net = parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
    acc[month] = (acc[month] || 0) + net
    return acc
  }, {})

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active="/freelancer/earnings" />
      <div className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Earnings</h1>
          <p className="text-gray-600 mt-1">Your payment history and earnings summary</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl p-6 text-white">
            <div className="flex items-center justify-between mb-3">
              <p className="text-primary-100 text-sm">Total Earned</p>
              <TrendingUp className="w-5 h-5 text-primary-200" />
            </div>
            <p className="text-3xl font-bold">${totalEarned.toLocaleString()}</p>
            <p className="text-primary-200 text-sm mt-1">{releasedPayments.length} payments received</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-gray-500 text-sm">Pending in Escrow</p>
              <Clock className="w-5 h-5 text-yellow-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">${pendingAmount.toLocaleString()}</p>
            <p className="text-gray-400 text-sm mt-1">Awaiting release</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-gray-500 text-sm">Platform Fee</p>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">10%</p>
            <p className="text-gray-400 text-sm mt-1">You keep 90%</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Transaction History */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Transaction History</h2>
            </div>
            {loading ? (
              <div className="p-6 space-y-3">
                {[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}
              </div>
            ) : payments.length === 0 ? (
              <div className="py-16 text-center">
                <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-600 mb-2">No earnings yet</p>
                <p className="text-sm text-gray-400">Complete contracts to earn money</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {payments.map(payment => (
                  <div key={payment.id} className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                        payment.status === 'RELEASED' ? 'bg-green-50' : 'bg-yellow-50'
                      }`}>
                        <ArrowUpRight className={`w-5 h-5 ${payment.status === 'RELEASED' ? 'text-green-600' : 'text-yellow-600'}`} />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 text-sm">Contract #{payment.contract}</p>
                        <p className="text-xs text-gray-400 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(payment.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${payment.status === 'RELEASED' ? 'text-green-600' : 'text-yellow-600'}`}>
                        +${(parseFloat(payment.freelancer_amount || payment.total_amount * 0.9 || 0)).toLocaleString()}
                      </p>
                      <span className={`text-xs ${payment.status === 'RELEASED' ? 'text-green-500' : 'text-yellow-500'}`}>
                        {payment.status === 'RELEASED' ? 'Received' : 'In Escrow'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Monthly Summary */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Monthly Summary</h2>
            {Object.keys(monthlyData).length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No data available</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(monthlyData).slice(0, 6).map(([month, amount]) => (
                  <div key={month} className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">{month}</p>
                    <p className="text-sm font-semibold text-gray-900">${amount.toLocaleString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FreelancerEarningsPage
