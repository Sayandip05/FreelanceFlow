import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ScrollText, Briefcase, Search, Filter, ArrowRight,
  ShieldCheck, CheckCircle2, Clock, AlertTriangle,
  DollarSign, User, MessageSquare, PlusCircle, ExternalLink,
  ChevronRight, Sparkles, RefreshCw
} from 'lucide-react'
import { contractsAPI } from '../../api/bids'
import { formatCurrency } from '../../utils/formatCurrency'

export default function FreelancerContractsPage() {
  const navigate = useNavigate()
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeTab, setActiveTab] = useState('all')

  useEffect(() => {
    fetchContracts()
  }, [])

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

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-gray-900 via-primary-950 to-indigo-950 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold text-primary-200 border border-white/10">
            <ShieldCheck className="w-3.5 h-3.5 text-primary-300" />
            Razorpay Escrow Protected
          </div>
          <h1 className="text-3xl font-black tracking-tight">My Freelance Contracts</h1>
          <p className="text-sm text-primary-200 max-w-xl">
            Track your active client contracts, check escrow-funded milestone stages, submit deliverables, and track payments.
          </p>
        </div>

        <div className="flex items-center gap-3 relative z-10 flex-shrink-0">
          <button
            onClick={() => navigate('/freelancer/browse')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white text-gray-900 text-sm font-bold hover:bg-gray-50 transition-all shadow-md active:scale-95"
          >
            <Briefcase className="w-4 h-4 text-primary-600" /> Browse Projects
          </button>
        </div>

        {/* Decorative background blur */}
        <div className="absolute -right-16 -bottom-16 w-64 h-64 bg-primary-500/20 rounded-full blur-3xl pointer-events-none" />
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
            <p className="text-2xl font-black text-emerald-600">{activeContractsCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 flex-shrink-0">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Completed</p>
            <p className="text-2xl font-black text-blue-600">{completedContractsCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600 flex-shrink-0">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Value</p>
            <p className="text-xl font-black text-gray-900">{formatCurrency(totalEarningsPotential)}</p>
          </div>
        </div>
      </div>

      {/* ── Search & Filter Toolbar ─────────────────────────────────────── */}
      <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by project title, client name..."
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
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
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === tab.id
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* ── Contract Cards List ─────────────────────────────────────────── */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border border-gray-100 p-6 space-y-4 animate-pulse">
              <div className="h-6 bg-gray-200 rounded-md w-1/3" />
              <div className="h-4 bg-gray-100 rounded-md w-1/2" />
              <div className="h-10 bg-gray-100 rounded-xl" />
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
          <button
            onClick={() => navigate('/freelancer/browse')}
            className="px-6 py-2.5 btn-primary text-sm font-bold inline-flex items-center gap-2"
          >
            <Briefcase className="w-4 h-4" /> Browse Projects
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredContracts.map((contract) => {
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
                className="bg-white rounded-2xl border border-gray-200/80 hover:border-primary-300 hover:shadow-lg transition-all duration-200 overflow-hidden group"
              >
                <div className="p-6">
                  {/* Top row */}
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-2.5">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 ${
                        contract.is_active
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-blue-50 text-blue-700 border border-blue-200'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${contract.is_active ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500'}`} />
                        {contract.is_active ? 'Active Contract' : 'Completed'}
                      </span>
                      <span className="text-xs font-medium text-gray-400">
                        Contract #{contract.id}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-xs font-semibold text-primary-700 bg-primary-50/80 px-3 py-1 rounded-lg border border-primary-100">
                      <ShieldCheck className="w-3.5 h-3.5 text-primary-600" />
                      Razorpay Escrow Protected
                    </div>
                  </div>

                  {/* Project Title & Client */}
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-gray-100">
                    <div className="space-y-2 flex-1 min-w-0">
                      <button
                        onClick={() => navigate(`/freelancer/contracts/${contract.id}`)}
                        className="text-xl font-bold text-gray-900 hover:text-primary-600 transition-colors text-left truncate block max-w-2xl"
                      >
                        {project.title || `Contract #${contract.id}`}
                      </button>

                      {/* Client Info */}
                      <div className="flex items-center gap-3">
                        {client.profile_photo ? (
                          <img
                            src={client.profile_photo}
                            alt={clientName}
                            className="w-8 h-8 rounded-full object-cover border border-gray-200"
                          />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-primary-600 text-white text-xs font-bold flex items-center justify-center">
                            {initials}
                          </div>
                        )}
                        <div>
                          <p className="text-xs font-bold text-gray-800">{clientName}</p>
                          <p className="text-[11px] text-gray-500">{client.email}</p>
                        </div>
                      </div>
                    </div>

                    {/* Contract Details Grid */}
                    <div className="grid grid-cols-3 gap-4 bg-gray-50/80 rounded-2xl p-4 border border-gray-100 text-center flex-shrink-0">
                      <div>
                        <p className="text-[11px] font-semibold text-gray-400 uppercase">Total Amount</p>
                        <p className="text-base font-black text-gray-900 mt-0.5">{formatCurrency(budget)}</p>
                      </div>
                      <div className="border-x border-gray-200 px-3">
                        <p className="text-[11px] font-semibold text-gray-400 uppercase">Contract Type</p>
                        <p className="text-xs font-bold text-primary-600 mt-1">Milestone-wise</p>
                      </div>
                      <div>
                        <p className="text-[11px] font-semibold text-gray-400 uppercase">Deadline</p>
                        <p className="text-xs font-bold text-gray-800 mt-1">{deadline}</p>
                      </div>
                    </div>
                  </div>

                  {/* Actions & Navigation Footer */}
                  <div className="flex flex-wrap items-center justify-between gap-4 pt-4">
                    <div className="flex items-center gap-2 text-xs text-gray-500 font-medium">
                      <Clock className="w-3.5 h-3.5 text-gray-400" />
                      Started on {startDate}
                    </div>

                    <div className="flex items-center gap-2.5">
                      <button
                        onClick={() => navigate(`/freelancer/messages?client=${client.id}`)}
                        className="p-2.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-xl transition-colors text-xs font-semibold flex items-center gap-1.5"
                        title="Send Message"
                      >
                        <MessageSquare className="w-4 h-4" />
                        <span className="hidden sm:inline">Message</span>
                      </button>

                      <button
                        onClick={() => navigate(`/freelancer/contracts/${contract.id}`)}
                        className="px-5 py-2.5 btn-primary text-xs font-bold flex items-center gap-2 group-hover:scale-[1.02]"
                      >
                        View Contract & Milestones <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
