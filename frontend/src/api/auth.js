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

  // Update user avatar
  updateAvatar: (avatarUrl) =>
    api.post('/users/avatar/', { avatar_url: avatarUrl }),

  uploadImage: (imageFile, imageType = 'avatar', onUploadProgress = null) => {
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('image_type', imageType)
    return api.post('/users/upload-image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    })
  },

  // Get user by ID
  getUser: (id) => api.get(`/users/${id}/`),

  // Logout (client-side only, clear tokens)
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return Promise.resolve()
  }
}

export const usersAPI = authAPI
export default authAPI
