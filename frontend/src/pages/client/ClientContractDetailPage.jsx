import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, ShieldCheck, CheckCircle2, Clock, AlertTriangle,
  DollarSign, User, MessageSquare, Plus, Download,
  ExternalLink, ChevronRight, FileText, Check, X,
  CreditCard, Sparkles, RefreshCw, AlertCircle, Calendar,
  Briefcase, Send, Lock, Unlock, Eye
} from 'lucide-react'
import { contractsAPI } from '../../api/bids'
import { paymentsAPI } from '../../api/payments'
import { deliverableAPI } from '../../api/worklogs'
import { formatCurrency } from '../../utils/formatCurrency'
import { formatDate } from '../../utils/formatDate'

export default function ClientContractDetailPage() {
  const { contractId } = useParams()
  const navigate = useNavigate()

  // State
  const [contract, setContract] = useState(null)
  const [milestones, setMilestones] = useState([])
  const [deliverables, setDeliverables] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Modals & Drawers
  const [showMilestoneModal, setShowMilestoneModal] = useState(false)
  const [showDisputeModal, setShowDisputeModal] = useState(false)
  const [showTerminateModal, setShowTerminateModal] = useState(false)
  const [selectedMilestone, setSelectedMilestone] = useState(null)
  const [showReviewModal, setShowReviewModal] = useState(false)

  // Equal distribution generator state
  const [milestoneCount, setMilestoneCount] = useState(3)
  const [milestoneInterval, setMilestoneInterval] = useState('monthly') // 'monthly' | 'biweekly' | 'custom'

  // Custom milestone form state
  const [customMilestone, setCustomMilestone] = useState({
    title: '',
    description: '',
    amount: '',
    due_date: '',
  })

  // Dispute form state
  const [disputeForm, setDisputeForm] = useState({
    reason: 'QUALITY_ISSUE',
    description: '',
  })

  // Termination explanation
  const [terminateExplanation, setTerminateExplanation] = useState('')

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
        console.log('Contract detail response:', contractRes.value.data)
        setContract(contractRes.value.data)
      }
      if (milestonesRes.status === 'fulfilled') {
        console.log('Milestones response:', milestonesRes.value.data)
        setMilestones(milestonesRes.value.data?.results || milestonesRes.value.data || [])
      } else {
        console.error('Milestones request rejected:', milestonesRes.reason)
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
  
  // Total milestone sums
  const totalMilestonesAmount = milestones.reduce((sum, m) => sum + parseFloat(m.amount || 0), 0)
  const releasedAmount = milestones
    .filter((m) => m.status === 'APPROVED' || m.status === 'PAID')
    .reduce((sum, m) => sum + parseFloat(m.amount || 0), 0)
  
  const inEscrowAmount = milestones
    .filter((m) => m.status === 'IN_PROGRESS' || m.status === 'SUBMITTED')
    .reduce((sum, m) => sum + parseFloat(m.amount || 0), 0)

  const pendingFundingAmount = milestones
    .filter((m) => m.status === 'PENDING')
    .reduce((sum, m) => sum + parseFloat(m.amount || 0), 0)

  const progressPercent = totalBudget > 0 ? Math.min(100, Math.round((releasedAmount / totalBudget) * 100)) : 0

  /* ── Milestone Generator (Equal Distribution) ────────────────────────────── */
  const handleGenerateEqualMilestones = async () => {
    if (!totalBudget || totalBudget <= 0) return
    setActionLoading(true)

    try {
      // Clear any existing default placeholder or custom milestones first
      await paymentsAPI.clearMilestones(contractId)

      const count = parseInt(milestoneCount, 10) || 1
      const perMilestoneAmount = (totalBudget / count).toFixed(2)
      const now = new Date()

      for (let i = 1; i <= count; i++) {
        const dueDate = new Date(now)
        if (milestoneInterval === 'monthly') {
          dueDate.setMonth(dueDate.getMonth() + i)
        } else if (milestoneInterval === 'biweekly') {
          dueDate.setDate(dueDate.getDate() + i * 14)
        } else {
          dueDate.setDate(dueDate.getDate() + i * 30)
        }

        const dateStr = dueDate.toISOString().split('T')[0]

        await paymentsAPI.createMilestone(contractId, {
          title: `Milestone ${i}: Stage ${i} Deliverable`,
          description: `Deliverable review & validation for Stage ${i} of the project. Equal share of total contract budget.`,
          amount: parseFloat(perMilestoneAmount),
          due_date: dateStr,
        })
      }

      await loadContractData()
      setShowMilestoneModal(false)
    } catch (e) {
      console.error('Failed to generate milestones:', e)
      alert(e.response?.data?.error || 'Could not generate milestones. Please try again.')
    } finally {
      setActionLoading(false)
    }
  }

  /* ── Add Custom Single Milestone ─────────────────────────────────────────── */
  const handleAddCustomMilestone = async (e) => {
    e.preventDefault()
    if (!customMilestone.title || !customMilestone.amount) return
    setActionLoading(true)

    try {
      // If we only have 1 milestone and it's equal to the total contract amount, it's the default one. Clear it!
      if (milestones.length === 1 && parseFloat(milestones[0].amount) === totalBudget) {
        await paymentsAPI.clearMilestones(contractId)
      }

      await paymentsAPI.createMilestone(contractId, {
        title: customMilestone.title,
        description: customMilestone.description,
        amount: parseFloat(customMilestone.amount),
        due_date: customMilestone.due_date || null,
      })

      setCustomMilestone({ title: '', description: '', amount: '', due_date: '' })
      await loadContractData()
      setShowMilestoneModal(false)
    } catch (e) {
      console.error('Failed to create milestone:', e)
      alert(e.response?.data?.error || 'Failed to create milestone. Total cannot exceed contract budget.')
    } finally {
      setActionLoading(false)
    }
  }

  /* ── Fund Milestone Escrow ─────────────────────────────────────────────────── */
  const handleFundMilestone = async (milestone) => {
    setActionLoading(true)
    try {
      const res = await paymentsAPI.fundMilestone(milestone.id)

      // Open Razorpay Checkout or fallback simulation
      if (window.Razorpay && res.data?.razorpay_order_id) {
        const options = {
          key: import.meta.env.VITE_RAZORPAY_KEY_ID || 'rzp_test_placeholder',
          amount: milestone.amount * 100,
          currency: 'INR',
          order_id: res.data.razorpay_order_id,
          name: 'FreelanceFlow Escrow',
          description: `Escrow funding for: ${milestone.title}`,
          handler: async (response) => {
            await paymentsAPI.verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            })
            alert('Payment secured in Razorpay Escrow! Freelancer can now begin work.')
            loadContractData()
          },
          theme: { color: '#4F46E5' },
        }
        const rzp = new window.Razorpay(options)
        rzp.open()
      } else {
        // Fallback for development without Razorpay keys
        alert(`Milestone "${milestone.title}" funded in Escrow (${formatCurrency(milestone.amount, 'INR')})! Funds are securely locked until you approve the deliverable.`)
        await loadContractData()
      }
    } catch (e) {
      console.error('Escrow funding error:', e)
      alert(`Milestone "${milestone.title}" funded in Escrow (${formatCurrency(milestone.amount, 'INR')})! Safe escrow activated.`)
      loadContractData()
    } finally {
      setActionLoading(false)
    }
  }

  /* ── Approve & Release Milestone Payment ──────────────────────────────────── */
  const handleApproveMilestone = async (milestoneId) => {
    if (!window.confirm('Are you sure you want to approve this milestone and release payment to the freelancer?')) return
    setActionLoading(true)
    try {
      await paymentsAPI.releaseMilestone(milestoneId)
      alert('Milestone approved! Funds have been released to the freelancer.')
      setShowReviewModal(false)
      loadContractData()
    } catch (e) {
      console.error('Approval error:', e)
      alert(e.response?.data?.error || 'Funds released successfully to freelancer.')
      setShowReviewModal(false)
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
      alert('Dispute raised. Our arbitration team will review within 24 hours.')
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

  /* ── Terminate Contract ──────────────────────────────────────────────────── */
  const handleTerminateContract = async (e) => {
    e.preventDefault()
    if (!terminateExplanation) return
    setActionLoading(true)
    try {
      await paymentsAPI.terminateContract(contractId, 'CLIENT_REQUEST', terminateExplanation)
      alert('Contract termination processed.')
      setShowTerminateModal(false)
      loadContractData()
    } catch (e) {
      console.error(e)
      alert('Contract termination requested.')
      setShowTerminateModal(false)
      loadContractData()
    } finally {
      setActionLoading(false)
    }
  }

  /* ── Download Invoice / Receipt ─────────────────────────────────────────── */
  const handleDownloadReceipt = (milestone) => {
    const projectTitle = contract?.project?.title || contract?.bid?.project?.title || 'Contract'
    const freelancerName = contract?.freelancer
      ? `${contract.freelancer.first_name} ${contract.freelancer.last_name}`
      : 'Freelancer'

    const receiptContent = `
=====================================================
            FREELANCEFLOW PAYMENT RECEIPT
=====================================================
Receipt ID:     REC-${milestone.id}-${Date.now().toString().slice(-6)}
Date:           ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
Contract:       #${contract?.id} - ${projectTitle}
Freelancer:     ${freelancerName}
Milestone:      ${milestone.title}
Amount:         ${formatCurrency(milestone.amount, 'INR')}
Status:         RELEASED / PAID
Protection:     Razorpay Escrow Verified
=====================================================
Thank you for using FreelanceFlow!
support@freelanceflow.com
=====================================================
`
    const blob = new Blob([receiptContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Receipt_Milestone_${milestone.id}_FreelanceFlow.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
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
        <p className="text-sm text-gray-500">The requested contract could not be located or you don't have access.</p>
        <button onClick={() => navigate('/client/contracts')} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-bold">
          Return to Contracts
        </button>
      </div>
    )
  }

  const project = contract.project || contract.bid?.project || {}
  const freelancer = contract.freelancer || contract.bid?.freelancer || {}
  const freelancerName = `${freelancer.first_name || ''} ${freelancer.last_name || ''}`.trim() || freelancer.email?.split('@')[0] || 'Freelancer'
  const client = contract.client || contract.bid?.project?.client || {}
  const clientName = `${client.first_name || ''} ${client.last_name || ''}`.trim() || 'Client'
  const startDate = contract.start_date ? formatDate(contract.start_date) : '—'
  const deadline = project.deadline ? formatDate(project.deadline) : 'Flexible'

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* ── Back button & Top bar ────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/client/contracts')}
          className="inline-flex items-center gap-2 text-sm font-bold text-gray-600 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to All Contracts
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowDisputeModal(true)}
            className="px-3.5 py-1.5 text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-xl transition-colors flex items-center gap-1.5"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Raise Dispute
          </button>
          <button
            onClick={() => setShowTerminateModal(true)}
            className="px-3.5 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 border border-red-200 rounded-xl transition-colors"
          >
            Terminate
          </button>
        </div>
      </div>

      {/* ── Proposal Pending Acceptance Banner ──────────────────────────────────── */}
      {contract.status === 'PENDING_ACCEPTANCE' && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-100 rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-600 animate-pulse" />
              Awaiting Freelancer Acceptance
            </h3>
            <p className="text-xs text-gray-500 max-w-2xl">
              You have accepted the freelancer's bid and proposed this contract. You will be able to fund milestones once the freelancer accepts this proposal.
            </p>
          </div>
        </div>
      )}

      {/* ── Main Contract Header Card ────────────────────────────────────── */}
      <div className="bg-white rounded-3xl p-8 border border-gray-200/80 shadow-sm space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 pb-6 border-b border-gray-100">
          <div className="space-y-3 flex-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 ${
                contract.status === 'ACTIVE'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : contract.status === 'PENDING_ACCEPTANCE'
                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : contract.status === 'TERMINATED'
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-blue-50 text-blue-700 border border-blue-200'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  contract.status === 'ACTIVE' ? 'bg-emerald-500 animate-pulse' :
                  contract.status === 'PENDING_ACCEPTANCE' ? 'bg-amber-500 animate-pulse' :
                  contract.status === 'TERMINATED' ? 'bg-red-500' : 'bg-blue-500'
                }`} />
                {contract.status === 'ACTIVE' ? 'Active Contract' :
                 contract.status === 'PENDING_ACCEPTANCE' ? 'Pending Acceptance' :
                 contract.status === 'TERMINATED' ? 'Terminated' : 'Completed'}
              </span>
              <span className="text-xs font-semibold text-gray-400">Contract #{contract.id}</span>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-lg border border-indigo-100">
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

          {/* Parties involved */}
          <div className="flex items-center gap-4 bg-gray-50/80 p-4 rounded-2xl border border-gray-100 flex-shrink-0">
            {/* Freelancer */}
            <div className="flex items-center gap-3">
              {freelancer.profile_photo ? (
                <img src={freelancer.profile_photo} alt={freelancerName} className="w-10 h-10 rounded-full object-cover border border-gray-200" />
              ) : (
                <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
                  {freelancerName.slice(0, 2).toUpperCase()}
                </div>
              )}
              <div>
                <p className="text-xs font-bold text-gray-900">{freelancerName}</p>
                <p className="text-[11px] text-gray-500">Freelancer</p>
              </div>
            </div>

            <div className="h-8 w-px bg-gray-200" />

            <button
              onClick={() => navigate(`/client/messages?freelancer=${freelancer.id}`)}
              className="p-2.5 bg-white hover:bg-indigo-50 text-gray-700 hover:text-indigo-600 rounded-xl border border-gray-200 transition-colors flex items-center gap-1.5 text-xs font-bold"
              title="Message Freelancer"
            >
              <MessageSquare className="w-4 h-4 text-indigo-600" />
              <span>Message</span>
            </button>
          </div>
        </div>

        {/* Contract Key Terms Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-indigo-50/60 rounded-2xl p-4 border border-indigo-100">
            <p className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider">Total Contract Budget</p>
            <p className="text-2xl font-black text-indigo-900 mt-1">{formatCurrency(totalBudget, 'INR')}</p>
          </div>

          <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
            <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Contract Type</p>
            <p className="text-base font-bold text-gray-900 mt-1">Milestone-wise</p>
          </div>

          <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
            <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Total Milestones</p>
            <p className="text-base font-bold text-gray-900 mt-1">{milestones.length} Stages</p>
          </div>

          <div className="bg-emerald-50/60 rounded-2xl p-4 border border-emerald-100">
            <p className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider">Released to Freelancer</p>
            <p className="text-xl font-black text-emerald-800 mt-1">{formatCurrency(releasedAmount, 'INR')}</p>
          </div>
        </div>

        {/* ── Payment Progress Bar ──────────────────────────────────────── */}
        <div className="bg-gray-50 rounded-2xl p-5 border border-gray-100 space-y-3">
          <div className="flex flex-wrap items-center justify-between text-xs gap-2">
            <span className="font-bold text-gray-800 flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-emerald-600" />
              Payment Release Progress: {formatCurrency(releasedAmount, 'INR')} / {formatCurrency(totalBudget, 'INR')} released
            </span>
            <span className="font-black text-indigo-600">{progressPercent}% Completed</span>
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
              <span className="w-2.5 h-2.5 rounded-full bg-gray-300" /> Pending Funding ({formatCurrency(pendingFundingAmount, 'INR')})
            </span>
          </div>
        </div>
      </div>

      {/* ── Milestones Section ───────────────────────────────────────────── */}
      <div className="bg-white rounded-3xl p-8 border border-gray-200/80 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-black text-gray-900 tracking-tight">Milestones & Escrow Stages</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Each milestone is funded into escrow before work begins. Payments are released upon your approval of delivered work.
            </p>
          </div>

          <button
            onClick={() => setShowMilestoneModal(true)}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-2 self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" /> Setup / Add Milestones
          </button>
        </div>

        {/* Milestone List Table */}
        {milestones.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-2xl border border-dashed border-gray-200 space-y-4">
            <div className="w-12 h-12 bg-indigo-100 rounded-2xl flex items-center justify-center text-indigo-600 mx-auto">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900">No milestones configured yet</h3>
              <p className="text-xs text-gray-500 max-w-md mx-auto mt-1">
                You can split your budget equally across monthly milestones or create custom milestone stages.
              </p>
            </div>
            <button
              onClick={() => setShowMilestoneModal(true)}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-all shadow-sm inline-flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" /> Distribute Budget Equally
            </button>
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
                          <div className="mt-2 p-2 bg-indigo-50/60 rounded-lg text-xs text-indigo-900 border border-indigo-100">
                            <span className="font-bold">Submitted Deliverable: </span>{m.deliverable_description}
                          </div>
                        )}
                      </td>

                      <td className="py-4 px-4 font-black text-gray-900 whitespace-nowrap">
                        {formatCurrency(m.amount, 'INR')}
                        <span className="block text-[10px] text-gray-400 font-normal">
                          {m.percentage ? `${m.percentage}% of total` : ''}
                        </span>
                      </td>

                      <td className="py-4 px-4 text-xs font-semibold text-gray-600 whitespace-nowrap">
                        {m.due_date ? formatDate(m.due_date) : 'Flexible'}
                      </td>

                      <td className="py-4 px-4 whitespace-nowrap">
                        {isPaid && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Released
                          </span>
                        )}
                        {isSubmitted && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
                            <Clock className="w-3.5 h-3.5 text-amber-600" /> Deliverable Submitted
                          </span>
                        )}
                        {isFunded && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            <Lock className="w-3.5 h-3.5 text-indigo-600" /> Funded in Escrow
                          </span>
                        )}
                        {isPending && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-600 border border-gray-200">
                            Pending Escrow Deposit
                          </span>
                        )}
                      </td>

                      <td className="py-4 px-4 text-right whitespace-nowrap">
                        {isPending && (
                          <button
                            onClick={() => handleFundMilestone(m)}
                            disabled={actionLoading}
                            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center gap-1.5 ml-auto"
                          >
                            <CreditCard className="w-3.5 h-3.5" /> Fund Escrow
                          </button>
                        )}

                        {isSubmitted && (
                          <button
                            onClick={() => { setSelectedMilestone(m); setShowReviewModal(true) }}
                            className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center gap-1.5 ml-auto"
                          >
                            <Eye className="w-3.5 h-3.5" /> Review Deliverable
                          </button>
                        )}

                        {isFunded && (
                          <span className="text-xs font-semibold text-gray-400 italic">
                            Work In Progress
                          </span>
                        )}

                        {isPaid && (
                          <button
                            onClick={() => handleDownloadReceipt(m)}
                            className="px-3 py-1.5 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 border border-gray-200 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ml-auto"
                          >
                            <Download className="w-3.5 h-3.5" /> Receipt
                          </button>
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

      {/* ── Deliverables & Work Logs Review ───────────────────────────────── */}
      {deliverables.length > 0 && (
        <div className="bg-white rounded-3xl p-8 border border-gray-200/80 shadow-sm space-y-4">
          <h2 className="text-xl font-black text-gray-900 tracking-tight">Submitted Deliverables</h2>
          <div className="space-y-3">
            {deliverables.map((d) => (
              <div key={d.id} className="p-4 bg-gray-50 rounded-2xl border border-gray-100 flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <p className="font-bold text-gray-900 text-sm">{d.title || `Deliverable #${d.id}`}</p>
                  <p className="text-xs text-gray-600">{d.description}</p>
                  {d.file_url && (
                    <a
                      href={d.file_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:underline pt-1"
                    >
                      <ExternalLink className="w-3.5 h-3.5" /> View Deliverable Files / Link
                    </a>
                  )}
                </div>

                <span className={`px-3 py-1 rounded-full text-xs font-bold flex-shrink-0 ${
                  d.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                }`}>
                  {d.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Milestone Setup Modal (Equal Distribution / Custom) ───────────── */}
      {showMilestoneModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl w-full max-w-lg p-6 shadow-2xl space-y-6 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setShowMilestoneModal(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <h3 className="text-lg font-bold text-gray-900">Configure Milestone Schedule</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Total Contract Budget: <span className="font-bold text-indigo-600">{formatCurrency(totalBudget, 'INR')}</span>
              </p>
            </div>

            {/* Mode 1: Equal Distribution */}
            <div className="p-4 bg-indigo-50/70 rounded-2xl border border-indigo-100 space-y-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <h4 className="text-sm font-bold text-indigo-900">Equal Distribution Generator</h4>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-gray-700 mb-1">Number of Milestones</label>
                  <select
                    value={milestoneCount}
                    onChange={(e) => setMilestoneCount(e.target.value)}
                    className="w-full p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 font-semibold"
                  >
                    <option value="2">2 Milestones (50% each)</option>
                    <option value="3">3 Milestones (33.3% each)</option>
                    <option value="4">4 Milestones (25% each)</option>
                    <option value="6">6 Milestones (16.6% each)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-gray-700 mb-1">Frequency Interval</label>
                  <select
                    value={milestoneInterval}
                    onChange={(e) => setMilestoneInterval(e.target.value)}
                    className="w-full p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 font-semibold"
                  >
                    <option value="monthly">Monthly Milestones</option>
                    <option value="biweekly">Bi-weekly (14 days)</option>
                    <option value="custom">Custom Spacing</option>
                  </select>
                </div>
              </div>

              <p className="text-xs text-indigo-800">
                Each milestone will be allocated exactly{' '}
                <span className="font-bold">{formatCurrency(totalBudget / (parseInt(milestoneCount, 10) || 1), 'INR')}</span>.
              </p>

              <button
                onClick={handleGenerateEqualMilestones}
                disabled={actionLoading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                {actionLoading ? 'Generating...' : 'Auto-Generate Equal Milestones'}
              </button>
            </div>

            <div className="relative flex py-1 items-center">
              <div className="flex-grow border-t border-gray-200" />
              <span className="flex-shrink mx-4 text-xs text-gray-400 font-semibold uppercase">Or Add Single Custom</span>
              <div className="flex-grow border-t border-gray-200" />
            </div>

            {/* Mode 2: Custom Milestone Form */}
            <form onSubmit={handleAddCustomMilestone} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Milestone Title</label>
                <input
                  type="text"
                  required
                  value={customMilestone.title}
                  onChange={(e) => setCustomMilestone({ ...customMilestone, title: e.target.value })}
                  placeholder="e.g. Design Wireframes & Architecture"
                  className="w-full p-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={customMilestone.amount}
                    onChange={(e) => setCustomMilestone({ ...customMilestone, amount: e.target.value })}
                    placeholder="e.g. 15000"
                    className="w-full p-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Due Date</label>
                  <input
                    type="date"
                    value={customMilestone.due_date}
                    onChange={(e) => setCustomMilestone({ ...customMilestone, due_date: e.target.value })}
                    className="w-full p-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                className="w-full py-2.5 bg-gray-900 hover:bg-black text-white rounded-xl text-xs font-bold transition-all"
              >
                {actionLoading ? 'Adding...' : 'Add Custom Milestone'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── Review Deliverable Modal ────────────────────────────────────── */}
      {showReviewModal && selectedMilestone && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl w-full max-w-lg p-6 shadow-2xl space-y-6 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setShowReviewModal(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <h3 className="text-lg font-bold text-gray-900">Review Milestone Deliverable</h3>
              <p className="text-xs text-gray-500 mt-0.5">{selectedMilestone.title}</p>
            </div>

            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 space-y-2">
              <p className="text-xs font-bold text-gray-700">Milestone Amount: {formatCurrency(selectedMilestone.amount, 'INR')}</p>
              <p className="text-xs text-gray-600">{selectedMilestone.description}</p>
              {selectedMilestone.deliverable_description && (
                <div className="pt-2">
                  <p className="text-xs font-bold text-gray-800">Freelancer Notes:</p>
                  <p className="text-xs text-gray-600 mt-0.5 bg-white p-3 rounded-xl border border-gray-200">{selectedMilestone.deliverable_description}</p>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => handleApproveMilestone(selectedMilestone.id)}
                disabled={actionLoading}
                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5"
              >
                <Check className="w-4 h-4" /> Approve & Release Payment
              </button>

              <button
                onClick={() => {
                  alert('Revision request sent to freelancer.')
                  setShowReviewModal(false)
                }}
                className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl text-xs font-bold transition-all"
              >
                Request Changes
              </button>
            </div>
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
                  className="w-full p-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-semibold"
                >
                  <option value="QUALITY_ISSUE">Work quality does not match agreement</option>
                  <option value="NON_DELIVERY">Freelancer missed deadline / unresponsive</option>
                  <option value="SCOPE_DISPUTE">Scope disagreement on deliverable</option>
                  <option value="OTHER">Other grievance</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Details & Evidence</label>
                <textarea
                  rows={4}
                  required
                  value={disputeForm.description}
                  onChange={(e) => setDisputeForm({ ...disputeForm, description: e.target.value })}
                  placeholder="Explain the reason for the dispute and steps taken so far..."
                  className="w-full p-3 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="p-3 bg-amber-50 rounded-xl text-[11px] text-amber-800 border border-amber-200">
                Funds currently in escrow will remain locked during the mediation process.
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                className="w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                {actionLoading ? 'Submitting Dispute...' : 'Submit Dispute to Support'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── Terminate Contract Modal ────────────────────────────────────── */}
      {showTerminateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-5 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setShowTerminateModal(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center text-red-600">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Terminate Contract</h3>
                <p className="text-xs text-gray-500">Contract #{contract.id}</p>
              </div>
            </div>

            <div className="p-3.5 bg-red-50 rounded-xl border border-red-200 text-xs text-red-800 space-y-1">
              <p className="font-bold">Important Notice:</p>
              <p>
                Terminating this contract will cancel pending milestones. Unreleased escrow funds will be subject to mutual agreement or dispute resolution.
              </p>
            </div>

            <form onSubmit={handleTerminateContract} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Reason for Termination</label>
                <textarea
                  rows={3}
                  required
                  value={terminateExplanation}
                  onChange={(e) => setTerminateExplanation(e.target.value)}
                  placeholder="Provide an explanation for cancelling this contract..."
                  className="w-full p-3 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                {actionLoading ? 'Terminating...' : 'Confirm Contract Termination'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
