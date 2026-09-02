import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { contractsAPI } from '../../api/bids'
import { Skeleton } from '../../components/common/Skeleton'
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
      <div>
        <div className="flex items-center gap-2.5">
          <span className="p-2 rounded-xl bg-gray-100 text-gray-800 border border-gray-200">
            <SparklesIcon className="w-5 h-5 text-gray-700" />
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
            Work Logs & Deliverables
          </h1>
        </div>
        <p className="text-sm text-gray-500 mt-1 max-w-2xl">
          Track milestones, log deliverables manually or with your AI assistant, and compile client reports.
        </p>
      </div>

      {/* ── Key Metrics Cards ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {/* Active Projects */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex items-center gap-4">
          <div className="p-3 bg-blue-50 rounded-xl text-blue-600 border border-blue-200">
            <BriefcaseIcon className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Active Projects</span>
            <div className="text-2xl font-black text-gray-900 mt-0.5">{totalActive}</div>
            <span className="text-xs text-gray-500 font-medium">Contracts ready for work log</span>
          </div>
        </div>

        {/* Total Contract Value */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex items-center gap-4">
          <div className="p-3 bg-blue-50 rounded-xl text-blue-600 border border-blue-200">
            <CurrencyDollarIcon className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Total Contract Value</span>
            <div className="text-2xl font-black text-gray-900 mt-0.5">${totalBudget.toLocaleString()}</div>
            <span className="text-xs text-gray-500 font-medium">Across active engagements</span>
          </div>
        </div>

        {/* Completed Projects */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex items-center gap-4">
          <div className="p-3 bg-gray-100 rounded-xl text-gray-700 border border-gray-200">
            <CheckCircleIcon className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Completed Projects</span>
            <div className="text-2xl font-black text-gray-900 mt-0.5">{completedContracts.length}</div>
            <span className="text-xs text-gray-500 font-medium">Finished milestones & reports</span>
          </div>
        </div>
      </div>

      {/* ── Search & Filter Controls ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-96">
          <MagnifyingGlassIcon className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search contracts or clients..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-xs font-medium text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-2xs"
          />
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-1.5 p-1 bg-gray-100 rounded-xl text-xs font-bold text-gray-600 w-full sm:w-auto overflow-x-auto">
          {[
            { key: 'ALL', label: 'All Projects', count: contracts.length },
            { key: 'ACTIVE', label: 'Active', count: activeContracts.length },
            { key: 'COMPLETED', label: 'Completed', count: completedContracts.length },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap ${statusFilter === tab.key
                  ? 'bg-white text-gray-900 shadow-xs'
                  : 'hover:text-gray-900'
                }`}
            >
              {tab.label}
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${statusFilter === tab.key ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Contracts Grid ────────────────────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-3xl border border-gray-150 p-6 space-y-4 shadow-xs">
              <div className="flex justify-between items-start">
                <Skeleton className="h-6 w-3/4 rounded-xl" />
                <Skeleton className="h-6 w-20 rounded-full" />
              </div>
              <Skeleton className="h-10 w-full rounded-xl" />
              <div className="pt-2 border-t border-gray-100 flex justify-between items-center">
                <Skeleton className="h-5 w-24 rounded-md" />
                <Skeleton className="h-9 w-28 rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredContracts.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-3xl border border-gray-200 p-8 shadow-sm">
          <BriefcaseIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-900">No active work contracts found</h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto mt-1">
            When a client accepts your bid or hires you on a project, your worklog workspace will appear here.
          </p>
          <button
            onClick={() => navigate('/freelancer/browse')}
            className="mt-5 inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all"
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
                className="bg-white rounded-3xl border border-gray-200 p-6 shadow-sm hover:shadow-lg hover:border-blue-200 transition-all duration-300 flex flex-col justify-between group"
              >
                <div>
                  {/* Top Status & Badge */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`px-2.5 py-1 rounded-full text-[11px] font-extrabold tracking-wide uppercase ${isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'bg-gray-100 text-gray-600'
                      }`}>
                      {contract.status || 'ACTIVE'}
                    </span>
                    <span className="text-[11px] text-gray-400 font-medium">
                      #{contract.id}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <h3 className="text-base font-bold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                    {projectTitle}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                    {contract.project?.description || contract.description || 'Active milestone workspace with progress tracking enabled.'}
                  </p>

                  {/* Client and Rate Details */}
                  <div className="mt-5 pt-4 border-t border-gray-100 space-y-2 text-xs text-gray-600">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2 text-gray-500">
                        {contract.client?.avatar ? (
                          <img
                            src={contract.client.avatar}
                            alt={clientName}
                            className="w-6 h-6 rounded-full object-cover border border-gray-200"
                          />
                        ) : (
                          <UserCircleIcon className="w-4 h-4" />
                        )}
                        Client:
                      </span>
                      <span className="font-semibold text-gray-900">{clientName}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-500">Contract Budget:</span>
                      <span className="font-bold text-blue-600 text-sm">
                        ${parseFloat(amount).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Action Button */}
                <div className="mt-6 pt-4 border-t border-gray-100">
                  <button
                    onClick={() => navigate(`/freelancer/worklogs/${contract.id}`)}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold shadow-md shadow-blue-600/20 transition-all active:scale-98"
                  >
                    <SparklesIcon className="w-4 h-4 text-blue-200" />
                    Log Work (AI & Manual)
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
