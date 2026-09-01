import api from './axiosConfig'

export const messagesAPI = {
  // Get all conversations
  getConversations: () => api.get('/messaging/conversations/'),

  // Get single conversation
  getConversation: (id) => api.get(`/messaging/conversations/${id}/`),

  // Get messages for a conversation with pagination
  getMessages: (conversationId, params = {}) =>
    api.get(`/messaging/conversations/${conversationId}/messages/`, { params }),

  // Send message
  sendMessage: (conversationId, content) =>
    api.post(`/messaging/conversations/${conversationId}/send/`, { content }),

  // Mark messages as read
  markAsRead: (conversationId) =>
    api.post(`/messaging/conversations/${conversationId}/mark_read/`),

  // Build WebSocket URL for contract chat
  getChatWebSocketUrl: (contractId) => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || ''
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
    
    try {
      const urlObj = new URL(apiUrl)
      const protocol = urlObj.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${urlObj.host}/ws/chat/${contractId}/?token=${token}`
    } catch (e) {
      // Fallback if URL parsing fails
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
      return `${protocol}//${host}/ws/chat/${contractId}/?token=${token}`
    }
  },
}

export default messagesAPI
