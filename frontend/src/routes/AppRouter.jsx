import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { NotificationProvider } from '../context/NotificationContext'
import ClientRoute from './ClientRoute'
import FreelancerRoute from './FreelancerRoute'
import FreelancerLayout from '../components/layout/FreelancerLayout'
import ClientLayout from '../components/layout/ClientLayout'

// Auth Pages
import AuthPage from '../pages/auth/AuthPage'
import GoogleCallbackPage from '../pages/auth/GoogleCallbackPage'

// Shared Pages
import LandingPage from '../pages/LandingPage'

// Client Pages
import ClientOverviewPage from '../pages/client/ClientOverviewPage'
import ClientHomePage from '../pages/client/ClientHomePage'
import ClientOnboardingPage from '../pages/client/ClientOnboardingPage'
import ClientProjectsPage from '../pages/client/ClientProjectsPage'
import ClientProjectDetailPage from '../pages/client/ClientProjectDetailPage'
import ClientContractsPage from '../pages/client/ClientContractsPage'
import ClientContractDetailPage from '../pages/client/ClientContractDetailPage'
import ClientDeliverableReviewPage from '../pages/client/ClientDeliverableReviewPage'
import ClientPaymentsPage from '../pages/client/ClientPaymentsPage'
import ClientMessagesPage from '../pages/client/ClientMessagesPage'
import ClientReviewPage from '../pages/client/ClientReviewPage'

// Freelancer Pages
import FreelancerOnboardingPage from '../pages/freelancer/FreelancerOnboardingPage'
import FreelancerOverviewPage from '../pages/freelancer/FreelancerOverviewPage'
import FreelancerBrowsePage from '../pages/freelancer/FreelancerBrowsePage'
import FreelancerProjectDetailPage from '../pages/freelancer/FreelancerProjectDetailPage'
import FreelancerBidsPage from '../pages/freelancer/FreelancerBidsPage'
import FreelancerContractsPage from '../pages/freelancer/FreelancerContractsPage'
import FreelancerContractDetailPage from '../pages/freelancer/FreelancerContractDetailPage'
import FreelancerWorkPage from '../pages/freelancer/FreelancerWorkPage'
import FreelancerWorklogsPage from '../pages/freelancer/FreelancerWorklogsPage'
import FreelancerEarningsPage from '../pages/freelancer/FreelancerEarningsPage'
import FreelancerMessagesPage from '../pages/freelancer/FreelancerMessagesPage'

const AppRouter = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<AuthPage />} />
            <Route path="/register" element={<AuthPage />} />
            <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />

            {/* Client Routes */}
            <Route path="/client" element={<ClientRoute />}>
              <Route path="onboarding" element={<ClientOnboardingPage />} />
              <Route element={<ClientLayout />}>
                <Route index element={<Navigate to="/client/home" replace />} />
                <Route path="home" element={<ClientHomePage />} />
                <Route path="dashboard" element={<ClientOverviewPage />} />
                <Route path="projects" element={<ClientProjectsPage />} />
                <Route path="projects/:projectId" element={<ClientProjectDetailPage />} />
                <Route path="contracts" element={<ClientContractsPage />} />
                <Route path="contracts/:contractId" element={<ClientContractDetailPage />} />
                <Route path="deliverables/:deliverableId/review" element={<ClientDeliverableReviewPage />} />
                <Route path="payments" element={<ClientPaymentsPage />} />
                <Route path="messages" element={<ClientMessagesPage />} />
                <Route path="reviews" element={<ClientReviewPage />} />
              </Route>
            </Route>

            {/* Freelancer Routes */}
            <Route path="/freelancer" element={<FreelancerRoute />}>
              <Route path="onboarding" element={<FreelancerOnboardingPage />} />
              <Route element={<FreelancerLayout />}>
                <Route index element={<Navigate to="/freelancer/browse" replace />} />
                <Route path="dashboard" element={<FreelancerOverviewPage />} />
                <Route path="browse" element={<FreelancerBrowsePage />} />
                <Route path="projects/:projectId" element={<FreelancerProjectDetailPage />} />
                <Route path="bids" element={<FreelancerBidsPage />} />
                <Route path="contracts" element={<FreelancerContractsPage />} />
                <Route path="contracts/:contractId" element={<FreelancerContractDetailPage />} />
                <Route path="contracts/:contractId/work" element={<FreelancerWorkPage />} />
                <Route path="worklogs" element={<FreelancerWorklogsPage />} />
                <Route path="worklogs/:contractId" element={<FreelancerWorkPage />} />
                <Route path="earnings" element={<FreelancerEarningsPage />} />
                <Route path="messages" element={<FreelancerMessagesPage />} />
              </Route>
            </Route>

            {/* 404 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default AppRouter
