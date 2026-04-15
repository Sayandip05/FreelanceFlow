import api from './axiosConfig'

export const authAPI = {
  // Register new user
  register: (email, password, role, firstName, lastName) =>
    api.post('/users/register/', {
      email,
      password,
      role,
      first_name: firstName,
      last_name: lastName
    }),

  // Login user
  login: (email, password) =>
    api.post('/users/login/', { email, password }),

  // Refresh token
  refreshToken: (refreshToken) =>
    api.post('/users/token/refresh/', { refresh: refreshToken }),

  // Get current user profile
  getProfile: () => api.get('/users/me/'),

  // Update profile
  updateProfile: (data) => api.patch('/users/me/', data),

  // Change password
  changePassword: (oldPassword, newPassword) =>
    api.post('/users/change-password/', {
      old_password: oldPassword,
      new_password: newPassword
    }),

  // Get user by ID
  getUser: (id) => api.get(`/users/${id}/`),

  // Logout (client-side only, clear tokens)
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return Promise.resolve()
  }
}

export default authAPI
