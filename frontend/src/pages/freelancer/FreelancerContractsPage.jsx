import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ScrollText, Briefcase, Search, Filter, ArrowRight,
  ShieldCheck, CheckCircle2, Clock, AlertTriangle,
  DollarSign, User, MessageSquare, PlusCircle, ExternalLink,
  ChevronRight, Sparkles, RefreshCw, ChevronLeft, Calendar
} from 'lucide-react'
import { contractsAPI } from '../../api/bids'
import { formatCurrency } from '../../utils/formatCurrency'

const ITEMS_PER_PAGE = 12

export default function FreelancerContractsPage() {
  const navigate = useNavigate()
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    fetchContracts()
  }, [])

  // Reset to first page whenever search term or tab filter changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, activeTab])

  const fetchContracts = async () => {
    setLoading(true)
    try {
      const res = await contractsAPI.getContracts()
      setContracts(res.data?.results || res.data || [])
    } catch (e) {
      console.error('Failed to fetch freelancer contracts:', e)
    } finally {
      setLoading(false)
    }
  }

  // Filter contracts
  const filteredContracts = contracts.filter((c) => {
    const projectTitle = c.project?.title || c.bid?.project?.title || ''
    const clientName = c.client
      ? `${c.client.first_name || ''} ${c.client.last_name || ''}`.trim()
      : c.bid?.project?.client
        ? `${c.bid.project.client.first_name || ''} ${c.bid.project.client.last_name || ''}`.trim()
        : ''
    const clientEmail = c.client?.email || c.bid?.project?.client?.email || ''

    const matchesSearch =
      projectTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
      clientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      clientEmail.toLowerCase().includes(searchTerm.toLowerCase())

    if (!matchesSearch) return false

    if (activeTab === 'active') return c.is_active
    if (activeTab === 'completed') return !c.is_active
    return true
  })

  // Metrics
  const totalContracts = contracts.length
  const activeContractsCount = contracts.filter((c) => c.is_active).length
  const completedContractsCount = contracts.filter((c) => !c.is_active).length
  const totalEarningsPotential = contracts.reduce((sum, c) => sum + parseFloat(c.agreed_amount || 0), 0)

  // Pagination calculation
  const totalPages = Math.ceil(filteredContracts.length / ITEMS_PER_PAGE) || 1
  const paginatedContracts = filteredContracts.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
          My Freelance Contracts
        </h1>
      </div>

      {/* ── Stats Summary Grid ──────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center text-primary-600 flex-shrink-0">
            <ScrollText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Contracts</p>
            <p className="text-2xl font-black text-gray-900">{totalContracts}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 flex-shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Active Contracts</p>
            <p className="text-2xl font-black text-gray-900">{activeContractsCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 flex-shrink-0">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Completed</p>
            <p className="text-2xl font-black text-gray-900">{completedContractsCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600 flex-shrink-0">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Value</p>
            <p className="text-2xl font-black text-gray-900">{formatCurrency(totalEarningsPotential)}</p>
          </div>
        </div>
      </div>

      {/* ── Search & Filter Controls ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by project title, client name..."
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-2xs"
          />
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-xl self-start md:self-auto">
          {[
            { id: 'all', label: 'All Contracts', count: totalContracts },
            { id: 'active', label: 'Active', count: activeContractsCount },
            { id: 'completed', label: 'Completed', count: completedContractsCount },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === tab.id
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-800'
                }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* ── Boxy 3-Columns Grid of Contracts (3 Boxes per row, up to 12 per page) ── */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-3xl border border-gray-200 p-6 space-y-4 animate-pulse">
              <div className="h-6 bg-gray-200 rounded-md w-1/3" />
              <div className="h-5 bg-gray-100 rounded-md w-3/4" />
              <div className="h-4 bg-gray-100 rounded-md w-full" />
              <div className="h-10 bg-gray-100 rounded-xl mt-4" />
            </div>
          ))}
        </div>
      ) : filteredContracts.length === 0 ? (
        <div className="bg-white rounded-3xl border border-gray-100 p-12 text-center space-y-4 shadow-sm">
          <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600 mx-auto">
            <ScrollText className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">No contracts found</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            {searchTerm
              ? 'Try modifying your search keywords to find your contracts.'
              : 'Submit proposals on open projects. Once a client accepts your bid, your contract will appear here.'}
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* 3 boxes per line grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedContracts.map((contract) => {
              const project = contract.project || contract.bid?.project || {}
              const client = contract.client || contract.bid?.project?.client || {}
              const clientName = `${client.first_name || ''} ${client.last_name || ''}`.trim() || client.email?.split('@')[0] || 'Client'
              const initials = [client.first_name?.[0], client.last_name?.[0]].filter(Boolean).join('').toUpperCase() || 'CL'
              const budget = contract.agreed_amount || project.budget || 0
              const startDate = contract.start_date ? new Date(contract.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'
              const deadline = project.deadline ? new Date(project.deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Flexible'

              return (
                <div
                  key={contract.id}
                  className="bg-white rounded-3xl border border-gray-200/90 hover:border-primary-300 hover:shadow-lg transition-all duration-300 p-6 flex flex-col justify-between group shadow-sm"
                >
                  <div>
                    {/* Top row: Status & Contract # */}
                    <div className="flex items-center justify-between gap-3 mb-3.5">
                      <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold flex items-center gap-1.5 ${contract.is_active
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-blue-50 text-blue-700 border border-blue-200'
                        }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${contract.is_active ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500'}`} />
                        {contract.is_active ? 'Active Contract' : 'Completed'}
                      </span>
                      <span className="text-xs font-semibold text-gray-400">
                        #{contract.id}
                      </span>
                    </div>

                    {/* Project Title */}
                    <h3
                      onClick={() => navigate(`/freelancer/contracts/${contract.id}`)}
                      className="text-base font-bold text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-1 cursor-pointer"
                    >
                      {project.title || `Contract #${contract.id}`}
                    </h3>

                    {/* Description preview */}
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                      {project.description || 'Active milestone workspace with progress and deliverable tracking.'}
                    </p>

                    {/* Client Info Bar */}
                    <div className="mt-4 pt-3.5 border-t border-gray-100 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5 min-w-0">
                        {client.profile_photo ? (
                          <img
                            src={client.profile_photo}
                            alt={clientName}
                            className="w-7 h-7 rounded-full object-cover border border-gray-200 shrink-0"
                          />
                        ) : (
                          <div className="w-7 h-7 rounded-full bg-primary-600 text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                            {initials}
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-gray-800 truncate">{clientName}</p>
                          <p className="text-[10px] text-gray-400 truncate">{client.email}</p>
                        </div>
                      </div>

                      <button
                        onClick={() => navigate(`/freelancer/messages?client=${client.id}`)}
                        className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors shrink-0"
                        title="Message Client"
                      >
                        <MessageSquare className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Contract Budget & Deadline row */}
                    <div className="mt-3.5 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-gray-400 block">Total Budget</span>
                        <span className="text-base font-black text-gray-900">{formatCurrency(budget)}</span>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] uppercase font-bold text-gray-400 block">Deadline</span>
                        <span className="text-xs font-bold text-gray-700">{deadline}</span>
                      </div>
                    </div>
                  </div>

                  {/* Action Button at bottom */}
                  <div className="mt-5 pt-3 border-t border-gray-100">
                    <button
                      onClick={() => navigate(`/freelancer/contracts/${contract.id}`)}
                      className="w-full py-2.5 px-4 btn-primary text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-sm active:scale-98 transition-all"
                    >
                      View Contract & Milestones <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* ── Standard Numbered Pagination (1, 2, 3... with Arrows) ── */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-6">
              {/* Prev Button */}
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2.5 rounded-xl border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:pointer-events-none transition-colors shadow-2xs"
                title="Previous Page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              {/* Number Buttons */}
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`w-9 h-9 rounded-xl text-xs font-bold transition-all ${
                    currentPage === pageNum
                      ? 'bg-primary-600 text-white shadow-md shadow-primary-500/20'
                      : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              ))}

              {/* Next Button */}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2.5 rounded-xl border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:pointer-events-none transition-colors shadow-2xs"
                title="Next Page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
