import api from './axiosConfig'

export const paymentsAPI = {
  // Get all payments for user
  getPayments: () => api.get('/payments/'),

  // Get single payment
  getPayment: (id) => api.get(`/payments/${id}/`),

  // Get payment by contract
  getPaymentByContract: (contractId) => 
    api.get('/payments/', { params: { contract: contractId } })
      .then(res => res.data.results?.[0] || res.data[0]),

  // Create escrow (client only)
  createEscrow: (contractId) =>
    api.post('/payments/escrow/', { contract_id: contractId }),

  // Verify Razorpay payment
  verifyPayment: (data) =>
    api.post('/payments/verify/', data),

  // Release payment (client only)
  releasePayment: (contractId) =>
    api.post('/payments/release/', { contract_id: contractId }),

  // Milestone APIs
  getMilestones: (contractId) =>
    api.get(`/payments/milestones/${contractId}/milestones/`),

  createMilestone: (contractId, data) =>
    api.post(`/payments/milestones/${contractId}/milestones/`, data),

  clearMilestones: (contractId) =>
    api.post(`/payments/milestones/${contractId}/clear/`),

  completeMilestone: (milestoneId, data = {}) =>
    api.post(`/payments/milestones/${milestoneId}/complete/`, data),

  fundMilestone: (milestoneId) =>
    api.post(`/payments/milestones/${milestoneId}/fund/`),

  releaseMilestone: (milestoneId) =>
    api.post(`/payments/milestones/${milestoneId}/release/`),

  getMilestoneProgress: (contractId) =>
    api.get(`/payments/milestones/${contractId}/milestone-progress/`),

  // Dispute APIs
  raiseDispute: (contractId, reason, description) =>
    api.post('/payments/disputes/', { contract_id: contractId, reason, description }),

  // Termination APIs
  terminateContract: (contractId, reason, explanation) =>
    api.post(`/bidding/contracts/${contractId}/terminate/`, { reason, explanation }),
}

export default paymentsAPI
