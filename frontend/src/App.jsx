import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import FreelancerWorklogsPage from './pages/freelancer/FreelancerWorklogsPage'
import ClientReviewPage from './pages/client/ClientReviewPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/freelancer/worklogs" element={<FreelancerWorklogsPage />} />
      <Route path="/client/review" element={<ClientReviewPage />} />
    </Routes>
  )
}

export default App
