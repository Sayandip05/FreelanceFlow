import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import GoogleCallbackPage from './pages/auth/GoogleCallbackPage'
import FreelancerWorklogsPage from './pages/freelancer/FreelancerWorklogsPage'
import FreelancerWorkPage from './pages/freelancer/FreelancerWorkPage'
import ClientReviewPage from './pages/client/ClientReviewPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
      <Route path="/freelancer/worklogs" element={<FreelancerWorklogsPage />} />
      <Route path="/freelancer/work/:contractId" element={<FreelancerWorkPage />} />
      <Route path="/freelancer/worklogs/:contractId" element={<FreelancerWorkPage />} />
      <Route path="/client/review" element={<ClientReviewPage />} />
    </Routes>
  )
}

export default App
