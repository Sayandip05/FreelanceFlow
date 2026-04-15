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

  // Get payment history summary
  getPaymentHistory: () => api.get('/payments/history/'),
}

export default paymentsAPI
