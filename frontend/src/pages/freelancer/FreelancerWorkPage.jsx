import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { aiWorklogAPI } from '../../api/worklogs'
import { paymentsAPI } from '../../api/payments'
import { contractsAPI } from '../../api/bids'
import {
  SparklesIcon,
  PaperAirplaneIcon,
  CheckCircleIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  DocumentTextIcon,
  ArrowLeftIcon,
  ShieldCheckIcon,
  BriefcaseIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  UserCircleIcon,
  LockClosedIcon,
  ChevronRightIcon,
  CheckIcon,
  TrashIcon,
  PlusIcon,
  PencilSquareIcon,
} from '@heroicons/react/24/outline'
import { useAuth } from '../../context/AuthContext'
import { getWebSocketUrl } from '../../utils/websocket'
import { WorkPageSkeleton } from '../../components/common/Skeleton'

// ─── Milestone status badge helper ───────────────────────────────────────────
const statusBadge = (status) => {
  switch (status) {
    case 'APPROVED':
    case 'PAID':
      return { label: 'Released', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
    case 'SUBMITTED':
      return { label: 'Under Review', cls: 'bg-amber-50 text-amber-700 border-amber-200' }
    case 'IN_PROGRESS':
    case 'FUNDED':
      return { label: 'In Progress', cls: 'bg-blue-50 text-blue-700 border-blue-200' }
    default:
      return { label: 'Awaiting Escrow', cls: 'bg-gray-100 text-gray-600 border-gray-200' }
  }
}

const isApproved = (m) => m?.status === 'APPROVED' || m?.status === 'PAID'
const isFunded   = (m) => m?.status === 'IN_PROGRESS' || m?.status === 'FUNDED'
const isSubmitted= (m) => m?.status === 'SUBMITTED'
const isPending  = (m) => !isApproved(m) && !isFunded(m) && !isSubmitted(m)

const FreelancerWorkPage = () => {
  const { contractId } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { user } = useAuth()

  // Selected milestone from URL query: ?milestone=X
  const urlMilestoneId = searchParams.get('milestone')

  // Automatically redirect client users to client portal
  useEffect(() => {
    if (user?.role === 'CLIENT' && contractId) {
      navigate(`/client/contracts/${contractId}`, { replace: true })
    }
  }, [user, contractId, navigate])

  // ── State ──────────────────────────────────────────────────────────────────
  const [loading, setLoading]                 = useState(true)
  const [sending, setSending]                 = useState(false)
  const [approving, setApproving]             = useState(false)
  const [contextData, setContextData]         = useState(null)
  const [milestonesList, setMilestonesList]   = useState([])

  // Active milestone driven by right sidebar selection
  const [activeMilestoneId, setActiveMilestoneId] = useState(urlMilestoneId ? parseInt(urlMilestoneId, 10) : null)

  // Per-milestone isolated workspace state:
  // { [milestoneId]: { messages: [], conversationId, activeDraft, pdfUrl } }
  const [workspaceMap, setWorkspaceMap]       = useState({})

  const [inputValue, setInputValue]           = useState('')
  const [errorMsg, setErrorMsg]               = useState('')

  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)

  // ── Load Context & Milestones ──────────────────────────────────────────────
  useEffect(() => {
    if (contractId) loadContextBundle()
  }, [contractId])

  // Auto-scroll inside the messages container only
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, [workspaceMap, activeMilestoneId, sending])

  // Sync active milestone to URL search params
  useEffect(() => {
    if (activeMilestoneId) {
      setSearchParams({ milestone: activeMilestoneId }, { replace: true })
    }
  }, [activeMilestoneId])

  const loadContextBundle = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [res, milestonesRes, contractRes] = await Promise.allSettled([
        aiWorklogAPI.getContext(contractId),
        paymentsAPI.getMilestones(contractId),
        contractsAPI.getContractDetail(contractId),
      ])

      let data = {}
      if (res.status === 'fulfilled' && res.value?.data) {
        data = res.value.data
      }

      // Populate contract details if needed
      if (!data.contract && contractRes.status === 'fulfilled' && contractRes.value?.data) {
        const c = contractRes.value.data
        data.contract = {
          id: c.id,
          title: c.project?.title || c.title || `Contract #${contractId}`,
          description: c.project?.description || c.description || '',
          client_name: c.client?.first_name
            ? `${c.client.first_name} ${c.client.last_name || ''}`.trim()
            : c.client?.email || 'Client',
          rate: c.agreed_amount || c.total_amount || 0,
          status: c.status || 'ACTIVE',
        }
      }
      if (!data.contract) {
        data.contract = {
          id: contractId,
          title: `Contract #${contractId}`,
          description: '',
          client_name: 'Client',
          rate: 0,
          status: 'ACTIVE',
        }
      }

      setContextData(data)

      let milestones = []
      if (milestonesRes.status === 'fulfilled' && Array.isArray(milestonesRes.value.data)) {
        milestones = milestonesRes.value.data
      } else if (data.milestones) {
        milestones = data.milestones
      }
      setMilestonesList(milestones)

      // Target milestone selection
      let targetId = urlMilestoneId ? parseInt(urlMilestoneId, 10) : null
      if (!targetId || !milestones.some(m => m.id === targetId)) {
        const firstActive = milestones.find(m => isFunded(m) || isSubmitted(m)) || milestones[0]
        targetId = firstActive?.id || null
      }
      setActiveMilestoneId(targetId)

      // Seed workspaces for each milestone
      const newMap = {}
      milestones.forEach((m) => {
        const pdfLink = m.deliverable_description?.includes('| Link:')
          ? m.deliverable_description.split('| Link:')[1]?.trim()
          : null

        const isTarget = m.id === targetId
        const activeDraft = (isTarget && data.active_draft) ? data.active_draft : null
        const pdfUrl = pdfLink || activeDraft?.pdf_url || null

        const defaultMessages = [
          {
            role: 'assistant',
            content: `Hello! I'm your AI Worklog Assistant for **${m.title}**. Tell me what you worked on today, or click a quick prompt below to draft your milestone report.`,
            timestamp: new Date().toISOString(),
          }
        ]

        newMap[m.id] = {
          messages: (isTarget && data.conversation?.messages?.length > 0)
            ? data.conversation.messages
            : defaultMessages,
          conversationId: (isTarget && data.conversation?.id) ? data.conversation.id : null,
          activeDraft: activeDraft,
          pdfUrl: pdfUrl,
        }
      })

      setWorkspaceMap(prev => ({
        ...newMap,
        ...prev,
      }))
    } catch (err) {
      console.error('Error loading AI context bundle:', err)
      setErrorMsg('Failed to load contract workspace. Please make sure you have access.')
    } finally {
      setLoading(false)
    }
  }

  // ── Active Milestone Workspace Helpers ─────────────────────────────────────
  const activeMilestone = milestonesList.find(m => m.id === activeMilestoneId) || null

  const ws = activeMilestoneId ? (workspaceMap[activeMilestoneId] || {}) : {}
  const messages         = ws.messages || []
  const conversationId   = ws.conversationId || null
  const activeDraft      = ws.activeDraft || null

  const pdfUrlFromDesc = activeMilestone?.deliverable_description?.includes('| Link:')
    ? activeMilestone.deliverable_description.split('| Link:')[1]?.trim()
    : null
  const pdfUrl = ws.pdfUrl || pdfUrlFromDesc || null

  const updateWS = (patch) => {
    if (!activeMilestoneId) return
    setWorkspaceMap(prev => ({
      ...prev,
      [activeMilestoneId]: { ...prev[activeMilestoneId], ...patch }
    }))
  }

  // One-time AI worklog lock rule per milestone
  const hasApprovedReport = Boolean(
    pdfUrl ||
    (activeDraft?.pdf_url) ||
    (activeDraft?.status === 'APPROVED') ||
    isSubmitted(activeMilestone) ||
    isApproved(activeMilestone)
  )

  // ── Switch Milestone Selection ─────────────────────────────────────────────
  const handleSelectMilestone = (m) => {
    setActiveMilestoneId(m.id)
    setInputValue('')
    if (!workspaceMap[m.id]) {
      const pdfLink = m.deliverable_description?.includes('| Link:')
        ? m.deliverable_description.split('| Link:')[1]?.trim()
        : null
      setWorkspaceMap(prev => ({
        ...prev,
        [m.id]: {
          messages: [{
            role: 'assistant',
            content: `Hello! I'm your AI Worklog Assistant for **${m.title}**. Tell me what you've worked on, or click a quick prompt below to draft your report.`,
            timestamp: new Date().toISOString(),
          }],
          conversationId: null,
          activeDraft: null,
          pdfUrl: pdfLink,
        }
      }))
    }
  }

  // ── WebSocket for Live Updates ─────────────────────────────────────────────
  useEffect(() => {
    if (!contractId) return
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || ''
    const wsUrl = getWebSocketUrl(`/ws/contract/${contractId}/`, token ? { token } : {})
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'ai_draft_pdf_ready') {
          const { pdf_url } = data.payload || {}
          if (pdf_url && activeMilestoneId) {
            setWorkspaceMap(prev => ({
              ...prev,
              [activeMilestoneId]: {
                ...prev[activeMilestoneId],
                pdfUrl: pdf_url,
                activeDraft: { ...(prev[activeMilestoneId]?.activeDraft || {}), status: 'APPROVED', pdf_url },
              }
            }))
            setApproving(false)
            loadContextBundle()
          }
        } else if (data.type === 'ai_draft_pdf_error') {
          setApproving(false)
          alert('Failed to compile PDF: ' + (data.payload?.error || 'Unknown error'))
        } else if (['milestone_submitted', 'milestone_approved', 'milestone_funded', 'milestone_rejected'].includes(data.type)) {
          loadContextBundle()
        }
      } catch {}
    }
    ws.onerror = () => ws.close()
    return () => ws.close()
  }, [contractId, activeMilestoneId])

  // ── AI Chat Message Handler ────────────────────────────────────────────────
  const handleSendMessage = async (textToSend = null) => {
    const text = (textToSend || inputValue).trim()
    if (!text || sending || !activeMilestoneId) return

    setWorkspaceMap(prev => ({
      ...prev,
      [activeMilestoneId]: {
        ...prev[activeMilestoneId],
        messages: [
          ...(prev[activeMilestoneId]?.messages || []),
          { role: 'user', content: text, timestamp: new Date().toISOString() }
        ]
      }
    }))
    if (!textToSend) setInputValue('')
    setSending(true)

    try {
      const res = await aiWorklogAPI.sendChatMessage(contractId, text, conversationId, activeMilestoneId)
      const data = res.data

      setWorkspaceMap(prev => ({
        ...prev,
        [activeMilestoneId]: {
          ...prev[activeMilestoneId],
          conversationId: data.conversation_id || prev[activeMilestoneId]?.conversationId,
          activeDraft: data.is_draft_ready && data.draft
            ? { ...data.draft, id: data.draft_id }
            : prev[activeMilestoneId]?.activeDraft,
          messages: [
            ...(prev[activeMilestoneId]?.messages || []),
            {
              role: 'assistant',
              content: data.reply,
              timestamp: new Date().toISOString(),
              has_draft: data.is_draft_ready,
              draft_data: data.draft,
              draft_id: data.draft_id,
            }
          ]
        }
      }))
    } catch (err) {
      console.error(err)
      setWorkspaceMap(prev => ({
        ...prev,
        [activeMilestoneId]: {
          ...prev[activeMilestoneId],
          messages: [
            ...(prev[activeMilestoneId]?.messages || []),
            { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', is_error: true, timestamp: new Date().toISOString() }
          ]
        }
      }))
    } finally {
      setSending(false)
    }
  }

  // ── Inline Editable Draft Handlers ─────────────────────────────────────────
  const handleDraftUpdate = (msgIdx, patch) => {
    if (!activeMilestoneId) return
    setWorkspaceMap(prev => {
      const currMsgs = [...(prev[activeMilestoneId]?.messages || [])]
      if (currMsgs[msgIdx]) {
        const currDraft = currMsgs[msgIdx].draft_data || {}
        const updatedDraft = { ...currDraft, ...patch }
        currMsgs[msgIdx] = {
          ...currMsgs[msgIdx],
          draft_data: updatedDraft,
        }
      }
      return {
        ...prev,
        [activeMilestoneId]: {
          ...prev[activeMilestoneId],
          messages: currMsgs,
          activeDraft: currMsgs[msgIdx]?.draft_data || prev[activeMilestoneId]?.activeDraft,
        }
      }
    })
  }

  const handleDeliverableItemChange = (msgIdx, itemIdx, field, value) => {
    const msg = messages[msgIdx]
    if (!msg?.draft_data) return
    const deliverables = [...(msg.draft_data.section_deliverables || [])]
    if (deliverables[itemIdx]) {
      deliverables[itemIdx] = { ...deliverables[itemIdx], [field]: value }
      handleDraftUpdate(msgIdx, { section_deliverables: deliverables })
    }
  }

  const handleAddDeliverableItem = (msgIdx) => {
    const msg = messages[msgIdx]
    if (!msg?.draft_data) return
    const deliverables = [...(msg.draft_data.section_deliverables || [])]
    deliverables.push({
      title: 'New Deliverable Item',
      description: 'Describe deliverable details and verification...',
      status: 'COMPLETED',
    })
    handleDraftUpdate(msgIdx, { section_deliverables: deliverables })
  }

  const handleRemoveDeliverableItem = (msgIdx, itemIdx) => {
    const msg = messages[msgIdx]
    if (!msg?.draft_data) return
    const deliverables = (msg.draft_data.section_deliverables || []).filter((_, i) => i !== itemIdx)
    handleDraftUpdate(msgIdx, { section_deliverables: deliverables })
  }

  // ── Approve AI Draft & Generate PDF with Freelancer Edits ──────────────────
  const handleApproveDraft = async (draftIdToApprove = null, customDraftData = null) => {
    const targetDraftId = draftIdToApprove || activeDraft?.id
    const draftPayload = customDraftData || activeDraft || null
    setApproving(true)
    try {
      const res = await aiWorklogAPI.approveDraft(contractId, targetDraftId, activeMilestoneId, draftPayload)
      const data = res.data || {}
      const compiledPdf = data.pdf_url

      if (compiledPdf && activeMilestoneId) {
        updateWS({
          pdfUrl: compiledPdf,
          activeDraft: { ...(activeDraft || {}), status: 'APPROVED', pdf_url: compiledPdf }
        })
        setWorkspaceMap(prev => ({
          ...prev,
          [activeMilestoneId]: {
            ...prev[activeMilestoneId],
            pdfUrl: compiledPdf,
            activeDraft: { ...(prev[activeMilestoneId]?.activeDraft || {}), status: 'APPROVED', pdf_url: compiledPdf },
            messages: [
              ...(prev[activeMilestoneId]?.messages || []),
              {
                role: 'assistant',
                content: `Your official milestone deliverable and progress report have been submitted and are now **under review by the client**.`,
                pdf_url: compiledPdf,
                timestamp: new Date().toISOString(),
              }
            ]
          }
        }))
        setApproving(false)
        await loadContextBundle()
        return
      }

      // Fallback polling if pdf_url wasn't in direct response
      let attempts = 0
      const pollInterval = setInterval(async () => {
        attempts += 1
        try {
          const fresh = await aiWorklogAPI.getContext(contractId)
          const active = fresh?.data?.active_draft
          const prev_reports = fresh?.data?.previous_reports || []
          if (active?.pdf_url || prev_reports.length > 0 || attempts >= 5) {
            clearInterval(pollInterval)
            setApproving(false)
            if (active?.pdf_url) {
              updateWS({ pdfUrl: active.pdf_url })
            }
            loadContextBundle()
          }
        } catch {
          if (attempts >= 5) {
            clearInterval(pollInterval)
            setApproving(false)
          }
        }
      }, 1500)
    } catch (err) {
      console.error(err)
      alert('Failed to approve report: ' + (err.response?.data?.error || err.message))
      setApproving(false)
    }
  }

  // ── Loading & Error States ─────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-6">
        <WorkPageSkeleton />
      </div>
    )
  }

  if (errorMsg) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white border border-gray-200 rounded-3xl p-8 text-center shadow-lg">
          <ExclamationCircleIcon className="w-12 h-12 text-rose-500 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-gray-900">Access Denied or Not Found</h2>
          <p className="text-gray-500 text-sm mt-2">{errorMsg}</p>
          <button
            onClick={() => navigate(`/freelancer/contracts/${contractId}`)}
            className="mt-6 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-all shadow-md shadow-blue-600/20 cursor-pointer"
          >
            Back to Contract
          </button>
        </div>
      </div>
    )
  }

  const contract = contextData?.contract || {}
  const previous_reports = contextData?.previous_reports || []

  return (
    <div className="flex-1 min-h-0 flex flex-col w-full h-full bg-white text-gray-900 overflow-hidden">

      {/* ── Top Header Bar (Fixed / Stated in place) ────────────────────── */}
      <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 sm:px-6 shrink-0 z-20 shadow-2xs">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/freelancer/contracts/${contractId}`)}
            className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors flex items-center gap-1.5 text-xs font-bold cursor-pointer"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Back to Contract</span>
          </button>
          <div className="h-5 w-px bg-gray-200" />
          <div>
            <h1 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <span className="line-clamp-1">{contract?.title || `Contract #${contractId}`}</span>
              <span className="hidden md:inline text-xs px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 font-bold border border-blue-200">
                AI Worklog Workspace
              </span>
            </h1>
          </div>
        </div>

        {activeMilestone && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 font-medium hidden sm:inline">Active Milestone:</span>
            <span className="text-xs font-bold text-gray-800 hidden sm:inline">{activeMilestone.title}</span>
            <span className={`px-2.5 py-1 text-xs font-bold rounded-lg border ${statusBadge(activeMilestone.status).cls}`}>
              {statusBadge(activeMilestone.status).label}
            </span>
          </div>
        )}
      </header>

      {/* ── Main Fixed Body: Center Chat Workspace + Right White Sidebar ── */}
      <div className="flex-1 min-h-0 flex overflow-hidden">

        {/* ══════════════════════════════════════════════════════════════
            CENTER / LEFT: Active Milestone Workspace (Fixed, Stated in Place)
        ══════════════════════════════════════════════════════════════ */}
        <div className="flex-1 min-h-0 flex flex-col min-w-0 bg-white overflow-hidden">
          {!activeMilestone ? (
            <div className="flex-1 flex items-center justify-center text-center p-10 bg-gray-50">
              <div className="max-w-sm space-y-3">
                <BriefcaseIcon className="w-12 h-12 text-gray-400 mx-auto" />
                <h3 className="text-base font-bold text-gray-800">No Milestones Found</h3>
                <p className="text-xs text-gray-500">This contract does not have active milestones configured yet.</p>
              </div>
            </div>
          ) : isApproved(activeMilestone) ? (
            /* ── COMPLETED / RELEASED MILESTONE ── */
            <div className="flex-1 min-h-0 flex flex-col items-center justify-center bg-gray-50/60 p-6 sm:p-10 text-center">
              <div className="max-w-md w-full bg-white rounded-3xl border border-gray-200 p-8 shadow-md space-y-5">
                <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 shadow-sm border border-emerald-100">
                  <CheckCircleIcon className="w-9 h-9" />
                </div>
                <div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Milestone Completed & Released
                  </span>
                  <h2 className="text-xl font-bold text-gray-900 mt-3">{activeMilestone.title}</h2>
                  <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                    {activeMilestone.description || 'All deliverables for this milestone were verified and payment was released.'}
                  </p>
                </div>

                <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-2xl flex items-center justify-between">
                  <div className="text-left">
                    <p className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">Payment Released</p>
                    <p className="text-xs text-emerald-600">Deposited to your balance</p>
                  </div>
                  <p className="text-2xl font-black text-emerald-700">
                    ${parseFloat(activeMilestone.amount || 0).toLocaleString()}
                  </p>
                </div>

                {/* Direct PDF Download Button */}
                {pdfUrl ? (
                  <a
                    href={pdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full flex items-center justify-center gap-2 py-3.5 px-5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold shadow-md shadow-blue-600/20 transition-all cursor-pointer active:scale-98"
                  >
                    <ArrowDownTrayIcon className="w-5 h-5" />
                    Download Approved Worklog PDF
                  </a>
                ) : (
                  <div className="p-3.5 bg-gray-50 rounded-xl border border-gray-200 text-xs text-gray-500">
                    Milestone approved and payment released by client.
                  </div>
                )}

                <div className="pt-2 border-t border-gray-100 text-xs text-gray-400">
                  Select the next funded milestone from the right sidebar to continue logging work.
                </div>
              </div>
            </div>
          ) : isPending(activeMilestone) ? (
            /* ── PENDING MILESTONE: Awaiting Escrow Deposit ── */
            <div className="flex-1 min-h-0 flex flex-col items-center justify-center bg-gray-50/60 p-6 sm:p-10 text-center">
              <div className="max-w-md w-full bg-white rounded-3xl border border-gray-200 p-8 shadow-md space-y-4">
                <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto text-gray-400">
                  <LockClosedIcon className="w-7 h-7" />
                </div>
                <div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-600 border border-gray-200">
                    Awaiting Client Escrow Deposit
                  </span>
                  <h2 className="text-xl font-bold text-gray-900 mt-3">{activeMilestone.title}</h2>
                  <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                    This milestone has not been funded into escrow yet. Once your client deposits the funds, you can immediately begin submitting work logs.
                  </p>
                </div>
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-2xl flex justify-between items-center">
                  <span className="text-xs font-bold text-gray-500">Milestone Amount:</span>
                  <span className="text-xl font-black text-gray-900">${parseFloat(activeMilestone.amount || 0).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ) : (
            /* ── ACTIVE / FUNDED / SUBMITTED MILESTONE: Pure AI Assistant Workspace ── */
            <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
              
              {/* Messages Stream (Independently Scrollable Container) */}
              <div
                ref={messagesContainerRef}
                className="flex-1 min-h-0 overflow-y-auto p-6 space-y-6 scroll-smooth bg-gray-50/30"
              >
                {messages.map((msg, i) => {
                  const isUser = msg.role === 'user'
                  return (
                    <div key={i} className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
                      {!isUser && (
                        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                          <SparklesIcon className="w-4 h-4 text-blue-100" />
                        </div>
                      )}

                      <div className={`max-w-[90%] sm:max-w-[80%] space-y-3 ${isUser ? 'items-end' : 'items-start'}`}>
                        <div
                          className={`rounded-2xl p-4 text-sm leading-relaxed ${
                            isUser
                              ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-600/20'
                              : 'bg-white border border-gray-200 text-gray-900 rounded-bl-none shadow-2xs'
                          }`}
                        >
                          <div className="whitespace-pre-wrap">{msg.content}</div>

                          {/* Download PDF button if attached to this assistant message */}
                          {msg.pdf_url && (
                            <div className="mt-3.5 pt-3 border-t border-gray-100">
                              <a
                                href={msg.pdf_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all cursor-pointer active:scale-98"
                              >
                                <ArrowDownTrayIcon className="w-4 h-4" />
                                Download Official PDF Report
                              </a>
                            </div>
                          )}
                        </div>

                        {/* ── Interactive Inline Editable Draft Card ── */}
                        {msg.has_draft && msg.draft_data && (
                          <div className="rounded-2xl bg-white border border-blue-200 p-5 shadow-lg space-y-4">
                            {/* Card Header & Controls */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-gray-100 gap-2">
                              <div className="flex items-center gap-2 flex-1">
                                <DocumentTextIcon className="w-5 h-5 text-blue-600 shrink-0" />
                                {!hasApprovedReport ? (
                                  <input
                                    type="text"
                                    value={msg.draft_data.title || ''}
                                    onChange={(e) => handleDraftUpdate(i, { title: e.target.value })}
                                    className="font-bold text-gray-900 text-sm w-full bg-gray-50 hover:bg-white focus:bg-white border border-transparent hover:border-gray-200 focus:border-blue-500 rounded-lg px-2 py-1 transition-colors"
                                    placeholder="Report Title..."
                                  />
                                ) : (
                                  <h4 className="text-sm font-bold text-gray-900">{msg.draft_data.title}</h4>
                                )}
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                {!hasApprovedReport ? (
                                  <div className="flex items-center gap-1.5 bg-blue-50 border border-blue-200 rounded-lg px-2.5 py-1">
                                    <ClockIcon className="w-3.5 h-3.5 text-blue-600" />
                                    <input
                                      type="number"
                                      step="0.5"
                                      min="0"
                                      value={msg.draft_data.hours_worked ?? 8}
                                      onChange={(e) => handleDraftUpdate(i, { hours_worked: parseFloat(e.target.value) || 0 })}
                                      className="w-12 bg-transparent text-xs font-black text-blue-700 text-center focus:outline-none"
                                    />
                                    <span className="text-[11px] font-bold text-blue-600">Hours</span>
                                  </div>
                                ) : (
                                  <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-xs font-bold">
                                    {msg.draft_data.hours_worked || 0} Hours Logged
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Informational Editing Badge */}
                            {!hasApprovedReport && (
                              <div className="flex items-center justify-between text-[11px] text-blue-700 bg-blue-50/70 border border-blue-200 rounded-xl px-3 py-1.5">
                                <span className="font-semibold flex items-center gap-1.5">
                                  <PencilSquareIcon className="w-3.5 h-3.5 text-blue-600" />
                                  Editable Draft — You can edit, add, or remove text before generating PDF
                                </span>
                              </div>
                            )}

                            {/* Section 1: Executive Summary */}
                            <div className="space-y-1.5">
                              <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                1. Executive Summary
                              </p>
                              {!hasApprovedReport ? (
                                <textarea
                                  rows={3}
                                  value={msg.draft_data.section_summary || ''}
                                  onChange={(e) => handleDraftUpdate(i, { section_summary: e.target.value })}
                                  placeholder="Summarize the core milestone work completed..."
                                  className="w-full text-xs text-gray-800 bg-gray-50 hover:bg-white focus:bg-white p-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 leading-relaxed transition-colors shadow-2xs"
                                />
                              ) : (
                                <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200 leading-relaxed">
                                  {msg.draft_data.section_summary}
                                </p>
                              )}
                            </div>

                            {/* Section 2: Deliverables Completed */}
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                  2. Deliverables & Tasks Completed
                                </p>
                                {!hasApprovedReport && (
                                  <button
                                    type="button"
                                    onClick={() => handleAddDeliverableItem(i)}
                                    className="inline-flex items-center gap-1 text-[11px] font-bold text-blue-600 hover:text-blue-700 hover:underline cursor-pointer"
                                  >
                                    <PlusIcon className="w-3.5 h-3.5" /> Add Item
                                  </button>
                                )}
                              </div>

                              <div className="space-y-2">
                                {msg.draft_data.section_deliverables?.map((item, idx) => (
                                  <div
                                    key={idx}
                                    className="p-3 rounded-xl bg-gray-50 border border-gray-200 text-xs space-y-2"
                                  >
                                    <div className="flex items-center justify-between gap-2">
                                      {!hasApprovedReport ? (
                                        <input
                                          type="text"
                                          value={item.title || ''}
                                          onChange={(e) => handleDeliverableItemChange(i, idx, 'title', e.target.value)}
                                          placeholder="Deliverable Title..."
                                          className="font-bold text-gray-900 bg-white border border-gray-200 rounded-lg px-2.5 py-1 text-xs flex-1 focus:border-blue-500 focus:outline-none"
                                        />
                                      ) : (
                                        <span className="font-semibold text-gray-900">{item.title}</span>
                                      )}

                                      {!hasApprovedReport ? (
                                        <div className="flex items-center gap-1.5 shrink-0">
                                          <select
                                            value={item.status || 'COMPLETED'}
                                            onChange={(e) => handleDeliverableItemChange(i, idx, 'status', e.target.value)}
                                            className="text-[10px] font-bold px-2 py-1 rounded bg-white text-blue-700 border border-gray-200 focus:outline-none"
                                          >
                                            <option value="COMPLETED">COMPLETED</option>
                                            <option value="IN_PROGRESS">IN PROGRESS</option>
                                            <option value="VERIFIED">VERIFIED</option>
                                          </select>
                                          <button
                                            type="button"
                                            onClick={() => handleRemoveDeliverableItem(i, idx)}
                                            title="Delete Item"
                                            className="p-1 text-gray-400 hover:text-rose-600 transition-colors cursor-pointer"
                                          >
                                            <TrashIcon className="w-3.5 h-3.5" />
                                          </button>
                                        </div>
                                      ) : (
                                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 shrink-0">
                                          {item.status || 'COMPLETED'}
                                        </span>
                                      )}
                                    </div>

                                    {!hasApprovedReport ? (
                                      <textarea
                                        rows={2}
                                        value={item.description || ''}
                                        onChange={(e) => handleDeliverableItemChange(i, idx, 'description', e.target.value)}
                                        placeholder="Deliverable details / verification proof notes..."
                                        className="w-full text-[11px] text-gray-700 bg-white p-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:outline-none"
                                      />
                                    ) : (
                                      item.description && (
                                        <p className="text-[11px] text-gray-600 pl-1">{item.description}</p>
                                      )
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Section 3: Next Steps */}
                            <div className="space-y-1.5">
                              <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                3. Next Steps & Priorities
                              </p>
                              {!hasApprovedReport ? (
                                <textarea
                                  rows={2}
                                  value={msg.draft_data.section_next_steps || ''}
                                  onChange={(e) => handleDraftUpdate(i, { section_next_steps: e.target.value })}
                                  placeholder="Next milestone sprint goals and client verification..."
                                  className="w-full text-xs text-gray-800 bg-gray-50 hover:bg-white focus:bg-white p-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 leading-relaxed transition-colors shadow-2xs"
                                />
                              ) : (
                                <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200 leading-relaxed">
                                  {msg.draft_data.section_next_steps}
                                </p>
                              )}
                            </div>

                            {/* Approve / Action Button */}
                            <div className="pt-2">
                              {hasApprovedReport ? (
                                <div className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold shadow-2xs">
                                  <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                                  Deliverable Submitted — Under Client Review
                                </div>
                              ) : (
                                <button
                                  onClick={() => handleApproveDraft(msg.draft_id, msg.draft_data)}
                                  disabled={approving}
                                  className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all disabled:opacity-50 active:scale-98 cursor-pointer"
                                >
                                  {approving ? (
                                    <>
                                      <ArrowPathIcon className="w-4 h-4 animate-spin" />
                                      Compiling PDF & Submitting to Client...
                                    </>
                                  ) : (
                                    <>
                                      <CheckCircleIcon className="w-4 h-4" />
                                      Approve & Submit Official PDF to Client
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}

                {sending && (
                  <div className="flex gap-3 items-center">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shadow-sm">
                      <SparklesIcon className="w-4 h-4 text-white animate-spin" />
                    </div>
                    <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-none px-4 py-3 text-xs text-gray-600 flex items-center gap-2 shadow-2xs">
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" />
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:0.2s]" />
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:0.4s]" />
                      <span className="ml-1 font-medium">Synthesizing worklog progress...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Action Chips (Fixed in place at bottom) */}
              <div className="px-6 py-2.5 bg-gray-50 border-t border-gray-200 flex items-center gap-2 overflow-x-auto scrollbar-none shrink-0">
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider shrink-0">Quick Prompts:</span>
                {['draft my progress report', 'what is my timeline of my progress report'].map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(prompt)}
                    disabled={sending}
                    className="px-3.5 py-1.5 rounded-full bg-white hover:bg-blue-50 text-gray-700 hover:text-blue-600 text-xs font-semibold whitespace-nowrap transition-colors border border-gray-200 shadow-2xs shrink-0 cursor-pointer disabled:opacity-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              {/* Chat Input Bar (Fixed in place at bottom) */}
              <div className="p-4 bg-white border-t border-gray-200 shrink-0">
                <form
                  onSubmit={(e) => {
                    e.preventDefault()
                    handleSendMessage()
                  }}
                  className="flex items-center gap-3"
                >
                  <input
                    type="text"
                    placeholder={
                      hasApprovedReport
                        ? 'Milestone report submitted. Under review by client...'
                        : `Describe what you worked on for ${activeMilestone?.title || 'this milestone'}...`
                    }
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    disabled={sending}
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={!inputValue.trim() || sending}
                    className="p-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl shadow-md shadow-blue-600/20 transition-all shrink-0 active:scale-95 cursor-pointer"
                  >
                    <PaperAirplaneIcon className="w-5 h-5" />
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>

        {/* ══════════════════════════════════════════════════════════════
            RIGHT SIDEBAR: White & Simple Milestone History Section
        ══════════════════════════════════════════════════════════════ */}
        <aside className="w-72 lg:w-80 bg-white text-gray-900 flex flex-col shrink-0 overflow-hidden border-l border-gray-200 shadow-xs">
          {/* Header */}
          <div className="p-4 border-b border-gray-100 bg-gray-50/60 flex items-center justify-between shrink-0">
            <div>
              <p className="text-[10px] uppercase tracking-widest font-extrabold text-gray-400">Milestone History</p>
              <p className="text-xs text-gray-900 font-bold line-clamp-1 mt-0.5">{contract?.title}</p>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-md bg-white text-gray-700 font-bold border border-gray-200 shadow-2xs">
              {milestonesList.filter(m => isApproved(m)).length}/{milestonesList.length}
            </span>
          </div>

          {/* Milestone List (Clean White Cards) */}
          <div className="flex-1 min-h-0 overflow-y-auto py-3 space-y-2 px-3">
            {milestonesList.length === 0 ? (
              <p className="text-xs text-gray-400 p-4 text-center italic">No milestones configured for this contract.</p>
            ) : (
              milestonesList.map((m, idx) => {
                const isActive = m.id === activeMilestoneId
                const isDone   = isApproved(m)
                const isLocked = isPending(m)
                const badge    = statusBadge(m.status)

                // PDF link if available
                const pdfLinkFromDesc = m.deliverable_description?.includes('| Link:')
                  ? m.deliverable_description.split('| Link:')[1]?.trim()
                  : null
                const milestoneWS = workspaceMap[m.id] || {}
                const milestonePdf = milestoneWS.pdfUrl || pdfLinkFromDesc || null

                return (
                  <div
                    key={m.id}
                    onClick={() => !isLocked && handleSelectMilestone(m)}
                    className={`group relative rounded-2xl p-3.5 transition-all duration-200 border ${
                      isActive
                        ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-500/15 shadow-xs'
                        : isLocked
                        ? 'bg-gray-50/80 border-gray-200 opacity-60 cursor-not-allowed'
                        : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300 cursor-pointer shadow-2xs'
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      {/* Step Number Badge */}
                      <div className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 text-[11px] font-black mt-0.5 ${
                        isDone
                          ? 'bg-emerald-600 text-white shadow-2xs'
                          : isSubmitted(m)
                          ? 'bg-amber-500 text-white'
                          : isFunded(m)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}>
                        {isDone ? <CheckIcon className="w-3.5 h-3.5 stroke-[3]" /> : idx + 1}
                      </div>

                      {/* Milestone Title & Details */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-1">
                          <p className={`text-xs font-bold truncate ${
                            isActive ? 'text-blue-900 font-extrabold' : 'text-gray-900 group-hover:text-blue-600'
                          }`}>
                            {m.title}
                          </p>
                          {isLocked && <LockClosedIcon className="w-3.5 h-3.5 text-gray-400 shrink-0" />}
                        </div>

                        <div className="flex items-center justify-between gap-2 mt-1.5">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${badge.cls}`}>
                            {badge.label}
                          </span>
                          <span className="text-[11px] font-black text-gray-900">
                            ${parseFloat(m.amount || 0).toLocaleString()}
                          </span>
                        </div>

                        {/* Direct PDF download on sidebar card for approved milestones */}
                        {isDone && milestonePdf && (
                          <div className="mt-2.5 pt-2 border-t border-gray-100 flex items-center justify-between">
                            <span className="text-[10px] text-emerald-700 font-bold">Report Verified</span>
                            <a
                              href={milestonePdf}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded-lg border border-emerald-200 transition-all shadow-2xs cursor-pointer"
                            >
                              <ArrowDownTrayIcon className="w-3 h-3" /> PDF
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>

          {/* ── Generated PDF Download Section (Lower Portion of Sidebar) ── */}
          <div className="p-3.5 border-t border-gray-200 bg-gray-50/70 shrink-0 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
                <DocumentTextIcon className="w-3.5 h-3.5 text-blue-600" />
                Worklog PDF Downloads
              </span>
              {pdfUrl && (
                <span className="text-[10px] font-bold px-1.5 py-0.2 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
                  Active Ready
                </span>
              )}
            </div>

            {/* Active Milestone PDF if available */}
            {pdfUrl ? (
              <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-2xs space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-gray-900 truncate">
                      {activeMilestone?.title || 'Milestone Report'}
                    </p>
                    <p className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1 mt-0.5">
                      <CheckCircleIcon className="w-3 h-3" /> Official PDF Generated
                    </p>
                  </div>
                </div>
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs transition-all active:scale-98 cursor-pointer"
                >
                  <ArrowDownTrayIcon className="w-3.5 h-3.5" />
                  Download Worklog PDF
                </a>
              </div>
            ) : previous_reports?.length > 0 ? (
              <div className="space-y-1.5 max-h-40 overflow-y-auto pr-0.5">
                {previous_reports.map((rpt, idx) => (
                  <div
                    key={rpt.id || idx}
                    className="p-2.5 rounded-xl bg-white border border-gray-200 shadow-2xs flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-gray-900 truncate">{rpt.title}</p>
                      <p className="text-[10px] text-gray-500">
                        {rpt.hours_worked}h • {new Date(rpt.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    {rpt.pdf_url && (
                      <a
                        href={rpt.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white transition-all text-[10px] font-bold flex items-center gap-1 shrink-0 border border-blue-200 cursor-pointer"
                      >
                        <ArrowDownTrayIcon className="w-3 h-3" /> PDF
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-white rounded-xl border border-dashed border-gray-200 text-center">
                <p className="text-[11px] text-gray-500 font-medium">No PDF generated yet for this project.</p>
                <p className="text-[10px] text-gray-400 mt-0.5">Approve an AI draft or complete a milestone to download official PDF.</p>
              </div>
            )}
          </div>
        </aside>

      </div>
    </div>
  )
}

export default FreelancerWorkPage
