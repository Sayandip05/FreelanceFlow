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
  CurrencyDollarIcon,
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

  const activeContracts = contracts.filter(c => c.status === 'ACTIVE')
  const completedContracts = contracts.filter(c => c.status === 'COMPLETED')
  const totalActive = activeContracts.length

  const filteredContracts = contracts.filter(c => {
    const titleMatch = (c.project?.title || c.title || '').toLowerCase().includes(searchQuery.toLowerCase())
    const clientMatch = (c.client?.first_name || c.client?.email || '').toLowerCase().includes(searchQuery.toLowerCase())
    const matchesSearch = titleMatch || clientMatch

    if (statusFilter === 'ALL') return matchesSearch
    return matchesSearch && c.status === statusFilter
  })

  // Total Contract Budget Aggregate
  const totalBudget = contracts.reduce((acc, c) => acc + parseFloat(c.agreed_amount || c.total_amount || 0), 0)

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {/* ── Top Header ────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <SparklesIcon className="w-5 h-5" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
              Work & AI Assistant
            </h1>
          </div>
          <p className="text-sm text-gray-500 mt-1 max-w-2xl">
            Track milestones, chat with your AI project assistant grounded with Qdrant vector memory, and auto-generate client-ready deliverables.
          </p>
        </div>

        {/* Quick stat pill */}
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-indigo-50 border border-indigo-100/80 rounded-2xl flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-bold text-indigo-950">
              {totalActive} Active Projects Available
            </span>
          </div>
        </div>
      </div>

      {/* ── Key Metrics Cards ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
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
            <CurrencyDollarIcon className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Contract Value</p>
            <p className="text-2xl font-black text-gray-900">${totalBudget.toLocaleString()}</p>
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
            <p className="text-xs text-purple-600 font-medium mt-0.5">Real-time semantic chat retrieval</p>
          </div>
        </div>
      </div>

      {/* ── Toolbar: Search & Filter Tabs ─────────────────────────────────── */}
      <div className="bg-white rounded-2xl p-4 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <MagnifyingGlassIcon className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search contracts or clients..."
            className="w-full pl-9 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          />
        </div>

        {/* Status Pills */}
        <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-xl">
          {[
            { id: 'ALL', label: 'All Projects', count: contracts.length },
            { id: 'ACTIVE', label: 'Active', count: activeContracts.length },
            { id: 'COMPLETED', label: 'Completed', count: completedContracts.length },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                statusFilter === tab.id
                  ? 'bg-white text-gray-900 shadow-xs'
                  : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              {tab.label}
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                statusFilter === tab.id ? 'bg-gray-100 text-gray-700' : 'bg-gray-200/70 text-gray-500'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Contracts Grid ────────────────────────────────────────────────── */}
      {loading ? (
        <div className="flex items-center justify-center py-24">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredContracts.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-3xl border border-gray-200/80 p-8 shadow-sm">
          <BriefcaseIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-900">No active work contracts found</h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto mt-1">
            When a client accepts your bid or hires you on a project, your AI worklog workspace will appear here.
          </p>
          <button
            onClick={() => navigate('/freelancer/browse')}
            className="mt-5 inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all"
          >
            Browse Open Projects <ArrowRightIcon className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredContracts.map((contract) => {
            const projectTitle = contract.project?.title || contract.title || 'Untitled Project'
            const clientName = contract.client?.first_name
              ? `${contract.client.first_name} ${contract.client.last_name || ''}`.trim()
              : (contract.client?.email || 'Direct Client')
            const amount = contract.agreed_amount || contract.total_amount || 0
            const isActive = contract.status === 'ACTIVE'

            return (
              <div
                key={contract.id}
                className="bg-white rounded-3xl border border-gray-200/80 p-6 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-300 flex flex-col justify-between group"
              >
                <div>
                  {/* Top Status & Badge */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`px-2.5 py-1 rounded-full text-[11px] font-extrabold tracking-wide uppercase ${
                      isActive
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {contract.status || 'ACTIVE'}
                    </span>
                    <span className="text-[11px] text-gray-400 font-medium">
                      #{contract.id}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <h3 className="text-base font-bold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                    {projectTitle}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                    {contract.project?.description || contract.description || 'Active milestone workspace with AI tracking enabled.'}
                  </p>

                  {/* Client and Rate Details */}
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
                        ${parseFloat(amount).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Action Button */}
                <div className="mt-6 pt-4 border-t border-gray-100">
                  <button
                    onClick={() => navigate(`/freelancer/contracts/${contract.id}/work`)}
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
  )
}

export default FreelancerWorklogsPage
