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
const isPending  = (m) => m?.status === 'PENDING'

// ─── Main Component ───────────────────────────────────────────────────────────
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
  // { [milestoneId]: { mode: 'AI'|'MANUAL', messages: [], conversationId, activeDraft, pdfUrl } }
  const [workspaceMap, setWorkspaceMap]       = useState({})

  const [inputValue, setInputValue]           = useState('')
  const [errorMsg, setErrorMsg]               = useState('')

  // Manual submission form
  const [manualForm, setManualForm]           = useState({ description: '', files_link: '' })

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
          mode: 'AI',
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
  const mode             = ws.mode || 'AI'
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
          mode: 'AI',
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
                messages: [
                  ...(prev[activeMilestoneId]?.messages || []),
                  {
                    role: 'assistant',
                    content: `🎉 **Report Approved & Compiled!** Your official client report is ready for download.`,
                    pdf_url,
                    timestamp: new Date().toISOString(),
                  }
                ]
              }
            }))
            setApproving(false)
            loadContextBundle()
          }
        } else if (data.type === 'ai_draft_pdf_error') {
          setApproving(false)
          alert('Failed to compile PDF: ' + (data.payload?.error || 'Unknown error'))
        } else if (['milestone_submitted', 'milestone_approved', 'milestone_funded'].includes(data.type)) {
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

    // If AI report is already created, guide user to Manual Mode
    if (hasApprovedReport && (text.toLowerCase().includes('draft') || text.toLowerCase().includes('report') || text.toLowerCase().includes('compile'))) {
      setWorkspaceMap(prev => ({
        ...prev,
        [activeMilestoneId]: {
          ...prev[activeMilestoneId],
          messages: [
            ...(prev[activeMilestoneId]?.messages || []),
            { role: 'user', content: text, timestamp: new Date().toISOString() },
            {
              role: 'assistant',
              content: `An official AI worklog report has already been created for **${activeMilestone?.title || 'this milestone'}**. To submit additional updates or revisions, please switch to **Manual Worklog Mode**.`,
              show_manual_action: true,
              timestamp: new Date().toISOString(),
            }
          ]
        }
      }))
      if (!textToSend) setInputValue('')
      return
    }

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
      const res = await aiWorklogAPI.sendChatMessage(contractId, text, conversationId)
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

  // ── Approve AI Draft & Generate PDF ────────────────────────────────────────
  const handleApproveDraft = async (draftIdToApprove = null) => {
    const targetDraftId = draftIdToApprove || activeDraft?.id
    setApproving(true)
    try {
      const res = await aiWorklogAPI.approveDraft(contractId, targetDraftId)
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
                content: `🎉 **Report Approved & Submitted!** Your official client worklog report has been generated and submitted to the client.`,
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

  // ── Manual Milestone Deliverable Submission ────────────────────────────────
  const handleManualSubmit = async (e) => {
    e.preventDefault()
    if (!manualForm.description || !activeMilestoneId) return
    setSending(true)
    try {
      await paymentsAPI.completeMilestone(activeMilestoneId, {
        deliverable_description: `${manualForm.description}${manualForm.files_link ? ` | Link: ${manualForm.files_link}` : ''}`,
      })
      alert(`Deliverable for "${activeMilestone?.title}" submitted to client for approval!`)
      setManualForm({ description: '', files_link: '' })
      loadContextBundle()
    } catch (err) {
      console.error(err)
      alert(err.response?.data?.error || 'Milestone deliverable submitted!')
      loadContextBundle()
    } finally {
      setSending(false)
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
            className="mt-6 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-all shadow-md shadow-blue-600/20"
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
                Worklog Workspace
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
              <div>
                <BriefcaseIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-base font-bold text-gray-700">Select a milestone from the right to begin</p>
                <p className="text-xs text-gray-400 mt-1">Milestones funded into escrow are ready for work logs.</p>
              </div>
            </div>
          ) : isApproved(activeMilestone) ? (
            /* ── APPROVED MILESTONE: Clean White Completed View (No editing needed) ── */
            <div className="flex-1 min-h-0 flex flex-col items-center justify-center bg-gray-50/60 p-6 sm:p-10 overflow-y-auto">
              <div className="max-w-md w-full bg-white rounded-3xl border border-gray-200 p-8 shadow-md space-y-6 text-center animate-in fade-in zoom-in-95 duration-200">
                <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 shadow-2xs">
                  <CheckCircleIcon className="w-9 h-9" />
                </div>
                <div>
                  <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase tracking-wide">
                    Milestone Completed & Approved
                  </span>
                  <h2 className="text-xl font-bold text-gray-900 mt-3">{activeMilestone.title}</h2>
                  {activeMilestone.description && (
                    <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{activeMilestone.description}</p>
                  )}
                </div>

                <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-2xl flex items-center justify-between">
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
            /* ── ACTIVE / FUNDED / SUBMITTED MILESTONE: Fixed Workspace ── */
            <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
              {/* Mode Switcher Tabs (Fixed at Top) */}
              <div className="flex border-b border-gray-200 shrink-0 bg-gray-50/80">
                <button
                  onClick={() => updateWS({ mode: 'AI' })}
                  className={`flex-1 py-3 text-xs sm:text-sm font-bold text-center transition-all flex items-center justify-center gap-2 cursor-pointer ${
                    mode === 'AI'
                      ? 'text-blue-600 border-b-2 border-blue-600 bg-white shadow-2xs'
                      : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  <SparklesIcon className="w-4 h-4 text-blue-600" />
                  AI Assistant Mode (One-Time Report)
                  {hasApprovedReport && (
                    <span className="text-[10px] font-black px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded ml-1">
                      DONE
                    </span>
                  )}
                </button>
                <button
                  onClick={() => updateWS({ mode: 'MANUAL' })}
                  className={`flex-1 py-3 text-xs sm:text-sm font-bold text-center transition-all flex items-center justify-center gap-2 cursor-pointer ${
                    mode === 'MANUAL'
                      ? 'text-blue-600 border-b-2 border-blue-600 bg-white shadow-2xs'
                      : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  <DocumentTextIcon className="w-4 h-4 text-blue-600" />
                  Manual Worklog Mode (Multi-Submission)
                </button>
              </div>

              {mode === 'AI' ? (
                /* ── AI CHAT ASSISTANT MODE (Fixed Layout, Scrollable Messages) ── */
                <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
                  {/* Banner when AI report is already created for this milestone */}
                  {hasApprovedReport && (
                    <div className="mx-6 mt-4 p-4 bg-blue-50/80 border border-blue-200 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs shrink-0">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-600 text-white rounded-xl shadow-xs shrink-0">
                          <CheckCircleIcon className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-gray-900">AI Worklog Report Already Compiled</p>
                          <p className="text-xs text-gray-600 mt-0.5">
                            The AI report for <strong>{activeMilestone?.title}</strong> has been generated. To submit additional changes or revisions requested by the client, use <strong>Manual Worklog Mode</strong>.
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => updateWS({ mode: 'MANUAL' })}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all whitespace-nowrap active:scale-95 flex items-center gap-1.5 shrink-0 cursor-pointer"
                      >
                        Switch to Manual Mode <ArrowRightIcon className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Messages Stream (Independently Scrollable Container) */}
                  <div
                    ref={messagesContainerRef}
                    className="flex-1 min-h-0 overflow-y-auto p-6 space-y-6 scroll-smooth"
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

                          <div className={`max-w-[85%] sm:max-w-[75%] space-y-3 ${isUser ? 'items-end' : 'items-start'}`}>
                            <div
                              className={`rounded-2xl p-4 text-sm leading-relaxed ${
                                isUser
                                  ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-600/20'
                                  : 'bg-gray-50 border border-gray-200 text-gray-900 rounded-bl-none shadow-2xs'
                              }`}
                            >
                              <div className="whitespace-pre-wrap">{msg.content}</div>

                              {/* Download PDF button if attached */}
                              {msg.pdf_url && (
                                <div className="mt-3 pt-3 border-t border-gray-200">
                                  <a
                                    href={msg.pdf_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all cursor-pointer"
                                  >
                                    <ArrowDownTrayIcon className="w-4 h-4" />
                                    Download Official PDF Report
                                  </a>
                                </div>
                              )}

                              {/* Suggest manual action */}
                              {msg.show_manual_action && (
                                <div className="mt-3 pt-3 border-t border-gray-200">
                                  <button
                                    onClick={() => updateWS({ mode: 'MANUAL' })}
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all cursor-pointer"
                                  >
                                    Go to Manual Worklog Mode <ArrowRightIcon className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              )}
                            </div>

                            {/* Structured AI Report Draft Card */}
                            {msg.has_draft && msg.draft_data && (
                              <div className="rounded-2xl bg-white border-2 border-blue-100 p-5 shadow-lg space-y-4">
                                <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                                  <div className="flex items-center gap-2">
                                    <DocumentTextIcon className="w-5 h-5 text-blue-600" />
                                    <h4 className="text-sm font-bold text-gray-900">{msg.draft_data.title}</h4>
                                  </div>
                                  <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-xs font-bold">
                                    {msg.draft_data.hours_worked || 0} Hours Logged
                                  </span>
                                </div>

                                <div className="space-y-1">
                                  <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                    1. Executive Summary
                                  </p>
                                  <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200 leading-relaxed">
                                    {msg.draft_data.section_summary}
                                  </p>
                                </div>

                                <div className="space-y-1">
                                  <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                    2. Deliverables Completed
                                  </p>
                                  <div className="space-y-1.5">
                                    {msg.draft_data.section_deliverables?.map((item, idx) => (
                                      <div
                                        key={idx}
                                        className="p-3 rounded-lg bg-gray-50 border border-gray-200 text-xs flex items-center justify-between"
                                      >
                                        <span className="font-semibold text-gray-900">{item.title}</span>
                                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                                          {item.status || 'COMPLETED'}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                <div className="space-y-1">
                                  <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                    3. Next Steps & Blockers
                                  </p>
                                  <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200 leading-relaxed">
                                    {msg.draft_data.section_next_steps}
                                  </p>
                                </div>

                                {/* Approve / Action Button */}
                                <div className="pt-2">
                                  {hasApprovedReport ? (
                                    <a
                                      href={pdfUrl || '#'}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
                                    >
                                      <CheckCircleIcon className="w-4 h-4" />
                                      Report Approved & Submitted — View PDF
                                    </a>
                                  ) : (
                                    <button
                                      onClick={() => handleApproveDraft(msg.draft_id)}
                                      disabled={approving}
                                      className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all disabled:opacity-50 active:scale-98 cursor-pointer"
                                    >
                                      {approving ? (
                                        <>
                                          <ArrowPathIcon className="w-4 h-4 animate-spin" />
                                          Compiling PDF & Submitting to Client...
                                        </>
                                      ) : (
                                        <>
                                          <CheckCircleIcon className="w-4 h-4" />
                                          Approve Draft & Generate Official PDF
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
                        <div className="bg-gray-50 border border-gray-200 rounded-2xl rounded-bl-none px-4 py-3 text-xs text-gray-600 flex items-center gap-2">
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
                    {hasApprovedReport ? (
                      <button
                        onClick={() => updateWS({ mode: 'MANUAL' })}
                        className="px-3.5 py-1.5 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold whitespace-nowrap transition-colors border border-blue-200 shadow-2xs shrink-0 flex items-center gap-1 cursor-pointer"
                      >
                        Go to Manual Worklog <ArrowRightIcon className="w-3 h-3" />
                      </button>
                    ) : (
                      ['draft my progress report', 'what is my timeline of my progress report'].map((prompt, i) => (
                        <button
                          key={i}
                          onClick={() => handleSendMessage(prompt)}
                          disabled={sending}
                          className="px-3.5 py-1.5 rounded-full bg-white hover:bg-blue-50 text-gray-700 hover:text-blue-600 text-xs font-semibold whitespace-nowrap transition-colors border border-gray-200 shadow-2xs shrink-0 cursor-pointer disabled:opacity-50"
                        >
                          {prompt}
                        </button>
                      ))
                    )}
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
                            ? 'AI report already compiled. Switch to Manual Mode for further submissions...'
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
              ) : (
                /* ── MANUAL WORKLOG MODE (Multi-Submission) ── */
                <div className="flex-1 min-h-0 overflow-y-auto p-6 md:p-10">
                  <div className="max-w-3xl mx-auto space-y-6">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">Submit Milestone Worklog (Manual)</h2>
                      <p className="text-sm text-gray-500 mt-1">
                        Logging work for <strong className="text-gray-800">{activeMilestone?.title}</strong>. You can make multiple submissions and revisions here.
                      </p>
                    </div>

                    <form onSubmit={handleManualSubmit} className="space-y-6">
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-1.5">
                          Target Milestone
                        </label>
                        <div className="p-4 bg-gray-50 border border-gray-200 rounded-2xl flex items-center justify-between">
                          <div>
                            <p className="text-sm font-bold text-gray-900">{activeMilestone?.title}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{activeMilestone?.description || 'Milestone scope deliverable'}</p>
                          </div>
                          <span className="text-sm font-black text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1 rounded-xl">
                            ${parseFloat(activeMilestone?.amount || 0).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">
                          Work Description & Deliverables Summary <span className="text-rose-500">*</span>
                        </label>
                        <textarea
                          rows={6}
                          required
                          value={manualForm.description}
                          onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                          placeholder="Describe the tasks completed, revisions made, pull request links, verification steps, etc..."
                          className="w-full p-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm leading-relaxed shadow-xs"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">
                          Attachment Link (Optional)
                        </label>
                        <input
                          type="url"
                          value={manualForm.files_link}
                          onChange={(e) => setManualForm({ ...manualForm, files_link: e.target.value })}
                          placeholder="https://github.com/... or Figma link or Drive URL"
                          className="w-full p-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm shadow-xs"
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={sending}
                        className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-sm font-bold transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 active:scale-98 cursor-pointer"
                      >
                        {sending ? 'Submitting Deliverable...' : 'Submit Deliverable to Client for Approval'}
                      </button>
                    </form>
                  </div>
                </div>
              )}
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
                              className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded-lg border border-emerald-200 transition-all shadow-2xs"
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
                        className="px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white transition-all text-[10px] font-bold flex items-center gap-1 shrink-0 border border-blue-200"
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
