import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { contractsAPI } from '../../api/bids'
import {
  SparklesIcon,
  BriefcaseIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
  UserCircleIcon,
  CurrencyRupeeIcon,
} from '@heroicons/react/24/outline'

const FreelancerWorklogsPage = () => {
  const navigate = useNavigate()
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  useEffect(() => {
    fetchContracts()
  }, [])

  const fetchContracts = async () => {
    setLoading(true)
    try {
      const res = await contractsAPI.getContracts()
      const list = Array.isArray(res.data) ? res.data : (res.data.results || [])
      setContracts(list)
    } catch (err) {
      console.error('Error fetching contracts:', err)
    } finally {
      setLoading(false)
    }
  }

  // Filter logic
  const filteredContracts = contracts.filter((c) => {
    const title = c.project?.title || c.bid?.project?.title || c.project_title || ''
    const client =
      c.client
        ? `${c.client.first_name || ''} ${c.client.last_name || ''} ${c.client.email || ''}`
        : c.bid?.project?.client
        ? `${c.bid.project.client.first_name || ''} ${c.bid.project.client.last_name || ''} ${c.bid.project.client.email || ''}`
        : c.client_name || ''
    const matchesSearch =
      title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      client.toLowerCase().includes(searchQuery.toLowerCase())

    if (statusFilter === 'ALL') return matchesSearch
    if (statusFilter === 'ACTIVE') return matchesSearch && (c.is_active || c.status === 'ACTIVE')
    if (statusFilter === 'COMPLETED') return matchesSearch && (c.status === 'COMPLETED' || !c.is_active)
    return matchesSearch
  })

  // Metrics summary
  const totalContracts = contracts.length
  const totalActive = contracts.filter((c) => c.is_active || c.status === 'ACTIVE').length
  const totalBudget = contracts.reduce((sum, c) => sum + (parseFloat(c.agreed_amount || c.rate || 0)), 0)

  return (
    <div className="min-h-screen bg-gray-50/60 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header with Dark Hero Banner matching FreelanceFlow theme */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-gradient-to-r from-gray-900 via-slate-900 to-indigo-950 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden">
          <div className="relative z-10 space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold text-indigo-200 border border-white/10">
              <SparklesIcon className="w-4 h-4 text-indigo-300 animate-pulse" />
              AI-Powered Workspace & Qdrant Grounding
            </div>
            <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
              Worklogs & Report Hub
            </h1>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              Select an active contract to launch the AI Worklog Assistant, ground project requirements with Qdrant vector retrieval, synthesize weekly progress, and compile official PDF reports.
            </p>
          </div>

          <div className="flex items-center gap-3 relative z-10 shrink-0">
            <button
              onClick={() => navigate('/freelancer/contracts')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-gray-900 text-sm font-bold hover:bg-gray-100 transition-all shadow-md active:scale-95"
            >
              <BriefcaseIcon className="w-4 h-4 text-indigo-600" />
              View All Contracts
            </button>
          </div>

          {/* Decorative background glow */}
          <div className="absolute -right-16 -bottom-16 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        </div>

        {/* Overview Stats Grid (Clean White Cards) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div className="bg-white rounded-2xl p-6 border border-gray-200/80 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0">
              <BriefcaseIcon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Active Workspaces</p>
              <p className="text-2xl font-black text-gray-900">{totalActive}</p>
              <p className="text-xs text-indigo-600 font-medium mt-0.5">Contracts ready for AI assistant</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-gray-200/80 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 shrink-0">
              <CurrencyRupeeIcon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Contract Value</p>
              <p className="text-2xl font-black text-gray-900">₹{totalBudget.toLocaleString()}</p>
              <p className="text-xs text-emerald-600 font-medium mt-0.5">Across active engagements</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-gray-200/80 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600 shrink-0">
              <ShieldCheckIcon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Qdrant Vector Cloud</p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                <span className="text-sm font-bold text-gray-900">Active Vector Grounding</span>
              </div>
              <p className="text-xs text-purple-600 font-medium mt-0.5">Smart AI Assistant</p>
            </div>
          </div>
        </div>

        {/* Search & Filter Toolbar (Clean White) */}
        <div className="bg-white rounded-2xl p-4 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search contracts by project or client..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            />
          </div>

          {/* Tab Filter */}
          <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-xl self-start md:self-auto">
            {[
              { id: 'ALL', label: 'All Contracts', count: totalContracts },
              { id: 'ACTIVE', label: 'Active', count: totalActive },
              { id: 'COMPLETED', label: 'Completed', count: totalContracts - totalActive },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                  statusFilter === tab.id
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-800'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
        </div>

        {/* Contracts Grid (White Cards) */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-gray-200 shadow-sm">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
            <p className="text-gray-500 text-sm mt-4 font-medium">Loading active workspaces...</p>
          </div>
        ) : filteredContracts.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-gray-300 p-8 shadow-sm">
            <BriefcaseIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-gray-900">No contracts found</h3>
            <p className="text-gray-500 text-sm mt-1 max-w-sm mx-auto">
              {searchQuery ? 'No contracts match your search query.' : 'You currently do not have any contracts assigned.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredContracts.map((contract) => {
              const projectTitle =
                contract.project?.title ||
                contract.bid?.project?.title ||
                contract.project_title ||
                `Contract #${contract.id}`
              const projectDesc =
                contract.project?.description ||
                contract.bid?.project?.description ||
                contract.project_description ||
                'No description provided for this contract.'
              const clientObj = contract.client || contract.bid?.project?.client
              const clientName = clientObj
                ? `${clientObj.first_name || ''} ${clientObj.last_name || ''}`.trim() || clientObj.email || clientObj.username
                : contract.client_name || 'Client'
              const amount = contract.agreed_amount || contract.rate || 0
              const isActive = contract.is_active || contract.status === 'ACTIVE'

              return (
                <div
                  key={contract.id}
                  className="group flex flex-col justify-between rounded-2xl bg-white border border-gray-200/90 hover:border-indigo-500/50 p-6 shadow-sm hover:shadow-xl transition-all duration-300"
                >
                  <div>
                    {/* Header Badges */}
                    <div className="flex items-center justify-between gap-2 mb-4">
                      <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-gray-100 text-gray-700 border border-gray-200">
                        #{contract.id}
                      </span>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                          isActive
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-gray-100 text-gray-600 border border-gray-200'
                        }`}
                      >
                        {contract.status || (isActive ? 'ACTIVE' : 'COMPLETED')}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                      {projectTitle}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">
                      {projectDesc}
                    </p>

                    {/* Meta Details */}
                    <div className="mt-5 pt-4 border-t border-gray-100 space-y-2 text-xs text-gray-600">
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5 text-gray-500">
                          <UserCircleIcon className="w-4 h-4" />
                          Client:
                        </span>
                        <span className="font-semibold text-gray-900">{clientName}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-500">Contract Budget:</span>
                        <span className="font-bold text-indigo-600 text-sm">
                          ₹{parseFloat(amount).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Action Button */}
                  <div className="mt-6 pt-4 border-t border-gray-100">
                    <button
                      onClick={() => navigate(`/freelancer/work/${contract.id}`)}
                      className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold shadow-md shadow-indigo-600/20 transition-all group-hover:scale-[1.02] active:scale-95"
                    >
                      <SparklesIcon className="w-4 h-4 text-indigo-200" />
                      Open AI Assistant
                      <ArrowRightIcon className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default FreelancerWorklogsPage
