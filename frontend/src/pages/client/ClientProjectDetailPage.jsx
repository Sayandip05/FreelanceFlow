import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Briefcase, Clock, User, IndianRupee, CheckCircle, XCircle, MessageSquare,
  Trash2, AlertTriangle, Loader2
} from 'lucide-react'
import { projectsAPI } from '../../api/projects'
import { bidsAPI } from '../../api/bids'
import { DetailPageSkeleton } from '../../components/common/Skeleton'
import { formatCurrency } from '../../utils/formatCurrency'
import { getWebSocketUrl } from '../../utils/websocket'

const ClientProjectDetailPage = () => {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [bids, setBids] = useState([])
  const [loading, setLoading] = useState(true)
  const [accepting, setAccepting] = useState(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const wsRef = useRef(null)

  useEffect(() => {
    fetchData()
  }, [projectId])

  // Real-time Bid sync over WebSocket
  useEffect(() => {
    if (!projectId) return
    const token =
      localStorage.getItem('access_token') ||
      sessionStorage.getItem('access_token') ||
      ''
    const wsUrl = getWebSocketUrl(`/ws/project/${projectId}/`, token ? { token } : {})

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'bid_submitted') {
          const newBid = data.payload
          setBids((prev) => {
            // Avoid duplicates
            if (prev.some((b) => b.id === newBid.id)) return prev
            return [newBid, ...prev]
          })
        }
      } catch (err) {
        console.error('Error parsing project WS message:', err)
      }
    }

    ws.onerror = () => ws.close()

    return () => {
      ws.close()
    }
  }, [projectId])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [projRes, bidsRes] = await Promise.allSettled([
        projectsAPI.getProject(projectId),
        projectsAPI.getProjectBids(projectId),
      ])
      if (projRes.status === 'fulfilled') setProject(projRes.value.data)
      if (bidsRes.status === 'fulfilled') setBids(bidsRes.value.data?.results || bidsRes.value.data || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleAcceptBid = async (bidId) => {
    setAccepting(bidId)
    try {
      const res = await bidsAPI.acceptBid(bidId)
      const contractId = res.data.contract?.id
      if (contractId) {
        navigate(`/client/contracts/${contractId}`)
      } else {
        await fetchData()
      }
    } catch (e) {
      console.error(e)
    } finally {
      setAccepting(null)
    }
  }

  const handleRejectBid = async (bidId) => {
    try {
      await bidsAPI.rejectBid(bidId)
      setBids(prev => prev.map(b => b.id === bidId ? { ...b, status: 'REJECTED' } : b))
    } catch (e) {
      console.error(e)
    }
  }

  const handleDeleteProject = async () => {
    setDeleting(true)
    setDeleteError('')
    try {
      await projectsAPI.deleteProject(projectId)
      navigate('/client/projects')
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Failed to delete project. Active or completed projects cannot be deleted.'
      setDeleteError(msg)
      setDeleting(false)
    }
  }

  if (loading) return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <DetailPageSkeleton />
    </div>
  )

  if (!project) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-600 mb-4">Project not found.</p>
        <button onClick={() => navigate('/client/projects')} className="btn-primary">Back to Projects</button>
      </div>
    </div>
  )

  const pendingBids = bids.filter(b => b.status === 'PENDING')
  const acceptedBid = bids.find(b => b.status === 'ACCEPTED')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
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

            {deleteError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl font-medium">
                {deleteError}
              </div>
            )}

            <p className="text-sm text-gray-600">
              Are you sure you want to permanently delete <strong className="text-gray-900 font-semibold">"{project.title}"</strong>?
              Any proposals received on this project will also be removed.
            </p>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteProject}
                disabled={deleting}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2.5 px-4 rounded-xl transition flex items-center justify-center gap-2 text-sm disabled:opacity-60"
              >
                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {deleting ? 'Deleting...' : 'Delete Project'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-6 py-4">
        <button onClick={() => navigate('/client/projects')} className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-3">
          <ArrowLeft className="w-4 h-4" /> Back to Projects
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
            <p className="text-gray-500 text-sm mt-1">Posted {new Date(project.created_at).toLocaleDateString()}</p>
          </div>
          <div className="flex items-center gap-3">
            {(project.status === 'OPEN' || project.status === 'CANCELLED') && (
              <button
                onClick={() => setShowDeleteModal(true)}
                className="px-3.5 py-1.5 text-xs font-semibold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl transition flex items-center gap-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" /> Delete Project
              </button>
            )}
            <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${
              project.status === 'OPEN' ? 'bg-green-100 text-green-700' :
              project.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-600'
            }`}>{project.status}</span>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Description + Bids */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Project Description</h2>
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{project.description}</p>
              {project.required_skills?.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Required Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {project.required_skills.map((skill, i) => (
                      <span key={i} className="px-3 py-1 bg-primary-50 text-primary-700 text-sm rounded-full font-medium">{skill}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Accepted Bid */}
            {acceptedBid && (
              <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <h2 className="text-lg font-semibold text-green-800">Accepted Bid</h2>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{acceptedBid.freelancer?.first_name} {acceptedBid.freelancer?.last_name}</p>
                    <p className="text-sm text-gray-600">{formatCurrency(acceptedBid.amount)} · {acceptedBid.delivery_days} days</p>
                  </div>
                  <button
                    onClick={() => navigate(`/client/contracts/${acceptedBid.contract_id}`)}
                    className="btn-primary text-sm"
                  >
                    View Contract
                  </button>
                </div>
              </div>
            )}

            {/* Bids */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Bids ({bids.length})
              </h2>
              {bids.length === 0 ? (
                <div className="text-center py-10">
                  <User className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No bids yet. Check back soon!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {bids.map(bid => {
                    const freelancerName = `${bid.freelancer?.first_name || ''} ${bid.freelancer?.last_name || ''}`.trim()
                    const freelancerAvatar = bid.freelancer?.avatar
                    return (
                    <div key={bid.id} className={`border rounded-xl p-4 ${
                      bid.status === 'ACCEPTED' ? 'border-green-200 bg-green-50' :
                      bid.status === 'REJECTED' ? 'border-gray-200 opacity-60' :
                      'border-gray-200'
                    }`}>
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center overflow-hidden flex-shrink-0">
                            {freelancerAvatar ? (
                              <img src={freelancerAvatar} alt={freelancerName} className="w-full h-full object-cover" />
                            ) : (
                              <User className="w-5 h-5 text-white" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{freelancerName}</p>
                            <p className="text-sm text-gray-500">{bid.freelancer?.email}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-gray-900">{formatCurrency(bid.amount)}</p>
                          {bid.delivery_days && <p className="text-xs text-gray-500">{bid.delivery_days} days</p>}
                        </div>
                      </div>
                      {bid.cover_letter && (
                        <p className="text-sm text-gray-700 mb-3 bg-gray-50 rounded-lg p-3">{bid.cover_letter}</p>
                      )}
                      {bid.status === 'PENDING' && (
                        <div className="flex gap-2 mt-2">
                          <button
                            onClick={() => handleAcceptBid(bid.id)}
                            disabled={accepting === bid.id}
                            className="flex items-center gap-1.5 px-4 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors disabled:opacity-60"
                          >
                            <CheckCircle className="w-4 h-4" />
                            {accepting === bid.id ? 'Accepting...' : 'Accept'}
                          </button>
                          <button
                            onClick={() => handleRejectBid(bid.id)}
                            className="flex items-center gap-1.5 px-4 py-1.5 bg-red-50 text-red-600 text-sm rounded-lg hover:bg-red-100 transition-colors"
                          >
                            <XCircle className="w-4 h-4" /> Reject
                          </button>
                        </div>
                      )}
                      {bid.status !== 'PENDING' && (
                        <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                          bid.status === 'ACCEPTED' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                        }`}>{bid.status}</span>
                      )}
                    </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Project Details</h3>
              <div className="space-y-3">
                {[
                  { icon: IndianRupee, label: 'Budget', value: formatCurrency(project.budget) },
                  { icon: Clock, label: 'Duration', value: project.approx_duration || 'Not specified' },
                  { icon: Clock, label: 'Posted', value: new Date(project.created_at).toLocaleDateString() },
                  { icon: User, label: 'Total Bids', value: bids.length },
                  { icon: CheckCircle, label: 'Pending Bids', value: pendingBids.length },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center">
                      <item.icon className="w-4 h-4 text-gray-500" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">{item.label}</p>
                      <p className="text-sm font-medium text-gray-900">{item.value}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ClientProjectDetailPage
