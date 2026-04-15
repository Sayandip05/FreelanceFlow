import api from './axiosConfig'

export const messagesAPI = {
  // Get all conversations
  getConversations: () => api.get('/messaging/conversations/'),

  // Get single conversation
  getConversation: (id) => api.get(`/messaging/conversations/${id}/`),

  // Get messages for a conversation
  getMessages: (conversationId) =>
    api.get(`/messaging/conversations/${conversationId}/messages/`),

  // Send message
  sendMessage: (conversationId, content) =>
    api.post(`/messaging/conversations/${conversationId}/send/`, { content }),

  // Mark messages as read
  markAsRead: (conversationId) =>
    api.post(`/messaging/conversations/${conversationId}/mark_read/`),
}

export default messagesAPI
