import api from './axiosConfig'

// WorkLog APIs
export const worklogAPI = {
  // Get all worklogs (optionally filtered by contract)
  getWorkLogs: (contractId = null) => {
    const params = contractId ? { contract: contractId } : {}
    return api.get('/worklogs/logs/', { params })
  },

  // Get single worklog
  getWorkLog: (id) => api.get(`/worklogs/logs/${id}/`),

  // Create worklog
  createWorkLog: (contractId, data) => 
    api.post('/worklogs/logs/', data, { params: { contract: contractId } }),

  // Update worklog
  updateWorkLog: (id, data) => api.patch(`/worklogs/logs/${id}/`, data),

  // Delete worklog
  deleteWorkLog: (id) => api.delete(`/worklogs/logs/${id}/`),
}

// Deliverable APIs (AI-powered worklog flow)
export const deliverableAPI = {
  // Get all deliverables
  getDeliverables: (contractId = null, status = null) => {
    const params = {}
    if (contractId) params.contract = contractId
    if (status) params.status = status
    return api.get('/worklogs/deliverables/', { params })
  },

  // Get single deliverable
  getDeliverableDetail: (id) => api.get(`/worklogs/deliverables/${id}/`),

  // Create deliverable from AI chat
  createDeliverable: (contractId, data) =>
    api.post('/worklogs/deliverables/', data, { params: { contract: contractId } }),

  // Update deliverable draft
  updateDeliverable: (id, data) => api.patch(`/worklogs/deliverables/${id}/`, data),

  // Submit deliverable for review
  submitDeliverable: (id) => api.post(`/worklogs/deliverables/${id}/submit/`),

  // Approve deliverable (client only)
  approveDeliverable: (id, feedback = '') =>
    api.post(`/worklogs/deliverables/${id}/approve/`, { action: 'approve', feedback }),

  // Reject deliverable (client only)
  rejectDeliverable: (id, feedback, requestRevision = true) =>
    api.post(`/worklogs/deliverables/${id}/reject/`, { 
      action: requestRevision ? 'request_revision' : 'reject', 
      feedback 
    }),
}

// AI Chat APIs
export const aiChatAPI = {
  // Send message to AI
  sendMessage: (contractId, message, chatHistory = []) =>
    api.post('/worklogs/ai-chat/message/', 
      { message, chat_history: chatHistory },
      { params: { contract: contractId } }
    ),

  // Generate deliverable from chat
  generateDeliverable: (contractId, chatTranscript, attachedFiles = []) =>
    api.post('/worklogs/ai-chat/generate-deliverable/', 
      { chat_transcript: chatTranscript, attached_files: attachedFiles },
      { params: { contract: contractId } }
    ),
}

// File Upload APIs
export const uploadAPI = {
  // Upload file (screenshot, attachment)
  uploadFile: (file, description = '') => {
    const formData = new FormData()
    formData.append('file', file)
    if (description) formData.append('description', description)
    
    return api.post('/worklogs/upload/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// Weekly Report APIs
export const reportAPI = {
  // Get all reports
  getReports: (contractId = null) => {
    const params = contractId ? { contract: contractId } : {}
    return api.get('/worklogs/reports/', { params })
  },

  // Get single report
  getReport: (id) => api.get(`/worklogs/reports/${id}/`),
}

// Delivery Proof APIs
export const proofAPI = {
  // Get delivery proof for contract
  getProof: (contractId) => api.get(`/worklogs/proofs/${contractId}/`),

  // Generate delivery proof
  generateProof: (contractId) => api.post(`/worklogs/proofs/${contractId}/`),
}
