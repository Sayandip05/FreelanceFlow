import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, FileText, Briefcase, IndianRupee,
  MessageSquare, Clock, Send, CircleDot, Wifi, WifiOff,
  Loader2, X, ArrowDown, Check, CheckCheck
} from 'lucide-react'
import { messagesAPI } from '../../api/messages'
import { authAPI } from '../../api/auth'

const Avatar = ({ name, size = 'md' }) => {
  const initials = name ? name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() : '?'
  const s = size === 'sm' ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm'
  return (
    <div className={`${s} bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold flex-shrink-0 shadow-sm`}>
      {initials}
    </div>
  )
}

const formatChatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  const isYesterday = date.toDateString() === yesterday.toDateString()

  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  if (isYesterday) {
    return 'Yesterday'
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

const ClientMessagesPage = () => {
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [newMsg, setNewMsg] = useState('')
  const [loading, setLoading] = useState(true)
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [loadingEarlier, setLoadingEarlier] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [page, setPage] = useState(1)
  const [sending, setSending] = useState(false)
  const [search, setSearch] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const [otherUserOnline, setOtherUserOnline] = useState(false)
  const [showScrollBottom, setShowScrollBottom] = useState(false)
  const [typingUser, setTypingUser] = useState(null) // { full_name: string } | null

  const chatContainerRef = useRef(null)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)
  const isInitialScrollDone = useRef(false)
  const typingTimerRef = useRef(null)
  const typingSentRef = useRef(false)

  // Load all client conversations
  useEffect(() => {
    fetchConvs()
  }, [])

  const fetchConvs = async () => {
    try {
      const res = await messagesAPI.getConversations()
      const convs = res.data?.results || res.data || []
      setConversations(convs)
      if (convs.length > 0 && !selected) {
        setSelected(convs[0])
      }
    } catch (e) {
      console.error('Error fetching conversations:', e)
    } finally {
      setLoading(false)
    }
  }

  // Poll presence of selected user
  useEffect(() => {
    if (!selected) {
      setOtherUserOnline(false)
      return
    }
    
    const otherId = selected.other_user?.id || selected.contract?.freelancer?.id
    if (!otherId) return

    const checkPresence = async () => {
      try {
        const res = await authAPI.getUserPresence(otherId)
        setOtherUserOnline(res.data.is_online)
      } catch (err) {
        // silently fail
      }
    }

    checkPresence()
    const interval = setInterval(checkPresence, 20000)
    return () => clearInterval(interval)
  }, [selected])

  // Establish WebSocket connection when a chat is selected
  useEffect(() => {
    if (!selected) return

    setPage(1)
    setHasMore(true)
    setMessages([])
    isInitialScrollDone.current = false
    fetchInitialMessages(selected.id)

    // Connect WebSocket
    const contractId = selected.contract?.id || selected.id
    const wsUrl = messagesAPI.getChatWebSocketUrl(contractId)

    if (wsRef.current) {
      wsRef.current.close()
    }

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'read_receipt') {
          const readIds = new Set(data.message_ids || [])
          setMessages((prev) =>
            prev.map((m) => (readIds.size === 0 || readIds.has(m.id) ? { ...m, is_read: true } : m))
          )
          // Clear unread count in sidebar
          setConversations((prev) =>
            prev.map((c) => (c.id === selected.id ? { ...c, unread_count: 0 } : c))
          )
          return
        }

        if (data.type === 'typing_indicator') {
          if (data.is_typing) {
            setTypingUser({ full_name: data.full_name })
            clearTimeout(typingTimerRef.current)
            typingTimerRef.current = setTimeout(() => setTypingUser(null), 3000)
          } else {
            setTypingUser(null)
            clearTimeout(typingTimerRef.current)
          }
          return
        }

        if (data.type === 'chat_message' || (data.id && data.content)) {
          const incomingMsg = {
            id: data.id,
            content: data.content,
            sender: typeof data.sender === 'object' ? data.sender?.id : data.sender,
            created_at: data.created_at || new Date().toISOString(),
            is_read: data.is_read || false,
          }
          setMessages((prev) => {
            if (prev.some((m) => m.id === incomingMsg.id)) return prev
            return [...prev, incomingMsg]
          })

          // If incoming message is from the other user, emit read receipt back
          const otherId = selected.other_user?.id || selected.contract?.freelancer?.id
          const incomingSenderId = typeof incomingMsg.sender === 'object' && incomingMsg.sender !== null ? incomingMsg.sender.id : incomingMsg.sender
          if (incomingSenderId === otherId && ws.readyState === WebSocket.OPEN) {
            try {
              ws.send(JSON.stringify({ type: 'read_receipt' }))
            } catch {}
          }

          // Update conversation list item and sort to top
          setConversations((prev) => {
            const updated = prev.map((c) =>
              c.id === selected.id
                ? { ...c, last_message: { content: incomingMsg.content, created_at: incomingMsg.created_at } }
                : c
            )
            return [...updated].sort(
              (a, b) => new Date(b.last_message?.created_at || b.updated_at) - new Date(a.last_message?.created_at || a.updated_at)
            )
          })

          // Auto-scroll to bottom if near bottom
          setTimeout(() => {
            if (chatContainerRef.current) {
              const { scrollHeight, scrollTop, clientHeight } = chatContainerRef.current
              if (scrollHeight - scrollTop - clientHeight < 250) {
                scrollToBottom()
              }
            }
          }, 50)
        }
      } catch (err) {
        console.error('Error processing websocket message:', err)
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
    }

    ws.onerror = (err) => {
      console.warn('WebSocket connection warning:', err)
      setWsConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [selected?.id])

  const fetchInitialMessages = async (convId) => {
    setMessagesLoading(true)
    try {
      const res = await messagesAPI.getMessages(convId, { page: 1, page_size: 25 })
      const rawList = Array.isArray(res.data) ? res.data : (res.data?.results || [])
      // API returns newest first for pagination, reverse to chronological (oldest to newest)
      const chronological = [...rawList].reverse()
      setMessages(chronological)
      setHasMore(Boolean(res.data?.next))
      
      // Clear unread count locally instantly
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, unread_count: 0 } : c))
      )
      
      await messagesAPI.markAsRead(convId).catch(() => {})

      // Scroll to bottom on initial load
      setTimeout(() => {
        scrollToBottom('auto')
        isInitialScrollDone.current = true
      }, 50)
    } catch (e) {
      console.error('Error fetching initial messages:', e)
    } finally {
      setMessagesLoading(false)
    }
  }

  // Infinite scroll up: Load earlier page of messages
  const loadEarlierMessages = async () => {
    if (loadingEarlier || !hasMore || !selected) return
    setLoadingEarlier(true)

    const container = chatContainerRef.current
    const prevScrollHeight = container ? container.scrollHeight : 0
    const prevScrollTop = container ? container.scrollTop : 0
    const nextPage = page + 1

    try {
      const res = await messagesAPI.getMessages(selected.id, { page: nextPage, page_size: 25 })
      const rawList = Array.isArray(res.data) ? res.data : (res.data?.results || [])
      const olderChronological = [...rawList].reverse()

      if (olderChronological.length === 0) {
        setHasMore(false)
      } else {
        setMessages((prev) => {
          // Prepend unique older messages
          const existingIds = new Set(prev.map((m) => m.id))
          const newUnique = olderChronological.filter((m) => !existingIds.has(m.id))
          return [...newUnique, ...prev]
        })
        setPage(nextPage)
        setHasMore(Boolean(res.data?.next))

        // Retain user's current scroll position smoothly
        setTimeout(() => {
          if (container) {
            container.scrollTop = container.scrollHeight - prevScrollHeight + prevScrollTop
          }
        }, 10)
      }
    } catch (e) {
      console.error('Error loading earlier messages:', e)
      setHasMore(false)
    } finally {
      setLoadingEarlier(false)
    }
  }

  const handleChatScroll = () => {
    const container = chatContainerRef.current
    if (!container) return

    // Show/hide floating scroll-to-bottom button
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
    setShowScrollBottom(distanceFromBottom > 200)

    // Trigger loading earlier messages when scrolled near top
    if (container.scrollTop <= 40 && hasMore && !loadingEarlier && !messagesLoading && isInitialScrollDone.current) {
      loadEarlierMessages()
    }
  }

  const scrollToBottom = (behavior = 'smooth') => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior,
      })
    }
  }

  // Send typing indicator with debounce
  const sendTyping = (isTyping) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'typing', is_typing: isTyping }))
      } catch {}
    }
  }

  const handleInputChange = (e) => {
    setNewMsg(e.target.value)
    if (!typingSentRef.current) {
      typingSentRef.current = true
      sendTyping(true)
    }
    clearTimeout(typingTimerRef.current)
    typingTimerRef.current = setTimeout(() => {
      typingSentRef.current = false
      sendTyping(false)
    }, 2000)
  }

  const handleInputBlur = () => {
    clearTimeout(typingTimerRef.current)
    typingSentRef.current = false
    sendTyping(false)
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!newMsg.trim() || !selected) return
    const text = newMsg.trim()
    setNewMsg('')
    setSending(true)

    // Try WebSocket first
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ message: text }))
        setSending(false)
        setTimeout(() => scrollToBottom('smooth'), 50)
        return
      } catch (err) {
        console.warn('WebSocket send failed, falling back to REST:', err)
      }
    }

    // Fallback to HTTP API
    try {
      const res = await messagesAPI.sendMessage(selected.id, text)
      setMessages((prev) => [...prev, res.data])
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selected.id
            ? { ...c, last_message: { content: text, created_at: new Date().toISOString() } }
            : c
        )
      )
      setTimeout(() => scrollToBottom('smooth'), 50)
    } catch (e) {
      console.error('Error sending message:', e)
    } finally {
      setSending(false)
    }
  }

  const getOtherUserName = (conv) => {
    if (conv?.other_user?.first_name || conv?.other_user?.last_name) {
      return `${conv.other_user.first_name || ''} ${conv.other_user.last_name || ''}`.trim()
    }
    if (conv?.contract?.freelancer?.full_name) return conv.contract.freelancer.full_name
    if (conv?.contract?.freelancer?.email) return conv.contract.freelancer.email
    if (conv?.contract?.project?.title) return `Project: ${conv.contract.project.title}`
    return 'Freelancer'
  }

  const filtered = conversations.filter((c) => {
    const name = getOtherUserName(c)
    const projectTitle = c.contract?.project?.title || ''
    const lastContent = c.last_message?.content || ''
    const term = search.toLowerCase()
    return name.toLowerCase().includes(term) || projectTitle.toLowerCase().includes(term) || lastContent.toLowerCase().includes(term)
  })

  return (
    <div className="flex-1 flex h-full max-h-full overflow-hidden bg-white">
      {/* ── WhatsApp-style Left Sidebar (Only list scrolls) ─────────────────────────── */}
      <div className="w-80 md:w-88 lg:w-96 bg-white border-r border-gray-100 flex flex-col flex-shrink-0 h-full">
        {/* Fixed Top Header (Never scrolls) */}
        <div className="p-4 border-b border-gray-100 flex-shrink-0 bg-white z-10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold text-gray-900">Messages</h2>
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search conversations..."
              className="w-full pl-9 pr-8 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-gray-50/50 hover:bg-white focus:bg-white transition-colors"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-0.5 rounded-full"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Scrollable Conversation List Only */}
        <div className="flex-1 overflow-y-auto min-h-0 divide-y divide-gray-50 scrollbar-thin scrollbar-thumb-gray-200">
          {loading ? (
            <div className="p-4 space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-2">
                  <div className="w-10 h-10 bg-gray-100 rounded-full animate-pulse flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 bg-gray-100 rounded animate-pulse w-2/3" />
                    <div className="h-2.5 bg-gray-100 rounded animate-pulse w-full" />
                  </div>
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-16 text-center px-4">
              <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-3 text-gray-300">
                <MessageSquare className="w-6 h-6" />
              </div>
              <p className="text-sm font-medium text-gray-900 mb-1">
                {search ? 'No matches found' : 'No conversations yet'}
              </p>
              <p className="text-xs text-gray-400 max-w-xs mx-auto">
                {search
                  ? `No conversations matching "${search}"`
                  : 'Your freelancer communications will appear here.'}
              </p>
            </div>
          ) : (
            filtered.map((conv) => {
              const name = getOtherUserName(conv)
              const isSelected = selected?.id === conv.id
              const lastTime = formatChatTime(conv.last_message?.created_at || conv.updated_at)
              const unread = conv.unread_count || 0

              return (
                <button
                  key={conv.id}
                  onClick={() => setSelected(conv)}
                  className={`w-full flex items-center gap-3 px-4 py-3.5 hover:bg-gray-50/80 transition-all text-left group relative ${
                    isSelected ? 'bg-primary-50/70 border-l-4 border-primary-600' : 'border-l-4 border-transparent'
                  }`}
                >
                  <div className="relative flex-shrink-0">
                    <Avatar name={name} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <p className={`text-sm truncate ${isSelected ? 'font-bold text-primary-900' : 'font-medium text-gray-900 group-hover:text-primary-700'}`}>
                        {name || 'Freelancer'}
                      </p>
                      {lastTime && (
                        <span className="text-[11px] text-gray-400 flex-shrink-0 font-normal">
                          {lastTime}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs text-gray-500 truncate flex-1">
                        {conv.last_message?.content || 'Start conversation...'}
                      </p>
                      {unread > 0 && (
                        <span className="min-w-[18px] h-[18px] px-1.5 bg-emerald-500 text-white rounded-full text-[10px] font-bold flex items-center justify-center shadow-sm flex-shrink-0">
                          {unread}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* ── Main Chat Area ────────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col bg-slate-50/40 h-full min-w-0 relative">
        {!selected ? (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="text-center max-w-sm">
              <div className="w-16 h-16 bg-white shadow-sm border border-gray-100 rounded-3xl flex items-center justify-center mx-auto mb-4 text-primary-600">
                <MessageSquare className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-gray-900 mb-1">Your Direct Workplace Chat</h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                Select a freelancer conversation from the list to start messaging in real-time.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Chat Header (Fixed at top) */}
            <div className="px-6 py-3.5 bg-white border-b border-gray-100 flex items-center justify-between flex-shrink-0 shadow-sm z-10">
              <div className="flex items-center gap-3 min-w-0">
                <Avatar name={getOtherUserName(selected)} />
                <div className="min-w-0">
                  <p className="font-bold text-gray-900 text-sm truncate">{getOtherUserName(selected)}</p>
                </div>
              </div>
            </div>

            {/* Scrollable Message History with Page-in-set Infinite Scroll */}
            <div
              ref={chatContainerRef}
              onScroll={handleChatScroll}
              className="flex-1 overflow-y-auto p-6 space-y-3.5 min-h-0 scrollbar-thin scrollbar-thumb-gray-200 relative"
            >
              {/* Loading earlier messages spinner at top */}
              {loadingEarlier && (
                <div className="flex items-center justify-center py-2">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white shadow-sm border border-gray-100 text-xs text-gray-500 font-medium">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-primary-600" />
                    Loading earlier messages...
                  </div>
                </div>
              )}

              {/* Beginning of conversation badge */}
              {!hasMore && messages.length > 0 && (
                <div className="text-center py-3">
                  <span className="px-3 py-1 bg-gray-100/80 rounded-full text-[11px] font-medium text-gray-500">
                    Beginning of conversation
                  </span>
                </div>
              )}

              {messagesLoading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-16">
                  <div className="w-12 h-12 rounded-2xl bg-white border border-gray-100 shadow-sm flex items-center justify-center mx-auto mb-3 text-gray-400">
                    <MessageSquare className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-semibold text-gray-800 mb-1">No messages yet</p>
                  <p className="text-xs text-gray-400">Send a greeting below to begin collaborating!</p>
                </div>
              ) : (
                messages.map((msg, idx) => {
                  const otherId = selected.other_user?.id || selected.contract?.freelancer?.id
                  const senderId = typeof msg.sender === 'object' && msg.sender !== null ? msg.sender.id : msg.sender
                  const isMe = senderId !== otherId

                  return (
                    <div key={msg.id || idx} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                      <div
                        className={`max-w-xs sm:max-w-md lg:max-w-lg px-4 py-2.5 rounded-2xl text-sm shadow-sm transition-all ${
                          isMe
                            ? 'bg-primary-600 text-white rounded-br-sm'
                            : 'bg-white text-gray-900 border border-gray-100 rounded-bl-sm'
                        }`}
                      >
                        <p className="leading-relaxed whitespace-pre-wrap break-words">{msg.content}</p>
                        <div className={`flex items-center justify-end gap-1 mt-1 text-[10px] ${isMe ? 'text-primary-100' : 'text-gray-400'}`}>
                          <span>
                            {new Date(msg.created_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Floating Jump to Bottom Button */}
            {showScrollBottom && (
              <button
                onClick={() => scrollToBottom('smooth')}
                className="absolute right-6 bottom-20 p-2.5 bg-white text-gray-700 rounded-full shadow-lg border border-gray-100 hover:bg-gray-50 transition-all z-20"
                title="Jump to latest"
              >
                <ArrowDown className="w-4 h-4" />
              </button>
            )}

            {/* Fixed Bottom Input Form (Never overflows or causes outer scroll) */}
            <form onSubmit={handleSend} className="px-5 py-3 border-t border-gray-100 bg-white flex-shrink-0 z-10">
              {/* Typing indicator banner */}
              {typingUser && (
                <div className="flex items-center gap-2 mb-2 px-1">
                  <div className="flex gap-0.5 items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-xs text-gray-500 font-medium">{typingUser.full_name} is typing...</span>
                </div>
              )}
              <div className="flex gap-2.5 items-center">
                <input
                  value={newMsg}
                  onChange={handleInputChange}
                  onBlur={handleInputBlur}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-gray-50/50 hover:bg-white focus:bg-white transition-colors"
                />
                <button
                  type="submit"
                  disabled={sending || !newMsg.trim()}
                  className="w-10 h-10 bg-primary-600 text-white rounded-xl flex items-center justify-center hover:bg-primary-700 transition-colors disabled:opacity-40 flex-shrink-0 shadow-sm"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  )
}

export default ClientMessagesPage
