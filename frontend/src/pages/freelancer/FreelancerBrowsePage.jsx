import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Search, FileText, Briefcase, DollarSign,
  MessageSquare, Clock, Filter, ChevronDown, Tag, ArrowRight
} from 'lucide-react'
import { projectsAPI } from '../../api/projects'
import { bidsAPI } from '../../api/bids'

const Sidebar = ({ active }) => {
  const navigate = useNavigate()
  const links = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/freelancer/dashboard' },
    { icon: Search, label: 'Browse Projects', path: '/freelancer/browse' },
    { icon: FileText, label: 'My Bids', path: '/freelancer/bids' },
    { icon: Briefcase, label: 'Contracts', path: '/freelancer/contracts' },
    { icon: Clock, label: 'Work Logs', path: '/freelancer/worklogs' },
    { icon: DollarSign, label: 'Earnings', path: '/freelancer/earnings' },
    { icon: MessageSquare, label: 'Messages', path: '/freelancer/messages' },
  ]
  return (
    <aside className="w-64 bg-white border-r border-gray-100 min-h-screen flex-shrink-0">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-gray-900">FreelanceFlow</span>
        </div>
      </div>
      <nav className="p-4 space-y-1">
        {links.map((link) => (
          <button key={link.path} onClick={() => navigate(link.path)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
              active === link.path ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}>
            <link.icon className="w-5 h-5" />{link.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}

const BidModal = ({ project, onClose, onBidSubmitted }) => {
  const [form, setForm] = useState({ amount: '', cover_letter: '', delivery_days: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await bidsAPI.submitBid(project.id, parseFloat(form.amount), form.cover_letter)
      onBidSubmitted()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit bid. You may have already bid on this project.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-xl">
        <h2 className="text-xl font-bold text-gray-900 mb-1">Submit a Bid</h2>
        <p className="text-sm text-gray-500 mb-5">{project.title}</p>
        {error && <p className="text-sm text-red-600 mb-4 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Your Bid Amount (USD)</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <input type="number" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} required min="1"
                placeholder={project.budget} className="w-full pl-7 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
            </div>
            <p className="text-xs text-gray-400 mt-1">Client budget: ${project.budget}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cover Letter</label>
            <textarea value={form.cover_letter} onChange={e => setForm({...form, cover_letter: e.target.value})} required rows={4}
              placeholder="Explain why you're the best fit for this project..."
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm resize-none" />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 disabled:opacity-60">
              {loading ? 'Submitting...' : 'Submit Bid'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

const FreelancerBrowsePage = () => {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [budgetFilter, setBudgetFilter] = useState('')
  const [selectedProject, setSelectedProject] = useState(null)
  const [biddedProjects, setBiddedProjects] = useState(new Set())

  useEffect(() => {
    fetchProjects()
  }, [search, budgetFilter])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const filters = {}
      if (search) filters.search = search
      if (budgetFilter === 'low') { filters.budget_min = 0; filters.budget_max = 500 }
      else if (budgetFilter === 'mid') { filters.budget_min = 500; filters.budget_max = 2000 }
      else if (budgetFilter === 'high') { filters.budget_min = 2000 }
      const res = await projectsAPI.getProjects(filters)
      setProjects(res.data?.results || res.data || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchProjects()
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active="/freelancer/browse" />
      {selectedProject && (
        <BidModal
          project={selectedProject}
          onClose={() => setSelectedProject(null)}
          onBidSubmitted={() => {
            setBiddedProjects(prev => new Set([...prev, selectedProject.id]))
            setSelectedProject(null)
          }}
        />
      )}
      <div className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Browse Projects</h1>
          <p className="text-gray-600 mt-1">Find your next opportunity</p>
        </div>

        {/* Search & Filters */}
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search projects by title or skill..."
              className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
          </div>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select value={budgetFilter} onChange={e => setBudgetFilter(e.target.value)}
              className="pl-9 pr-8 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white appearance-none">
              <option value="">Any Budget</option>
              <option value="low">Under $500</option>
              <option value="mid">$500 – $2,000</option>
              <option value="high">$2,000+</option>
            </select>
          </div>
          <button type="submit" className="btn-primary px-5">Search</button>
        </form>

        {/* Results */}
        {loading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => <div key={i} className="h-32 bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-gray-100">
            <Search className="w-14 h-14 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No projects found</h3>
            <p className="text-gray-500">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">{projects.length} project{projects.length !== 1 ? 's' : ''} found</p>
            {projects.map(project => (
              <div key={project.id} className="bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-lg mb-1">{project.title}</h3>
                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">{project.description}</p>
                    {project.required_skills?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {project.required_skills.map((skill, i) => (
                          <span key={i} className="px-2.5 py-0.5 bg-primary-50 text-primary-700 text-xs rounded-full font-medium">{skill}</span>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {new Date(project.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xl font-bold text-gray-900 mb-1">${project.budget?.toLocaleString()}</p>
                    <p className="text-xs text-gray-400 mb-3">Fixed Budget</p>
                    {biddedProjects.has(project.id) ? (
                      <span className="text-sm text-green-600 font-medium flex items-center gap-1">
                        ✓ Bid Submitted
                      </span>
                    ) : (
                      <button onClick={() => setSelectedProject(project)} className="btn-primary text-sm px-4 py-2">
                        Place Bid
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default FreelancerBrowsePage
