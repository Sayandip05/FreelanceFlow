import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { aiWorklogAPI } from '../../api/worklogs'
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
  UserCircleIcon,
} from '@heroicons/react/24/outline'

const FreelancerWorkPage = () => {
  const { contractId } = useParams()
  const navigate = useNavigate()

  // State
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

  const chatEndRef = useRef(null)

  useEffect(() => {
    if (contractId) {
      loadContextBundle()
    }
  }, [contractId])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

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
          // Default initial greeting
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

  const handleSendMessage = async (textToSend = null) => {
    const text = textToSend || inputValue
    if (!text || !text.trim() || sending) return

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

  const handleApproveDraft = async (draftIdToApprove = null) => {
    const targetDraftId = draftIdToApprove || activeDraft?.id
    setApproving(true)
    try {
      const res = await aiWorklogAPI.approveDraft(contractId, targetDraftId)
      const data = res.data
      if (data.pdf_url) {
        setPdfUrl(data.pdf_url)
        setActiveDraft((prev) => (prev ? { ...prev, status: 'APPROVED', pdf_url: data.pdf_url } : null))
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `🎉 **Report Approved & Compiled!** Your official client report is ready for download.`,
            pdf_url: data.pdf_url,
          },
        ])
        // Refresh context to update past reports list
        loadContextBundle()
      }
    } catch (err) {
      console.error('Error approving report draft:', err)
      alert('Failed to compile and approve report PDF. Please try again.')
    } finally {
      setApproving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center text-gray-600">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-sm font-semibold tracking-wide">Connecting to Qdrant & Assembling Workspace...</p>
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
            className="mt-6 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-all shadow-md"
          >
            Back to Worklogs Hub
          </button>
        </div>
      </div>
    )
  }

  const { contract, deliverables = [], stats = {}, previous_reports = [], qdrant_status = {} } = contextData

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col h-screen overflow-hidden">
      {/* Top Navbar */}
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0 z-20 shadow-xs">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/freelancer/worklogs')}
            className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors flex items-center gap-1.5 text-xs font-bold"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Hub
          </button>
          <div className="h-5 w-px bg-gray-200"></div>
          <div>
            <h1 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              {contract.title}
              <span className="text-xs px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-100">
                Contract #{contract.id}
              </span>
            </h1>
          </div>
        </div>

        {/* Vector Grounding Pill */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs">
            <ShieldCheckIcon className="w-4 h-4 text-emerald-600" />
            <span className="text-gray-700 font-medium">Qdrant Vector Cloud:</span>
            <span className="text-emerald-700 font-bold">
              {qdrant_status.is_initialized ? `${qdrant_status.vectors_count} Grounded Docs` : 'Grounded'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL: Context, Deliverables, Stats & Past Reports */}
        <aside className="w-1/2 lg:w-5/12 border-r border-gray-200 bg-gray-50/70 p-6 overflow-y-auto space-y-6">
          {/* Contract Overview Box */}
          <div className="rounded-2xl bg-white border border-gray-200/90 p-5 space-y-3 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Contract Scope & Budget</span>
              <span className="text-sm font-black text-emerald-600">${parseFloat(contract.rate || 0).toLocaleString()}</span>
            </div>
            <p className="text-xs text-gray-600 line-clamp-3 leading-relaxed">{contract.description}</p>
            <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
              <span>Client: <strong className="text-gray-800">{contract.client_name}</strong></span>
              <span>Status: <strong className="text-indigo-600">{contract.status}</strong></span>
            </div>
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-2xl bg-indigo-50/60 border border-indigo-100 p-4 shadow-2xs">
              <div className="flex items-center gap-2 text-indigo-600 text-xs font-semibold uppercase tracking-wider">
                <ClockIcon className="w-4 h-4" />
                Hours Logged
              </div>
              <p className="text-2xl font-black text-gray-900 mt-1">{stats.total_hours_logged || 0} hrs</p>
            </div>
            <div className="rounded-2xl bg-purple-50/60 border border-purple-100 p-4 shadow-2xs">
              <div className="flex items-center gap-2 text-purple-600 text-xs font-semibold uppercase tracking-wider">
                <CheckCircleIcon className="w-4 h-4" />
                Deliverables Done
              </div>
              <p className="text-2xl font-black text-gray-900 mt-1">
                {stats.approved_deliverables || 0} / {stats.total_deliverables || 0}
              </p>
            </div>
          </div>

          {/* Deliverables Checklist */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Assigned Deliverables ({deliverables.length})
              </h3>
            </div>
            {deliverables.length === 0 ? (
              <p className="text-xs text-gray-400 italic">No discrete deliverables registered yet.</p>
            ) : (
              <div className="space-y-2.5">
                {deliverables.map((d) => (
                  <div
                    key={d.id}
                    className="p-3.5 rounded-xl bg-white border border-gray-200/90 shadow-2xs hover:border-indigo-200 transition-all flex items-start justify-between gap-3"
                  >
                    <div>
                      <h4 className="text-sm font-bold text-gray-900">{d.title}</h4>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">{d.description}</p>
                    </div>
                    <span
                      className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-md shrink-0 ${
                        d.status === 'APPROVED'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : d.status === 'SUBMITTED'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-gray-100 text-gray-600 border border-gray-200'
                      }`}
                    >
                      {d.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Past Approved Reports & PDF Downloads */}
          <div className="space-y-3 pt-4 border-t border-gray-200">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              Previous Compiled Reports ({previous_reports.length})
            </h3>
            {previous_reports.length === 0 ? (
              <p className="text-xs text-gray-400 italic">No approved reports generated yet for this contract.</p>
            ) : (
              <div className="space-y-2">
                {previous_reports.map((rpt, idx) => (
                  <div
                    key={rpt.id || idx}
                    className="p-3 rounded-xl bg-white border border-gray-200/90 shadow-2xs flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-2.5">
                      <DocumentTextIcon className="w-5 h-5 text-indigo-600 shrink-0" />
                      <div>
                        <p className="text-xs font-bold text-gray-900 line-clamp-1">{rpt.title}</p>
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
                        className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white transition-all text-xs font-bold flex items-center gap-1 shrink-0 border border-indigo-100"
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
        </aside>

        {/* RIGHT PANEL: Interactive AI Assistant Stream & Inline Report Draft */}
        <main className="w-1/2 lg:w-7/12 flex flex-col bg-white">
          {/* Chat Messages Stream */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, i) => {
              const isUser = msg.role === 'user'
              return (
                <div key={i} className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
                  {!isUser && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 shadow-sm">
                      <SparklesIcon className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div className={`max-w-[85%] space-y-3 ${isUser ? 'items-end' : 'items-start'}`}>
                    <div
                      className={`rounded-2xl p-4 text-sm leading-relaxed ${
                        isUser
                          ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/20'
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
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all"
                          >
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Download Official PDF Report
                          </a>
                        </div>
                      )}
                    </div>

                    {/* Inline Structured Draft Card */}
                    {msg.has_draft && msg.draft_data && (
                      <div className="rounded-2xl bg-white border-2 border-indigo-500/30 p-5 shadow-xl space-y-4">
                        <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                          <div className="flex items-center gap-2">
                            <DocumentTextIcon className="w-5 h-5 text-indigo-600" />
                            <h4 className="text-sm font-bold text-gray-900">{msg.draft_data.title}</h4>
                          </div>
                          <span className="px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-bold">
                            {msg.draft_data.hours_worked || 0} Hours
                          </span>
                        </div>

                        {/* Section 1: Executive Summary */}
                        <div className="space-y-1">
                          <p className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                            1. Executive Summary
                          </p>
                          <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200/80 leading-relaxed">
                            {msg.draft_data.section_summary}
                          </p>
                        </div>

                        {/* Section 2: Deliverables Completed */}
                        <div className="space-y-1">
                          <p className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                            2. Deliverables Completed
                          </p>
                          <div className="space-y-1.5">
                            {msg.draft_data.section_deliverables?.map((item, idx) => (
                              <div
                                key={idx}
                                className="p-3 rounded-lg bg-gray-50 border border-gray-200/80 text-xs flex items-center justify-between"
                              >
                                <span className="font-semibold text-gray-900">{item.title}</span>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                  {item.status || 'COMPLETED'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Section 3: Next Steps & Priorities */}
                        <div className="space-y-1">
                          <p className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                            3. Next Steps & Blockers
                          </p>
                          <p className="text-xs text-gray-700 bg-gray-50 p-3.5 rounded-xl border border-gray-200/80 leading-relaxed">
                            {msg.draft_data.section_next_steps}
                          </p>
                        </div>

                        {/* Approve Draft Button */}
                        <div className="pt-2">
                          <button
                            onClick={() => handleApproveDraft(msg.draft_id)}
                            disabled={approving}
                            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50 active:scale-98"
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
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shadow-sm">
                  <SparklesIcon className="w-4 h-4 text-white animate-spin" />
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-2xl rounded-bl-none px-4 py-3 text-xs text-gray-600 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce"></span>
                  <span className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce [animation-delay:0.4s]"></span>
                  <span className="ml-1 font-medium">Querying Qdrant context & synthesizing...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick Action Suggestion Chips */}
          <div className="px-6 py-2 bg-gray-50 border-t border-gray-200 flex items-center gap-2 overflow-x-auto scrollbar-none">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider shrink-0">Quick Prompts:</span>
            {[
              'Draft my weekly progress report',
              'Summarize completed deliverables',
              'Log 8 hours on sprint tasks',
              'What requirements are pending?',
            ].map((prompt, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(prompt)}
                disabled={sending}
                className="px-3.5 py-1.5 rounded-full bg-white hover:bg-gray-100 text-gray-700 hover:text-gray-900 text-xs font-semibold whitespace-nowrap transition-colors border border-gray-200 shadow-2xs shrink-0"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Chat Input Bar */}
          <div className="p-4 bg-white border-t border-gray-200">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSendMessage()
              }}
              className="flex items-center gap-3"
            >
              <input
                type="text"
                placeholder="Describe your work, request changes, or ask the AI to draft a report..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={sending}
                className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || sending}
                className="p-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-xl shadow-md shadow-indigo-600/20 transition-all shrink-0 active:scale-95"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  )
}

export default FreelancerWorkPage
