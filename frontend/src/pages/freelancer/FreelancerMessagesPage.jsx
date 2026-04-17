import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Search, FileText, Briefcase, DollarSign,
  MessageSquare, Clock, Send, CircleDot
} from 'lucide-react'
import { messagesAPI } from '../../api/messages'

const Sidebar = ({ active }) => {
  const navigate = useNavigate()
  const links = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/freelancer/dashboard' },
    { icon: Search, label: 'Browse Projects', path: '/freelancer/browse' },
    { icon: FileText, label: 'My Bids', path: '/freelancer/bids' },
    { icon: Briefcase, label: 'Contracts', path: '/freelancer/contracts' },
    { icon: Clock, label: 'Work Logs', path: '/freelancer/worklogs' },
    { icon: DollarSign, label: 'Earnings', path: '/freelancer/earnings' },
    { icon: MessageSquare, label: 'Messages', path: '/freelancer/messages' },
  ]
  return (
    <aside className="w-64 bg-white border-r border-gray-100 min-h-screen flex-shrink-0">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-gray-900">FreelanceFlow</span>
        </div>
      </div>
      <nav className="p-4 space-y-1">
        {links.map((link) => (
          <button key={link.path} onClick={() => navigate(link.path)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
              active === link.path ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}>
            <link.icon className="w-5 h-5" />{link.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}

const Avatar = ({ name, size = 'md' }) => {
  const initials = name ? name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : '?'
  const s = size === 'sm' ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm'
  return (
    <div className={`${s} bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold flex-shrink-0`}>
      {initials}
    </div>
  )
}

const FreelancerMessagesPage = () => {
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [newMsg, setNewMsg] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [search, setSearch] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    const fetchConvs = async () => {
      try {
        const res = await messagesAPI.getConversations()
        const convs = res.data?.results || res.data || []
        setConversations(convs)
        if (convs.length > 0) setSelected(convs[0])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchConvs()
  }, [])

  useEffect(() => {
    if (selected) fetchMessages()
  }, [selected])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchMessages = async () => {
    try {
      const res = await messagesAPI.getMessages(selected.id)
      setMessages(res.data?.results || res.data || [])
      await messagesAPI.markAsRead(selected.id).catch(() => {})
    } catch (e) {
      console.error(e)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!newMsg.trim() || !selected) return
    setSending(true)
    try {
      const res = await messagesAPI.sendMessage(selected.id, newMsg.trim())
      setMessages(prev => [...prev, res.data])
      setNewMsg('')
    } catch (e) {
      console.error(e)
    } finally {
      setSending(false)
    }
  }

  const filtered = conversations.filter(c =>
    (c.other_user?.first_name + ' ' + c.other_user?.last_name)
      .toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active="/freelancer/messages" />
      <div className="flex-1 flex overflow-hidden" style={{ height: '100vh' }}>
        {/* Conversations */}
        <div className="w-80 bg-white border-r border-gray-100 flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-3">Messages</h2>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..."
                className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 space-y-3">
                {[...Array(4)].map((_, i) => <div key={i} className="h-14 bg-gray-100 rounded-xl animate-pulse" />)}
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-16 text-center px-4">
                <MessageSquare className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No conversations yet</p>
              </div>
            ) : (
              filtered.map((conv) => {
                const name = `${conv.other_user?.first_name || ''} ${conv.other_user?.last_name || ''}`.trim()
                return (
                  <button key={conv.id} onClick={() => setSelected(conv)}
                    className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 border-b border-gray-50 text-left ${selected?.id === conv.id ? 'bg-primary-50' : ''}`}>
                    <div className="relative">
                      <Avatar name={name} />
                      {conv.has_unread && (
                        <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-primary-600 rounded-full border-2 border-white" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{name || 'Unknown'}</p>
                      <p className="text-xs text-gray-500 truncate">{conv.last_message?.content || 'No messages yet'}</p>
                    </div>
                  </button>
                )
              })
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-white">
          {!selected ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="w-14 h-14 text-gray-200 mx-auto mb-3" />
                <p className="text-gray-500">Select a conversation to start messaging</p>
              </div>
            </div>
          ) : (
            <>
              <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
                <Avatar name={`${selected.other_user?.first_name} ${selected.other_user?.last_name}`} />
                <div>
                  <p className="font-semibold text-gray-900">
                    {selected.other_user?.first_name} {selected.other_user?.last_name}
                  </p>
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <CircleDot className="w-3 h-3 text-green-500" /> Client
                  </p>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-10">
                    <p className="text-gray-400 text-sm">No messages yet. Say hello!</p>
                  </div>
                ) : (
                  messages.map((msg) => {
                    const isMe = msg.sender !== selected.other_user?.id
                    return (
                      <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2.5 rounded-2xl text-sm ${
                          isMe ? 'bg-primary-600 text-white rounded-br-sm' : 'bg-gray-100 text-gray-900 rounded-bl-sm'
                        }`}>
                          {msg.content}
                          <p className={`text-xs mt-1 ${isMe ? 'text-primary-200' : 'text-gray-400'}`}>
                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                    )
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={handleSend} className="px-6 py-4 border-t border-gray-100">
                <div className="flex gap-3">
                  <input value={newMsg} onChange={e => setNewMsg(e.target.value)} placeholder="Type a message..."
                    className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
                  <button type="submit" disabled={sending || !newMsg.trim()}
                    className="w-10 h-10 bg-primary-600 text-white rounded-xl flex items-center justify-center hover:bg-primary-700 transition-colors disabled:opacity-50">
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default FreelancerMessagesPage
