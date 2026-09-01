import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, FileText, CreditCard, MessageSquare, Star,
  Search, Plus, Filter, ChevronDown, ExternalLink, Trash2, AlertTriangle, Loader2
} from 'lucide-react'
import { projectsAPI } from '../../api/projects'

const STATUS_COLORS = {
  OPEN: 'bg-green-100 text-green-700',
  IN_PROGRESS: 'bg-blue-100 text-blue-700',
  COMPLETED: 'bg-gray-100 text-gray-600',
  CANCELLED: 'bg-red-100 text-red-600',
}

const CreateProjectModal = ({ onClose, onCreated }) => {
  const [form, setForm] = useState({ title: '', description: '', budget: '', approx_duration: '', skills: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await projectsAPI.createProject({
        title: form.title,
        description: form.description,
        budget: parseFloat(form.budget),
        approx_duration: form.approx_duration,
        required_skills: form.skills.split(',').map(s => s.trim()).filter(Boolean),
      })
      onCreated(res.data)
    } catch (err) {
      setError('Failed to create project. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-xl">
        <h2 className="text-xl font-bold text-gray-900 mb-5">Post a New Project</h2>
        {error && <p className="text-sm text-red-600 mb-4 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Title</label>
            <input value={form.title} onChange={e => setForm({...form, title: e.target.value})} required placeholder="e.g. Build a React Dashboard"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} required rows={3} placeholder="Describe what you need..."
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm resize-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Budget (USD)</label>
            <input type="number" value={form.budget} onChange={e => setForm({...form, budget: e.target.value})} required min="1" placeholder="500"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Approximate Duration</label>
            <input value={form.approx_duration} onChange={e => setForm({...form, approx_duration: e.target.value})} required placeholder="e.g. 1-2 months, 3 weeks"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Required Skills (comma-separated)</label>
            <input value={form.skills} onChange={e => setForm({...form, skills: e.target.value})} placeholder="React, Node.js, PostgreSQL"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 disabled:opacity-60">
              {loading ? 'Posting...' : 'Post Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

const DeleteProjectModal = ({ project, onClose, onDeleted }) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleDelete = async () => {
    setLoading(true)
    setError('')
    try {
      await projectsAPI.deleteProject(project.id)
      onDeleted(project.id)
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Failed to delete project. Projects with active contracts cannot be deleted.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl space-y-4">
        <div className="flex items-center gap-3 text-red-600">
          <div className="p-2.5 bg-red-100 rounded-xl">
            <AlertTriangle className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">Delete Project</h2>
            <p className="text-xs text-gray-500">This action cannot be undone.</p>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl font-medium">
            {error}
          </div>
        )}

        <p className="text-sm text-gray-600">
          Are you sure you want to permanently delete <strong className="text-gray-900 font-semibold">"{project.title}"</strong>?
          Any pending proposals on this project will also be removed.
        </p>

        <div className="flex gap-3 pt-2">
          <button type="button" onClick={onClose} disabled={loading} className="btn-secondary flex-1">
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={loading}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2.5 px-4 rounded-xl transition flex items-center justify-center gap-2 text-sm disabled:opacity-60"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            {loading ? 'Deleting...' : 'Delete Project'}
          </button>
        </div>
      </div>
    </div>
  )
}

const ClientProjectsPage = () => {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [showModal, setShowModal] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState(null)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const res = await projectsAPI.getMyProjects()
      setProjects(res.data?.results || res.data || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const filtered = projects.filter(p => {
    const matchSearch = p.title?.toLowerCase().includes(search.toLowerCase())
    const matchStatus = statusFilter === 'ALL' || p.status === statusFilter
    return matchSearch && matchStatus
  })

  return (
    <>
      {showModal && (
        <CreateProjectModal
          onClose={() => setShowModal(false)}
          onCreated={(proj) => { setProjects(prev => [proj, ...prev]); setShowModal(false) }}
        />
      )}

      {projectToDelete && (
        <DeleteProjectModal
          project={projectToDelete}
          onClose={() => setProjectToDelete(null)}
          onDeleted={(deletedId) => {
            setProjects(prev => prev.filter(p => p.id !== deletedId))
            setProjectToDelete(null)
          }}
        />
      )}

      <div>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Projects</h1>
            <p className="text-gray-600 mt-1">{projects.length} project{projects.length !== 1 ? 's' : ''} total</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Post Project
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search projects..."
              className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm" />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
              className="pl-9 pr-8 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white appearance-none">
              <option value="ALL">All Status</option>
              <option value="OPEN">Open</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
            </select>
          </div>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-44 bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-gray-100">
            <Briefcase className="w-14 h-14 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{search ? 'No projects found' : 'No projects yet'}</h3>
            <p className="text-gray-500 mb-6">{search ? 'Try a different search term' : 'Post your first project to get started'}</p>
            {!search && <button onClick={() => setShowModal(true)} className="btn-primary">Post a Project</button>}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filtered.map(project => (
              <div key={project.id} className="bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-md transition-shadow flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold text-gray-900 flex-1 pr-3">{project.title}</h3>
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium whitespace-nowrap ${STATUS_COLORS[project.status] || 'bg-gray-100 text-gray-600'}`}>
                      {project.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{project.description}</p>
                </div>
                
                <div className="flex items-center justify-between pt-2 border-t border-gray-50">
                  <span className="text-sm font-semibold text-gray-900">${project.budget?.toLocaleString()}</span>
                  <div className="flex items-center gap-2">
                    {(project.status === 'OPEN' || project.status === 'CANCELLED') && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setProjectToDelete(project)
                        }}
                        title="Delete project"
                        className="text-gray-400 hover:text-red-600 hover:bg-red-50 p-1.5 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                    <button onClick={() => navigate(`/client/projects/${project.id}`)}
                      className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                      View <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export default ClientProjectsPage
