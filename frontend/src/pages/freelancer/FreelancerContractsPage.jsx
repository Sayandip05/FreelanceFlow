import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Search, FileText, Briefcase, DollarSign,
  MessageSquare, Clock, CheckCircle, ArrowRight
} from 'lucide-react'
import { contractsAPI } from '../../api/bids'

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

const FreelancerContractsPage = () => {
  const navigate = useNavigate()
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('active')

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const res = await contractsAPI.getContracts()
        setContracts(res.data?.results || res.data || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchContracts()
  }, [])

  const activeContracts = contracts.filter(c => c.is_active)
  const completedContracts = contracts.filter(c => !c.is_active)
  const displayed = activeTab === 'active' ? activeContracts : completedContracts

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active="/freelancer/contracts" />
      <div className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">My Contracts</h1>
          <p className="text-gray-600 mt-1">Manage your active and completed contracts</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6 w-fit">
          <button onClick={() => setActiveTab('active')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'active' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}>
            Active ({activeContracts.length})
          </button>
          <button onClick={() => setActiveTab('completed')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'completed' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'}`}>
            Completed ({completedContracts.length})
          </button>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => <div key={i} className="h-28 bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
        ) : displayed.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-gray-100">
            <Briefcase className="w-14 h-14 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No {activeTab} contracts</h3>
            <p className="text-gray-500 mb-6">
              {activeTab === 'active' ? 'Win a bid to start a contract' : 'Complete a contract to see it here'}
            </p>
            <button onClick={() => navigate('/freelancer/browse')} className="btn-primary">Browse Projects</button>
          </div>
        ) : (
          <div className="space-y-4">
            {displayed.map(contract => (
              <div key={contract.id}
                onClick={() => navigate(`/freelancer/contracts/${contract.id}`)}
                className="bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-lg mb-1">
                      {contract.bid?.project?.title || `Contract #${contract.id}`}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Client: {contract.bid?.project?.client?.first_name} {contract.bid?.project?.client?.last_name}
                    </p>
                    <p className="text-sm text-gray-500 mt-0.5">
                      Started: {new Date(contract.start_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-xl font-bold text-gray-900">${contract.agreed_amount?.toLocaleString()}</p>
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${contract.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                        {contract.is_active ? 'Active' : 'Completed'}
                      </span>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default FreelancerContractsPage
