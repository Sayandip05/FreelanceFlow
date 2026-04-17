import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Search, FileText, Briefcase, DollarSign,
  MessageSquare, TrendingUp, Clock, CheckCircle, ArrowRight, Plus
} from 'lucide-react'
import { bidsAPI, contractsAPI } from '../../api/bids'
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

const StatCard = ({ icon: Icon, label, value, color, bg }) => (
  <div className="bg-white rounded-2xl border border-gray-100 p-6 flex items-center gap-4">
    <div className={`w-12 h-12 ${bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
      <Icon className={`w-6 h-6 ${color}`} />
    </div>
    <div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  </div>
)

const FreelancerOverviewPage = () => {
  const navigate = useNavigate()
  const [bids, setBids] = useState([])
  const [contracts, setContracts] = useState([])
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [bidsRes, contractsRes, paymentsRes] = await Promise.allSettled([
          bidsAPI.getMyBids(),
          contractsAPI.getContracts(),
          paymentsAPI.getPaymentHistory(),
        ])
        if (bidsRes.status === 'fulfilled') setBids(bidsRes.value.data?.results || bidsRes.value.data || [])
        if (contractsRes.status === 'fulfilled') setContracts(contractsRes.value.data?.results || contractsRes.value.data || [])
        if (paymentsRes.status === 'fulfilled') setPayments(paymentsRes.value.data?.results || paymentsRes.value.data || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const activeContracts = contracts.filter(c => c.is_active)
  const pendingBids = bids.filter(b => b.status === 'PENDING')
  const totalEarned = payments
    .filter(p => p.status === 'RELEASED')
    .reduce((s, p) => s + parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0), 0)

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active="/freelancer/dashboard" />
      <div className="flex-1 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Freelancer Dashboard</h1>
            <p className="text-gray-600 mt-1">Track your work, bids, and earnings</p>
          </div>
          <button onClick={() => navigate('/freelancer/browse')} className="btn-primary flex items-center gap-2">
            <Search className="w-4 h-4" /> Find Projects
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Briefcase} label="Active Contracts" value={loading ? '—' : activeContracts.length} color="text-primary-600" bg="bg-primary-50" />
          <StatCard icon={FileText} label="Pending Bids" value={loading ? '—' : pendingBids.length} color="text-yellow-600" bg="bg-yellow-50" />
          <StatCard icon={DollarSign} label="Total Earned" value={loading ? '—' : `$${totalEarned.toLocaleString()}`} color="text-accent-600" bg="bg-green-50" />
          <StatCard icon={CheckCircle} label="Completed" value={loading ? '—' : contracts.filter(c => !c.is_active).length} color="text-indigo-600" bg="bg-indigo-50" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Contracts */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-gray-900">Active Contracts</h2>
              <button onClick={() => navigate('/freelancer/contracts')}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                View all <ArrowRight className="w-4 h-4" />
              </button>
            </div>
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}
              </div>
            ) : activeContracts.length === 0 ? (
              <div className="text-center py-12">
                <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No active contracts yet</p>
                <button onClick={() => navigate('/freelancer/browse')} className="btn-primary text-sm">Browse Projects</button>
              </div>
            ) : (
              <div className="space-y-3">
                {activeContracts.slice(0, 5).map(contract => (
                  <div key={contract.id} onClick={() => navigate(`/freelancer/contracts/${contract.id}`)}
                    className="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors">
                    <div>
                      <p className="font-medium text-gray-900">{contract.bid?.project?.title || `Contract #${contract.id}`}</p>
                      <p className="text-sm text-gray-500">${contract.agreed_amount}</p>
                    </div>
                    <span className="text-xs px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium">Active</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <div className="bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl p-6 text-white">
              <TrendingUp className="w-8 h-8 mb-3 opacity-80" />
              <h3 className="font-semibold text-lg mb-1">Boost Your Income</h3>
              <p className="text-primary-100 text-sm mb-4">Browse new projects and submit competitive bids.</p>
              <button onClick={() => navigate('/freelancer/browse')}
                className="bg-white text-primary-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-primary-50 transition-colors w-full">
                Browse Projects
              </button>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
              <div className="space-y-2">
                {[
                  { icon: FileText, label: 'My Bids', path: '/freelancer/bids', color: 'text-yellow-600' },
                  { icon: Clock, label: 'Work Logs', path: '/freelancer/worklogs', color: 'text-blue-600' },
                  { icon: DollarSign, label: 'Earnings', path: '/freelancer/earnings', color: 'text-green-600' },
                  { icon: MessageSquare, label: 'Messages', path: '/freelancer/messages', color: 'text-purple-600' },
                ].map((item) => (
                  <button key={item.path} onClick={() => navigate(item.path)}
                    className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors">
                    <item.icon className={`w-5 h-5 ${item.color}`} />
                    <span className="text-sm text-gray-700">{item.label}</span>
                    <ArrowRight className="w-4 h-4 text-gray-400 ml-auto" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FreelancerOverviewPage
