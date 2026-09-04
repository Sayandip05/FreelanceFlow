import api from './axiosConfig'

export const authAPI = {
  // Register new user (legacy direct)
  register: (email, password, role, firstName, lastName) =>
    api.post('/users/register/', {
      email,
      password,
      role,
      first_name: firstName,
      last_name: lastName
    }),

  // OTP Registration
  initiateRegisterOtp: (email, password, role, firstName, lastName) =>
    api.post('/users/register/otp/', {
      email,
      password,
      role,
      first_name: firstName,
      last_name: lastName,
    }),

  verifyRegisterOtp: (email, otp) =>
    api.post('/users/register/verify-otp/', { email, otp }),

  resendRegisterOtp: (email) =>
    api.post('/users/register/resend-otp/', { email }),

  // OTP Password Reset
  initiatePasswordResetOtp: (email) =>
    api.post('/users/password-reset/otp/', { email }),

  verifyPasswordResetOtp: (email, otp, newPassword) =>
    api.post('/users/password-reset/verify-otp/', {
      email,
      otp,
      new_password: newPassword,
    }),

  resendPasswordResetOtp: (email) =>
    api.post('/users/password-reset/resend-otp/', { email }),

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

  uploadImage: async (imageFile, imageType = 'avatar', onUploadProgress = null) => {
    // 1. Get SAS token from backend
    const tokenRes = await api.post('/users/sas-token/', {
      image_type: imageType,
      filename: imageFile.name,
    })

    const { upload_url, public_url } = tokenRes.data

    // 2. Direct Cloud Upload: PUT directly to Azure Blob Storage
    const axios = (await import('axios')).default
    await axios.put(upload_url, imageFile, {
      headers: {
        'Content-Type': imageFile.type || 'image/jpeg',
        'x-ms-blob-type': 'BlockBlob',
      },
      onUploadProgress,
    })

    // 3. Update profile with the Azure public URL
    let userRes
    if (imageType === 'avatar') {
      userRes = await api.post('/users/avatar/', { avatar_url: public_url })
    } else {
      userRes = await api.post('/users/banner/', { banner_url: public_url })
    }

    return {
      data: {
        url: public_url,
        user: userRes?.data?.user,
      },
    }
  },

  // Get user by ID
  getUser: (id) => api.get(`/users/${id}/`),

  // Get user presence status (online/offline)
  getUserPresence: (id) => api.get(`/users/${id}/presence/`),

  // Link payout account for freelancer bank details
  linkPayoutAccount: (data) =>
    api.post('/users/freelancer/payout-account/', data),

  // Logout (client-side only, clear tokens)
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return Promise.resolve()
  }
}

export const usersAPI = authAPI
export default authAPI
