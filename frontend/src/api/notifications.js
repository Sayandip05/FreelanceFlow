import api from './axiosConfig'

export const notificationsAPI = {
  // Get all notifications
  getNotifications: (page = 1) =>
    api.get('/notifications/notifications/', { params: { page } }),

  // Get unread notifications
  getUnreadNotifications: () =>
    api.get('/notifications/notifications/unread/'),

  // Get unread count
  getUnreadCount: () =>
    api.get('/notifications/notifications/unread_count/'),

  // Get single notification
  getNotification: (id) =>
    api.get(`/notifications/notifications/${id}/`),

  // Mark notification as read
  markAsRead: (id) =>
    api.post(`/notifications/notifications/${id}/mark_read/`),

  // Mark all as read
  markAllAsRead: () =>
    api.post('/notifications/notifications/mark_all_read/'),

  // Delete notification
  deleteNotification: (id) =>
    api.delete(`/notifications/notifications/${id}/delete/`),
}

export default notificationsAPI
