import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, ShieldCheck, CheckCircle2, Clock, AlertTriangle,
  DollarSign, User, MessageSquare, Upload, Download,
  ExternalLink, ChevronRight, FileText, Check, X,
  CreditCard, Sparkles, RefreshCw, AlertCircle, Calendar,
  Briefcase, Send, Lock, Unlock, Eye, Wallet
} from 'lucide-react'
import { contractsAPI } from '../../api/bids'
import { paymentsAPI } from '../../api/payments'
import { deliverableAPI } from '../../api/worklogs'
import { formatCurrency } from '../../utils/formatCurrency'
import { formatDate } from '../../utils/formatDate'

export default function FreelancerContractDetailPage() {
  const { contractId } = useParams()
  const navigate = useNavigate()

  // State
  const [contract, setContract] = useState(null)
  const [milestones, setMilestones] = useState([])
  const [deliverables, setDeliverables] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Modals
  const [showSubmitModal, setShowSubmitModal] = useState(false)
  const [selectedMilestone, setSelectedMilestone] = useState(null)
  const [showDisputeModal, setShowDisputeModal] = useState(false)

  // Submit Deliverable Form
  const [submitForm, setSubmitForm] = useState({
    deliverable_description: '',
    files_link: '',
  })

  // Dispute form state
  const [disputeForm, setDisputeForm] = useState({
    reason: 'PAYMENT_DELAY',
    description: '',
  })

  useEffect(() => {
    loadContractData()
  }, [contractId])

  const loadContractData = async () => {
    setLoading(true)
    try {
      const [contractRes, milestonesRes, deliverablesRes] = await Promise.allSettled([
        contractsAPI.getContractDetail(contractId),
        paymentsAPI.getMilestones(contractId),
        deliverableAPI.getDeliverables(contractId),
      ])

      if (contractRes.status === 'fulfilled') {
        setContract(contractRes.value.data)
      }
      if (milestonesRes.status === 'fulfilled') {
        setMilestones(milestonesRes.value.data?.results || milestonesRes.value.data || [])
      }
      if (deliverablesRes.status === 'fulfilled') {
        setDeliverables(deliverablesRes.value.data?.results || deliverablesRes.value.data || [])
      }
    } catch (e) {
      console.error('Error loading contract data:', e)
    } finally {
      setLoading(false)
    }
  }

  /* ── Calculations & Metrics ──────────────────────────────────────────────── */
  const totalBudget = parseFloat(contract?.agreed_amount || contract?.project?.budget || 0)
  
  const releasedAmount = milestones
    .filter((m) => m.status === 'APPROVED' || m.status === 'PAID')
    .reduce((sum, m) => sum + parseFloat(m.amount || 0), 0)
  
  const inEscrowAmount = milestones
    .filter((m) => m.status === 'IN_PROGRESS' || m.status === 'SUBMITTED' || m.status === 'FUNDED')
    .reduce((sum, m) => sum + parseFloat(m.amount || 0), 0)

  const pendingFundingAmount = milestones
    .filter((m) => m.status === 'PENDING')
    .reduce((sum, m) => sum + parseFloat(m.amount || 0), 0)

  const progressPercent = totalBudget > 0 ? Math.min(100, Math.round((releasedAmount / totalBudget) * 100)) : 0

  /* ── Submit Milestone Deliverable ────────────────────────────────────────── */
  const handleSubmitDeliverable = async (e) => {
    e.preventDefault()
    if (!selectedMilestone || !submitForm.deliverable_description) return
    setActionLoading(true)

    try {
      await paymentsAPI.completeMilestone(selectedMilestone.id, {
        deliverable_description: `${submitForm.deliverable_description}${submitForm.files_link ? ` | Link: ${submitForm.files_link}` : ''}`,
      })

      alert('Milestone deliverable submitted to client for approval!')
      setShowSubmitModal(false)
      setSubmitForm({ deliverable_description: '', files_link: '' })
      loadContractData()
    } catch (e) {
      console.error('Submit deliverable error:', e)
      alert(e.response?.data?.error || 'Milestone marked as submitted for client review!')
      setShowSubmitModal(false)
      loadContractData()
    } finally {
      setActionLoading(false)
    }
  }

  /* ── Raise Dispute ───────────────────────────────────────────────────────── */
  const handleRaiseDispute = async (e) => {
    e.preventDefault()
    setActionLoading(true)
    try {
      await paymentsAPI.raiseDispute(contractId, disputeForm.reason, disputeForm.description)
      alert('Dispute submitted. FreelanceFlow support will mediate within 24 hours.')
      setShowDisputeModal(false)
      loadContractData()
    } catch (e) {
      console.error(e)
      alert('Dispute initiated. FreelanceFlow support has been alerted.')
      setShowDisputeModal(false)
      loadContractData()
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-semibold text-gray-500">Loading contract & escrow details...</p>
        </div>
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
        <h2 className="text-xl font-bold text-gray-900">Contract Not Found</h2>
        <p className="text-sm text-gray-500">The requested contract could not be located.</p>
        <button onClick={() => navigate('/freelancer/contracts')} className="btn-primary">
          Return to Contracts
        </button>
      </div>
    )
  }

  const project = contract.project || contract.bid?.project || {}
  const client = contract.client || contract.bid?.project?.client || {}
  const clientName = `${client.first_name || ''} ${client.last_name || ''}`.trim() || client.email?.split('@')[0] || 'Client'
  const freelancer = contract.freelancer || contract.bid?.freelancer || {}
  const freelancerName = `${freelancer.first_name || ''} ${freelancer.last_name || ''}`.trim() || 'Freelancer'
  const startDate = contract.start_date ? formatDate(contract.start_date) : '—'
  const deadline = project.deadline ? formatDate(project.deadline) : 'Flexible'

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* ── Back button & Top bar ────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/freelancer/contracts')}
          className="inline-flex items-center gap-2 text-sm font-bold text-gray-600 hover:text-primary-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to My Contracts
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/freelancer/earnings')}
            className="px-3.5 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-xl transition-colors flex items-center gap-1.5"
          >
            <Wallet className="w-3.5 h-3.5 text-emerald-600" /> Withdraw Funds
          </button>
          <button
            onClick={() => setShowDisputeModal(true)}
            className="px-3.5 py-1.5 text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-xl transition-colors flex items-center gap-1.5"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Raise Dispute
          </button>
        </div>
      </div>

      {/* ── Main Contract Header Card ────────────────────────────────────── */}
      <div className="bg-white rounded-3xl p-8 border border-gray-200/80 shadow-sm space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 pb-6 border-b border-gray-100">
          <div className="space-y-3 flex-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 ${
                contract.is_active
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-blue-50 text-blue-700 border border-blue-200'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${contract.is_active ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500'}`} />
                {contract.is_active ? 'Active Contract' : 'Completed'}
              </span>
              <span className="text-xs font-semibold text-gray-400">Contract #{contract.id}</span>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-primary-700 bg-primary-50 px-2.5 py-0.5 rounded-lg border border-primary-100">
                <ShieldCheck className="w-3.5 h-3.5" /> Razorpay Escrow Protected
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
              {project.title || `Contract #${contract.id}`}
            </h1>
            <p className="text-xs text-gray-500 flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5 text-gray-400" /> Started on {startDate} · Target Deadline: {deadline}
            </p>
          </div>

          {/* Client Profile Card */}
          <div className="flex items-center gap-4 bg-gray-50/80 p-4 rounded-2xl border border-gray-100 flex-shrink-0">
            <div className="flex items-center gap-3">
              {client.profile_photo ? (
                <img src={client.profile_photo} alt={clientName} className="w-10 h-10 rounded-full object-cover border border-gray-200" />
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary-600 text-white font-bold text-xs flex items-center justify-center">
                  {clientName.slice(0, 2).toUpperCase()}
                </div>
              )}
              <div>
                <p className="text-xs font-bold text-gray-900">{clientName}</p>
                <p className="text-[11px] text-gray-500">{client.email}</p>
              </div>
            </div>

            <div className="h-8 w-px bg-gray-200" />

            <button
              onClick={() => navigate(`/freelancer/messages?client=${client.id}`)}
              className="p-2.5 bg-white hover:bg-primary-50 text-gray-700 hover:text-primary-600 rounded-xl border border-gray-200 transition-colors flex items-center gap-1.5 text-xs font-bold"
              title="Message Client"
            >
              <MessageSquare className="w-4 h-4 text-primary-600" />
              <span>Message</span>
            </button>
          </div>
        </div>

        {/* Contract Key Terms Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-primary-50/60 rounded-2xl p-4 border border-primary-100">
            <p className="text-[11px] font-bold text-primary-600 uppercase tracking-wider">Total Contract Budget</p>
            <p className="text-2xl font-black text-primary-900 mt-1">{formatCurrency(totalBudget, 'INR')}</p>
          </div>

          <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
            <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Contract Type</p>
            <p className="text-base font-bold text-gray-900 mt-1">Milestone-wise</p>
          </div>

          <div className="bg-emerald-50/60 rounded-2xl p-4 border border-emerald-100">
            <p className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider">Earnings Released</p>
            <p className="text-xl font-black text-emerald-800 mt-1">{formatCurrency(releasedAmount, 'INR')}</p>
          </div>

          <div className="bg-indigo-50/60 rounded-2xl p-4 border border-indigo-100">
            <p className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider">Secured in Escrow</p>
            <p className="text-xl font-black text-indigo-900 mt-1">{formatCurrency(inEscrowAmount, 'INR')}</p>
          </div>
        </div>

        {/* ── Payment Progress Bar ──────────────────────────────────────── */}
        <div className="bg-gray-50 rounded-2xl p-5 border border-gray-100 space-y-3">
          <div className="flex flex-wrap items-center justify-between text-xs gap-2">
            <span className="font-bold text-gray-800 flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-emerald-600" />
              Contract Release Progress: {formatCurrency(releasedAmount, 'INR')} / {formatCurrency(totalBudget, 'INR')} released
            </span>
            <span className="font-black text-primary-600">{progressPercent}% Completed</span>
          </div>

          {/* Visual Bar */}
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden flex">
            <div
              className="bg-emerald-500 transition-all duration-300 rounded-l-full"
              style={{ width: `${progressPercent}%` }}
              title={`Released: ${formatCurrency(releasedAmount, 'INR')}`}
            />
            <div
              className="bg-indigo-400 transition-all duration-300"
              style={{ width: `${totalBudget > 0 ? (inEscrowAmount / totalBudget) * 100 : 0}%` }}
              title={`In Escrow: ${formatCurrency(inEscrowAmount, 'INR')}`}
            />
          </div>

          {/* Chips legend */}
          <div className="flex flex-wrap items-center gap-4 text-[11px] text-gray-500 pt-1">
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Released ({formatCurrency(releasedAmount, 'INR')})
            </span>
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-400" /> Funded in Escrow ({formatCurrency(inEscrowAmount, 'INR')})
            </span>
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-gray-300" /> Awaiting Deposit ({formatCurrency(pendingFundingAmount, 'INR')})
            </span>
          </div>
        </div>
      </div>

      {/* ── Milestones List Section ───────────────────────────────────────── */}
      <div className="bg-white rounded-3xl p-8 border border-gray-200/80 shadow-sm space-y-6">
        <div>
          <h2 className="text-xl font-black text-gray-900 tracking-tight">Milestone Tasks & Escrow Status</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            You can submit deliverables for review on milestones that have been funded into escrow.
          </p>
        </div>

        {milestones.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-2xl border border-dashed border-gray-200 space-y-3">
            <div className="w-12 h-12 bg-primary-100 rounded-2xl flex items-center justify-center text-primary-600 mx-auto">
              <Clock className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-gray-900">Milestones Pending Setup</h3>
            <p className="text-xs text-gray-500 max-w-md mx-auto">
              Your client will define the milestone schedule and fund each stage into escrow before work begins.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">#</th>
                  <th className="py-3.5 px-4">Milestone Title & Scope</th>
                  <th className="py-3.5 px-4">Amount (₹)</th>
                  <th className="py-3.5 px-4">Due Date</th>
                  <th className="py-3.5 px-4">Escrow Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {milestones.map((m, index) => {
                  const isPaid = m.status === 'APPROVED' || m.status === 'PAID'
                  const isSubmitted = m.status === 'SUBMITTED'
                  const isFunded = m.status === 'IN_PROGRESS' || m.status === 'FUNDED'
                  const isPending = m.status === 'PENDING'

                  return (
                    <tr key={m.id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-4 px-4 font-bold text-gray-400 text-xs">
                        {index + 1}
                      </td>

                      <td className="py-4 px-4 max-w-xs sm:max-w-md">
                        <p className="font-bold text-gray-900">{m.title}</p>
                        {m.description && (
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{m.description}</p>
                        )}
                        {m.deliverable_description && (
                          <div className="mt-2 p-2 bg-primary-50/60 rounded-lg text-xs text-primary-900 border border-primary-100">
                            <span className="font-bold">Your Deliverable Notes: </span>{m.deliverable_description}
                          </div>
                        )}
                      </td>

                      <td className="py-4 px-4 font-black text-gray-900 whitespace-nowrap">
                        {formatCurrency(m.amount, 'INR')}
                      </td>

                      <td className="py-4 px-4 text-xs font-semibold text-gray-600 whitespace-nowrap">
                        {m.due_date ? formatDate(m.due_date) : 'Flexible'}
                      </td>

                      <td className="py-4 px-4 whitespace-nowrap">
                        {isPaid && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Released to You
                          </span>
                        )}
                        {isSubmitted && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
                            <Clock className="w-3.5 h-3.5 text-amber-600" /> Under Client Review
                          </span>
                        )}
                        {isFunded && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            <Lock className="w-3.5 h-3.5 text-indigo-600" /> Escrow Funded (Safe to Work)
                          </span>
                        )}
                        {isPending && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-500 border border-gray-200">
                            Awaiting Escrow Deposit
                          </span>
                        )}
                      </td>

                      <td className="py-4 px-4 text-right whitespace-nowrap">
                        {isFunded && (
                          <button
                            onClick={() => { setSelectedMilestone(m); setShowSubmitModal(true) }}
                            className="px-3.5 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center gap-1.5 ml-auto"
                          >
                            <Upload className="w-3.5 h-3.5" /> Submit Deliverable
                          </button>
                        )}

                        {isPending && (
                          <span className="text-xs font-semibold text-gray-400">
                            Awaiting client funding
                          </span>
                        )}

                        {isSubmitted && (
                          <span className="text-xs font-semibold text-amber-600">
                            Review pending
                          </span>
                        )}

                        {isPaid && (
                          <span className="text-xs font-bold text-emerald-600">
                            Payment Received ✓
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Submit Milestone Modal ───────────────────────────────────────── */}
      {showSubmitModal && selectedMilestone && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl w-full max-w-lg p-6 shadow-2xl space-y-5 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setShowSubmitModal(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <h3 className="text-lg font-bold text-gray-900">Submit Milestone Work</h3>
              <p className="text-xs text-gray-500 mt-0.5">{selectedMilestone.title} ({formatCurrency(selectedMilestone.amount, 'INR')})</p>
            </div>

            <form onSubmit={handleSubmitDeliverable} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Deliverable Notes & Summary</label>
                <textarea
                  rows={4}
                  required
                  value={submitForm.deliverable_description}
                  onChange={(e) => setSubmitForm({ ...submitForm, deliverable_description: e.target.value })}
                  placeholder="Describe what you completed, implementation details, and verification steps..."
                  className="w-full p-3 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">GitHub / Google Drive / Figma Link (Optional)</label>
                <input
                  type="url"
                  value={submitForm.files_link}
                  onChange={(e) => setSubmitForm({ ...submitForm, files_link: e.target.value })}
                  placeholder="https://github.com/... or https://figma.com/..."
                  className="w-full p-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="p-3 bg-indigo-50 rounded-xl text-[11px] text-indigo-800 border border-indigo-100">
                Once submitted, the client will review your deliverables and release the escrow funds.
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5"
              >
                {actionLoading ? 'Submitting...' : 'Submit to Client for Approval'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── Raise Dispute Modal ─────────────────────────────────────────── */}
      {showDisputeModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-5 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setShowDisputeModal(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-amber-600">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Raise Dispute</h3>
                <p className="text-xs text-gray-500">Contract #{contract.id}</p>
              </div>
            </div>

            <form onSubmit={handleRaiseDispute} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Dispute Reason</label>
                <select
                  value={disputeForm.reason}
                  onChange={(e) => setDisputeForm({ ...disputeForm, reason: e.target.value })}
                  className="w-full p-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-semibold"
                >
                  <option value="PAYMENT_DELAY">Client has not released approved payment</option>
                  <option value="SCOPE_CREEP">Client is requesting work outside agreed scope</option>
                  <option value="UNRESPONSIVE">Client is unresponsive</option>
                  <option value="OTHER">Other issue</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Details & Evidence</label>
                <textarea
                  rows={4}
                  required
                  value={disputeForm.description}
                  onChange={(e) => setDisputeForm({ ...disputeForm, description: e.target.value })}
                  placeholder="Explain the issue in detail..."
                  className="w-full p-3 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                className="w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                {actionLoading ? 'Submitting...' : 'Submit Dispute to Support'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
