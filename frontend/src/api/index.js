// Central API exports
export { authAPI } from './auth'
export { projectsAPI } from './projects'
export { bidsAPI, contractsAPI } from './bids'
export { paymentsAPI } from './payments'
export { worklogAPI, deliverableAPI, aiChatAPI, uploadAPI, reportAPI, proofAPI } from './worklogs'
export { messagesAPI } from './messages'
export { notificationsAPI } from './notifications'
export { searchAPI } from './search'

// Default export with all APIs
import { authAPI } from './auth'
import { projectsAPI } from './projects'
import { bidsAPI, contractsAPI } from './bids'
import { paymentsAPI } from './payments'
import { worklogAPI, deliverableAPI, aiChatAPI, uploadAPI, reportAPI, proofAPI } from './worklogs'
import { messagesAPI } from './messages'
import { notificationsAPI } from './notifications'
import { searchAPI } from './search'

export default {
  auth: authAPI,
  projects: projectsAPI,
  bids: bidsAPI,
  contracts: contractsAPI,
  payments: paymentsAPI,
  worklogs: worklogAPI,
  deliverables: deliverableAPI,
  aiChat: aiChatAPI,
  upload: uploadAPI,
  reports: reportAPI,
  proofs: proofAPI,
  messages: messagesAPI,
  notifications: notificationsAPI,
  search: searchAPI,
}
