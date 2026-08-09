import api from './axiosConfig'

// Bid APIs
export const bidsAPI = {
  // Get all bids for user
  getBids: () => api.get('/bidding/bids/'),

  // Get user's bids
  getMyBids: () => api.get('/bidding/bids/my_bids/'),

  // Get single bid
  getBid: (id) => api.get(`/bidding/bids/${id}/`),

  // Submit bid (freelancer only)
  submitBid: (projectId, amount, coverLetter) =>
    api.post('/bidding/bids/', {
      project: projectId,
      amount: amount,
      cover_letter: coverLetter
    }),

  // Accept bid (client only)
  acceptBid: (bidId, milestoneData = {}) => 
    api.post(`/bidding/bids/${bidId}/accept/`, milestoneData),

  // Reject bid (client only)
  rejectBid: (bidId) => api.post(`/bidding/bids/${bidId}/reject/`),

  // Withdraw bid (freelancer only)
  withdrawBid: (bidId) => api.delete(`/bidding/bids/${bidId}/`),
}

// Contract APIs
export const contractsAPI = {
  // Get all contracts for user
  getContracts: () => api.get('/bidding/contracts/'),

  // Get single contract
  getContractDetail: (id) => api.get(`/bidding/contracts/${id}/`),

  // Accept proposed contract (freelancer only)
  acceptProposal: (contractId) => api.post(`/bidding/contracts/${contractId}/accept_proposal/`),

  // Decline proposed contract (freelancer only)
  declineProposal: (contractId) => api.post(`/bidding/contracts/${contractId}/decline_proposal/`),
}

export default { bidsAPI, contractsAPI }
