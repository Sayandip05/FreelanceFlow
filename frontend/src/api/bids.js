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
  submitBid: (arg1, amount, coverLetter) => {
    let payload = {}
    if (typeof arg1 === 'object' && arg1 !== null && ('project' in arg1 || 'amount' in arg1)) {
      payload = {
        project: typeof arg1.project === 'object' ? (arg1.project?.id || arg1.project?.pk) : parseInt(arg1.project, 10) || arg1.project,
        amount: arg1.amount,
        cover_letter: arg1.cover_letter || arg1.coverLetter
      }
    } else {
      const pId = typeof arg1 === 'object' && arg1 !== null ? (arg1.id || arg1.pk) : parseInt(arg1, 10) || arg1
      payload = {
        project: pId,
        amount: amount,
        cover_letter: coverLetter
      }
    }
    return api.post('/bidding/bids/', payload)
  },

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

  // Propose milestone schedule (client only)
  proposeMilestones: (contractId, milestones) => 
    api.post(`/bidding/contracts/${contractId}/propose_milestones/`, { milestones }),
}

// Review APIs
export const reviewsAPI = {
  // List reviews (given or received by current user)
  getReviews: () => api.get('/bidding/reviews/'),

  // Create a review for a completed contract
  createReview: (data) => api.post('/bidding/reviews/', data),

  // Get reviews received by current user
  getReceived: () => api.get('/bidding/reviews/received/'),

  // Get reviews given by current user
  getGiven: () => api.get('/bidding/reviews/given/'),

  // Get reviews for a specific user
  getUserReviews: (userId) => api.get(`/bidding/reviews/user/${userId}/`),

  // Get rating summary for a specific user
  getUserRatingSummary: (userId) => api.get(`/bidding/reviews/user/${userId}/summary/`),
}

export default { bidsAPI, contractsAPI }
