import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { aiWorklogAPI } from '../../api/worklogs'
import { paymentsAPI } from '../../api/payments'
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
} from '@heroicons/react/24/outline'
import { WorkPageSkeleton } from '../../components/common/Skeleton'

const FreelancerWorkPage = () => {
  const { contractId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const urlMilestoneId = searchParams.get('milestone')

  // State
  const [mode, setMode] = useState(urlMilestoneId ? 'MANUAL' : 'AI')
  const [manualForm, setManualForm] = useState({
    milestoneId: urlMilestoneId || '',
    description: '',
    files_link: ''
  })
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [approving, setApproving] = useState(false)
  const [contextData, setContextData] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [activeDraft, setActiveDraft] = useState(null)
  const [pdfUrl, setPdfUrl] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  const messagesContainerRef = useRef(null)

  useEffect(() => {
    if (contractId) {
      loadContextBundle()
    }
  }, [contractId])

  // Internal scroll only within messages container (prevent jumping window)
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }, [messages.length, sending])

  const loadContextBundle = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const res = await aiWorklogAPI.getContext(contractId)
      const data = res.data
      setContextData(data)

      if (data.active_draft) {
        setActiveDraft(data.active_draft)
        if (data.active_draft.pdf_url) {
          setPdfUrl(data.active_draft.pdf_url)
        }
      }

      if (data.conversation) {
        setConversationId(data.conversation.id)
        if (data.conversation.messages && data.conversation.messages.length > 0) {
          setMessages(data.conversation.messages)
        } else {
          setMessages([
            {
              role: 'assistant',
              content: `Hello! I'm your AI Worklog Assistant for **${data.contract?.title || 'this project'}**. I'm grounded with your project requirements via Qdrant. Tell me what you worked on today, or click a quick prompt below to draft your report.`,
            },
          ])
        }
      } else {
        setMessages([
          {
            role: 'assistant',
            content: `Hello! I'm your AI Worklog Assistant for **${data.contract?.title || 'this project'}**. I'm grounded with your project requirements via Qdrant. Tell me what you worked on today, or click a quick prompt below to draft your report.`,
          },
        ])
      }
    } catch (err) {
      console.error('Error loading AI context bundle:', err)
      setErrorMsg('Failed to load contract context. Please make sure you have access.')
    } finally {
      setLoading(false)
    }
  }

  const { contract, deliverables = [], previous_reports = [], qdrant_status = {} } = contextData || {}
  const hasApprovedReport = Boolean(pdfUrl || activeDraft?.status === 'APPROVED' || (previous_reports && previous_reports.length > 0))

  const handleSendMessage = async (textToSend = null) => {
    const text = textToSend || inputValue
    if (!text || !text.trim() || sending) return

    // If an AI worklog report is already generated and user is trying to generate again, redirect to manual
    if (hasApprovedReport && (text.toLowerCase().includes('draft') || text.toLowerCase().includes('report') || text.toLowerCase().includes('compile'))) {
      const userMsg = {
        role: 'user',
        content: text.trim(),
        timestamp: new Date().toISOString(),
      }
      const assistantMsg = {
        role: 'assistant',
        content: `An official AI worklog report has already been created and approved for this contract. For additional progress submissions or milestone deliverables, please switch to **Manual Worklog Mode**.`,
        timestamp: new Date().toISOString(),
        show_manual_action: true,
      }
      setMessages(prev => [...prev, userMsg, assistantMsg])
      if (!textToSend) setInputValue('')
      return
    }

    const userMsg = {
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    if (!textToSend) setInputValue('')
    setSending(true)

    try {
      const res = await aiWorklogAPI.sendChatMessage(contractId, text.trim(), conversationId)
      const data = res.data

      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      const assistantMsg = {
        role: 'assistant',
        content: data.reply,
        timestamp: new Date().toISOString(),
        has_draft: data.is_draft_ready,
        draft_data: data.draft,
        draft_id: data.draft_id,
      }

      setMessages((prev) => [...prev, assistantMsg])

      if (data.is_draft_ready && data.draft) {
        setActiveDraft({
          ...data.draft,
          id: data.draft_id,
        })
      }
    } catch (err) {
      console.error('Error sending message to AI agent:', err)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          is_error: true,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  // WebSocket for AI PDF compilation updates
  useEffect(() => {
    if (!contractId) return

    const token =
      localStorage.getItem('access_token') ||
      sessionStorage.getItem('access_token') ||
      ''
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host =
      window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
    const wsUrl = `${protocol}//${host}/ws/contract/${contractId}/?token=${token}`

    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'ai_draft_pdf_ready') {
          const { pdf_url } = data.payload
          setPdfUrl(pdf_url)
          setApproving(false)
          setActiveDraft((prev) => (prev ? { ...prev, status: 'APPROVED', pdf_url } : null))
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: `🎉 **Report Approved & Compiled!** Your official client report is ready for download.`,
              pdf_url,
            },
          ])
          loadContextBundle()
        } else if (data.type === 'ai_draft_pdf_error') {
          setApproving(false)
          alert('Failed to compile PDF: ' + data.payload.error)
        }
      } catch {}
    }

    ws.onerror = () => ws.close()

    return () => {
      ws.close()
    }
  }, [contractId])

  const handleApproveDraft = async (draftIdToApprove = null) => {
    const targetDraftId = draftIdToApprove || activeDraft?.id
    setApproving(true)
    try {
      await aiWorklogAPI.approveDraft(contractId, targetDraftId)
    } catch (err) {
      console.error('Error approving report draft:', err)
      alert('Failed to approve report PDF. Please try again.')
      setApproving(false)
    }
  }

  const handleManualSubmit = async (e) => {
    e.preventDefault()
    if (!manualForm.milestoneId || !manualForm.description) return
    setSending(true)
    try {
      await paymentsAPI.completeMilestone(manualForm.milestoneId, {
        deliverable_description: `${manualForm.description}${manualForm.files_link ? ` | Link: ${manualForm.files_link}` : ''}`,
      })
      alert('Milestone deliverable submitted to client for approval!')
      setManualForm({ ...manualForm, description: '', files_link: '' })
      loadContextBundle()
    } catch (err) {
      console.error(err)
      alert(err.response?.data?.error || 'Milestone deliverable submitted!')
      loadContextBundle()
    } finally {
      setSending(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <WorkPageSkeleton />
      </div>
    )
  }

  if (errorMsg || !contextData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white border border-gray-200 rounded-3xl p-8 text-center shadow-lg">
          <ExclamationCircleIcon className="w-12 h-12 text-rose-500 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-gray-900">Access Denied or Not Found</h2>
          <p className="text-gray-500 text-sm mt-2">{errorMsg || 'Could not load contract context.'}</p>
          <button
            onClick={() => navigate('/freelancer/worklogs')}
            className="mt-6 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-all shadow-md shadow-blue-600/20"
          >
            Back to Worklogs Hub
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col w-full h-full bg-white text-gray-900 overflow-hidden">
      {/* ── Top Header ────────────────────────────────────────── */}
      <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0 z-20 shadow-xs">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/freelancer/worklogs')}
            className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors flex items-center gap-1.5 text-xs font-bold"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Worklogs
          </button>
          <div className="h-5 w-px bg-gray-200"></div>
          <div>
            <h1 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              {contract.title}
              <span className="text-xs px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 font-bold border border-blue-200">
                Contract #{contract.id}
              </span>
            </h1>
          </div>
        </div>
      </header>

      {/* ── Main Layout: Expanded Workspace on Left + Clear Deliverables/Reports Sidebar on Right ── */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* ── MAIN WORKSPACE (AI Assistant / Manual Form) ── */}
        <main className="flex-1 flex flex-col bg-white border-r border-gray-200 overflow-hidden">
          {/* Mode Switcher */}
          <div className="flex border-b border-gray-200 shrink-0 bg-gray-50/70">
            <button
              onClick={() => setMode('AI')}
              className={`flex-1 py-3.5 text-sm font-bold text-center transition-all flex items-center justify-center gap-2 ${
                mode === 'AI' ? 'text-blue-600 border-b-2 border-blue-600 bg-white shadow-2xs' : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              <SparklesIcon className="w-4 h-4 text-blue-600" />
              AI Assistant Mode
            </button>
            <button
              onClick={() => setMode('MANUAL')}
              className={`flex-1 py-3.5 text-sm font-bold text-center transition-all flex items-center justify-center gap-2 ${
                mode === 'MANUAL' ? 'text-blue-600 border-b-2 border-blue-600 bg-white shadow-2xs' : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              <DocumentTextIcon className="w-4 h-4 text-blue-600" />
              Manual Worklog Mode
            </button>
          </div>

          {mode === 'AI' ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Once Generated Alert: If an AI report is already created, show Go to Manual banner */}
              {hasApprovedReport && (
                <div className="mx-6 mt-4 p-4 bg-blue-50/80 border border-blue-200 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs shrink-0">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-600 text-white rounded-xl shadow-xs shrink-0">
                      <CheckCircleIcon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-gray-900">AI Worklog Report Already Compiled</p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        An official AI worklog report has already been created for this project. To log additional updates or submit discrete milestone tasks, please use Manual Worklog Mode.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setMode('MANUAL')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all whitespace-nowrap active:scale-95 flex items-center gap-1.5"
                  >
                    Go to Manual Mode <ArrowRightIcon className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {/* Chat Messages Stream */}
              <div
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth"
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
                              : 'bg-gray-50 border border-gray-200 text-gray-800 rounded-bl-none shadow-2xs'
                          }`}
                        >
                          <div className="whitespace-pre-wrap">{msg.content}</div>

                          {/* Direct PDF Link if available */}
                          {msg.pdf_url && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <a
                                href={msg.pdf_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all"
                              >
                                <ArrowDownTrayIcon className="w-4 h-4" />
                                Download Official PDF Report
                              </a>
                            </div>
                          )}

                          {/* Go to manual action suggestion button */}
                          {msg.show_manual_action && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <button
                                onClick={() => setMode('MANUAL')}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all"
                              >
                                Go to Manual Worklog Mode <ArrowRightIcon className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          )}
                        </div>

                        {/* Inline Structured Draft Card */}
                        {msg.has_draft && msg.draft_data && (
                          <div className="rounded-2xl bg-white border-2 border-blue-100 p-5 shadow-lg space-y-4">
                            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                              <div className="flex items-center gap-2">
                                <DocumentTextIcon className="w-5 h-5 text-blue-600" />
                                <h4 className="text-sm font-bold text-gray-900">{msg.draft_data.title}</h4>
                              </div>
                              <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-xs font-bold">
                                {msg.draft_data.hours_worked || 0} Hours
                              </span>
                            </div>

                            {/* Section 1: Executive Summary */}
                            <div className="space-y-1">
                              <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                1. Executive Summary
                              </p>
                              <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200 leading-relaxed">
                                {msg.draft_data.section_summary}
                              </p>
                            </div>

                            {/* Section 2: Deliverables Completed */}
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

                            {/* Section 3: Next Steps & Priorities */}
                            <div className="space-y-1">
                              <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                                3. Next Steps & Blockers
                              </p>
                              <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200 leading-relaxed">
                                {msg.draft_data.section_next_steps}
                              </p>
                            </div>

                            {/* Approve Draft Button */}
                            <div className="pt-2">
                              <button
                                onClick={() => handleApproveDraft(msg.draft_id)}
                                disabled={approving}
                                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all disabled:opacity-50 active:scale-98"
                              >
                                {approving ? (
                                  <>
                                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                                    Compiling WeasyPrint PDF & Uploading...
                                  </>
                                ) : (
                                  <>
                                    <CheckCircleIcon className="w-4 h-4" />
                                    Approve Draft & Generate Official PDF
                                  </>
                                )}
                              </button>
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
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce"></span>
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:0.2s]"></span>
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:0.4s]"></span>
                      <span className="ml-1 font-medium">Querying Qdrant context & synthesizing...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Action Suggestion Chips */}
              <div className="px-6 py-2.5 bg-gray-50 border-t border-gray-200 flex items-center gap-2 overflow-x-auto scrollbar-none shrink-0">
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider shrink-0">Quick Prompts:</span>
                {hasApprovedReport ? (
                  <button
                    onClick={() => setMode('MANUAL')}
                    className="px-3.5 py-1.5 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold whitespace-nowrap transition-colors border border-blue-200 shadow-2xs shrink-0 flex items-center gap-1"
                  >
                    Go to Manual Worklog <ArrowRightIcon className="w-3 h-3" />
                  </button>
                ) : (
                  [
                    'draft my progress report',
                    'what is my timeline of my progress report',
                  ].map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendMessage(prompt)}
                      disabled={sending}
                      className="px-3.5 py-1.5 rounded-full bg-white hover:bg-blue-50 text-gray-700 hover:text-blue-600 text-xs font-semibold whitespace-nowrap transition-colors border border-gray-200 shadow-2xs shrink-0"
                    >
                      {prompt}
                    </button>
                  ))
                )}
              </div>

              {/* Chat Input Bar */}
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
                    placeholder={hasApprovedReport ? "Ask questions about project context or switch to Manual Mode to log work..." : "Describe your work, request changes, or ask the AI to draft a report..."}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    disabled={sending}
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={!inputValue.trim() || sending}
                    className="p-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl shadow-md shadow-blue-600/20 transition-all shrink-0 active:scale-95"
                  >
                    <PaperAirplaneIcon className="w-5 h-5" />
                  </button>
                </form>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6 md:p-10">
              <div className="max-w-3xl mx-auto space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Submit Deliverable Manually</h2>
                  <p className="text-sm text-gray-500 mt-1">Log your work and submit it directly to a milestone for client review.</p>
                </div>
                
                <form onSubmit={handleManualSubmit} className="space-y-6">
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Select Milestone</label>
                    <select
                      value={manualForm.milestoneId}
                      onChange={(e) => setManualForm({ ...manualForm, milestoneId: e.target.value })}
                      required
                      className="w-full p-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm font-medium shadow-xs"
                    >
                      <option value="">-- Choose an active milestone --</option>
                      {contextData.milestones?.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.title} - ${m.amount} ({m.status})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Work Description & Deliverables</label>
                    <textarea
                      rows={6}
                      required
                      value={manualForm.description}
                      onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                      placeholder="Describe the tasks completed, PR links, deliverables summary..."
                      className="w-full p-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm leading-relaxed shadow-xs"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Attachment Link (Optional)</label>
                    <input
                      type="url"
                      value={manualForm.files_link}
                      onChange={(e) => setManualForm({ ...manualForm, files_link: e.target.value })}
                      placeholder="https://github.com/... or Figma link"
                      className="w-full p-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm shadow-xs"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={sending}
                    className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-sm font-bold transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 active:scale-98 cursor-pointer"
                  >
                    {sending ? 'Submitting...' : 'Submit Worklog to Client'}
                  </button>
                </form>
              </div>
            </div>
          )}
        </main>

        {/* ── RIGHT PANEL: Previous Compiled Reports (At Top), Current Ready Deliverables & Contract Scope ── */}
        <aside className="w-80 lg:w-96 bg-gray-50/70 p-6 flex flex-col gap-6 overflow-y-auto shrink-0">
          
          {/* Previous Compiled Reports (Positioned on Upper Part) */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              Previous Compiled Reports ({previous_reports.length})
            </h3>
            {previous_reports.length === 0 ? (
              <p className="text-xs text-gray-400 italic bg-white p-3.5 rounded-xl border border-gray-200 text-center">
                No approved reports generated yet.
              </p>
            ) : (
              <div className="space-y-2">
                {previous_reports.map((rpt, idx) => (
                  <div
                    key={rpt.id || idx}
                    className="p-3.5 rounded-xl bg-white border border-gray-200 shadow-2xs flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <DocumentTextIcon className="w-5 h-5 text-blue-600 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-gray-900 truncate">{rpt.title}</p>
                        <p className="text-[10px] text-gray-500">
                          {rpt.hours_worked}h logged • {new Date(rpt.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    {rpt.pdf_url && (
                      <a
                        href={rpt.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white transition-all text-xs font-bold flex items-center gap-1 shrink-0 border border-blue-200"
                      >
                        <ArrowDownTrayIcon className="w-3.5 h-3.5" />
                        PDF
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Current Deliverable Status (Only shown when PDF is ready or Draft is pending) */}
          {(pdfUrl || activeDraft) && (
            <div>
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">
                Current Deliverable
              </h3>
              
              {pdfUrl ? (
                <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-2xl flex flex-col items-center text-center space-y-3 shadow-sm">
                  <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 shadow-sm">
                    <CheckCircleIcon className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-900">PDF Ready</p>
                    <p className="text-xs text-gray-600 mt-1">Your deliverable has been compiled and is ready for the client.</p>
                  </div>
                  <a
                    href={pdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition-all mt-2"
                  >
                    <ArrowDownTrayIcon className="w-4 h-4" />
                    Download PDF
                  </a>
                </div>
              ) : (
                <div className="p-5 bg-amber-50 border border-amber-200 rounded-2xl flex flex-col items-center text-center space-y-3 shadow-sm">
                  <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center text-amber-600 shadow-sm">
                    <DocumentTextIcon className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-900">Draft Pending</p>
                    <p className="text-xs text-gray-600 mt-1">Review the draft in the chat and approve it to generate the PDF.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Contract Overview Box */}
          <div className="rounded-2xl bg-white border border-gray-200 p-5 space-y-3 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Contract Budget</span>
              <span className="text-sm font-black text-blue-600">${parseFloat(contract.rate || 0).toLocaleString()}</span>
            </div>
            <p className="text-xs text-gray-600 line-clamp-3 leading-relaxed">{contract.description}</p>
            <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
              <span>Client: <strong className="text-gray-800">{contract.client_name}</strong></span>
              <span>Status: <strong className="text-blue-600 font-bold">{contract.status}</strong></span>
            </div>
          </div>

          {/* Deliverables Overview Checklist */}
          {deliverables.length > 0 && (
            <div className="space-y-2.5">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Assigned Deliverables ({deliverables.length})
              </h3>
              <div className="space-y-2">
                {deliverables.map((d) => (
                  <div
                    key={d.id}
                    className="p-3 rounded-xl bg-white border border-gray-200 shadow-2xs flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <h4 className="text-xs font-bold text-gray-900 truncate">{d.title}</h4>
                      <p className="text-[10px] text-gray-500 truncate">{d.description}</p>
                    </div>
                    <span
                      className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded shrink-0 ${
                        d.status === 'APPROVED'
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : d.status === 'SUBMITTED'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      {d.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </aside>
      </div>
    </div>
  )
}

export default FreelancerWorkPage
