import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, FileText, CreditCard, MessageSquare, Star,
  TrendingUp, Clock, CheckCircle, AlertCircle, Plus, ArrowRight, Wallet
} from 'lucide-react'
import { projectsAPI } from '../../api/projects'
import { paymentsAPI } from '../../api/payments'
import { DashboardSkeleton } from '../../components/common/Skeleton'

const StatCard = ({ icon: Icon, label, value, color, bg }) => (
  <div className="bg-white rounded-2xl border border-gray-100 p-6 flex items-center gap-4">
    <div className={`w-12 h-12 ${bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
      <Icon className={`w-6 h-6 ${color}`} />
    </div>
    <div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  </div>
)

const ClientOverviewPage = () => {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projRes, payRes] = await Promise.allSettled([
          projectsAPI.getMyProjects(),
          paymentsAPI.getPayments(),
        ])
        if (projRes.status === 'fulfilled') setProjects(projRes.value.data?.results || projRes.value.data || [])
        if (payRes.status === 'fulfilled') setPayments(payRes.value.data?.results || payRes.value.data || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const activeProjects = projects.filter(p => p.status === 'OPEN' || p.status === 'IN_PROGRESS')
  const totalSpent = payments.filter(p => p.status === 'RELEASED').reduce((s, p) => s + parseFloat(p.total_amount || 0), 0)
  const pendingPayments = payments.filter(p => p.status === 'ESCROWED').length

  const recentProjects = projects.slice(0, 4)

  if (loading) {
    return (
      <div className="flex-1 p-8">
        <DashboardSkeleton />
      </div>
    )
  }

  return (
          
      <div className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Client Dashboard</h1>
            <p className="text-gray-600 mt-1">Manage your projects and track progress</p>
          </div>
          <button
            onClick={() => navigate('/client/projects')}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Project
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Briefcase} label="Active Projects" value={loading ? '—' : activeProjects.length} color="text-primary-600" bg="bg-primary-50" />
          <StatCard icon={FileText} label="Total Projects" value={loading ? '—' : projects.length} color="text-indigo-600" bg="bg-indigo-50" />
          <StatCard icon={Wallet} label="Total Spent" value={loading ? '—' : `$${totalSpent.toLocaleString()}`} color="text-accent-600" bg="bg-green-50" />
          <StatCard icon={Clock} label="Pending Payments" value={loading ? '—' : pendingPayments} color="text-yellow-600" bg="bg-yellow-50" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Projects */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-gray-900">Recent Projects</h2>
              <button
                onClick={() => navigate('/client/projects')}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : recentProjects.length === 0 ? (
              <div className="text-center py-12">
                <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No projects yet</p>
                <button onClick={() => navigate('/client/projects')} className="btn-primary text-sm">
                  Post Your First Project
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {recentProjects.map((project) => (
                  <div
                    key={project.id}
                    onClick={() => navigate(`/client/projects/${project.id}`)}
                    className="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div>
                      <p className="font-medium text-gray-900">{project.title}</p>
                      <p className="text-sm text-gray-500">Budget: ${project.budget}</p>
                    </div>
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                      project.status === 'OPEN' ? 'bg-green-100 text-green-700' :
                      project.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {project.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="space-y-4">
            <div className="bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl p-6 text-white">
              <TrendingUp className="w-8 h-8 mb-3 opacity-80" />
              <h3 className="font-semibold text-lg mb-1">Find Top Talent</h3>
              <p className="text-primary-100 text-sm mb-4">Post a project and receive bids from skilled freelancers.</p>
              <button
                onClick={() => navigate('/client/projects')}
                className="bg-white text-primary-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-primary-50 transition-colors w-full"
              >
                Post a Project
              </button>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
              <div className="space-y-2">
                {[
                  { icon: CreditCard, label: 'View Payments', path: '/client/payments', color: 'text-green-600' },
                  { icon: MessageSquare, label: 'My Messages', path: '/client/messages', color: 'text-blue-600' },
                  { icon: Star, label: 'Leave a Review', path: '/client/reviews', color: 'text-yellow-600' },
                ].map((item) => (
                  <button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors"
                  >
                    <item.icon className={`w-5 h-5 ${item.color}`} />
                    <span className="text-sm text-gray-700">{item.label}</span>
                    <ArrowRight className="w-4 h-4 text-gray-400 ml-auto" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
  )
}

export default ClientOverviewPage
