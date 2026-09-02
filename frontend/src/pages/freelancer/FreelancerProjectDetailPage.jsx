import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, Clock, DollarSign, Tag, User, ShieldCheck, CheckCircle,
  Briefcase, Send, AlertCircle
} from 'lucide-react'
import { projectsAPI } from '../../api/projects'
import { bidsAPI } from '../../api/bids'
import { DetailPageSkeleton } from '../../components/common/Skeleton'

export default function FreelancerProjectDetailPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Proposal Form State
  const [bidForm, setBidForm] = useState({ amount: '', cover_letter: '' })
  const [submitting, setSubmitting] = useState(false)
  const [bidError, setBidError] = useState('')
  const [isBidded, setIsBidded] = useState(false)

  useEffect(() => {
    fetchProjectDetail()
  }, [projectId])

  const fetchProjectDetail = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await projectsAPI.getProject(projectId)
      setProject(res.data)
      setBidForm(prev => ({ ...prev, amount: res.data?.budget || '' }))

      // Check if user already submitted a bid for this project
      try {
        const myBidsRes = await bidsAPI.getMyBids()
        const myBids = myBidsRes.data?.results || myBidsRes.data || []
        const existingBid = myBids.find(b => b.project === parseInt(projectId) || b.project?.id === parseInt(projectId))
        if (existingBid) {
          setIsBidded(true)
        }
      } catch (e) {
        // Ignore errors checking my_bids
      }
    } catch (err) {
      console.error(err)
      setError('Failed to load project details. It may have been removed.')
    } finally {
      setLoading(false)
    }
  }

  const handleBidSubmit = async (e) => {
    e.preventDefault()
    if (!bidForm.amount || !bidForm.cover_letter) return

    setSubmitting(true)
    setBidError('')
    try {
      const pId = parseInt(projectId, 10) || projectId
      await bidsAPI.submitBid({
        project: pId,
        amount: parseFloat(bidForm.amount),
        cover_letter: bidForm.cover_letter,
      })
      setIsBidded(true)
    } catch (err) {
      console.error(err)
      const data = err.response?.data
      let msg = 'Failed to submit proposal. Please try again.'
      if (typeof data === 'string') msg = data
      else if (data?.error) msg = data.error
      else if (data?.detail) msg = data.detail
      else if (data?.non_field_errors) msg = data.non_field_errors[0]
      else if (data?.amount) msg = `Amount error: ${Array.isArray(data.amount) ? data.amount[0] : data.amount}`
      else if (data?.cover_letter) msg = `Proposal error: ${Array.isArray(data.cover_letter) ? data.cover_letter[0] : data.cover_letter}`
      else if (typeof data === 'object') {
        const firstKey = Object.keys(data)[0]
        const firstVal = data[firstKey]
        const text = Array.isArray(firstVal) ? firstVal[0] : String(firstVal)
        const fieldName = firstKey.replace('_', ' ')
        msg = `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)}: ${text}`
      }
      setBidError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-6">
        <DetailPageSkeleton />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="max-w-3xl mx-auto py-16 text-center bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Project Not Found</h2>
        <p className="text-gray-500 mb-6">{error || "The project you're looking for doesn't exist."}</p>
        <Link to="/freelancer/browse" className="btn-primary inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Browse Projects
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-16">
      {/* Back button */}
      <button
        onClick={() => navigate('/freelancer/browse')}
        className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Browse Projects
      </button>

      {/* Main Header Card */}
      <div className="bg-white rounded-2xl border border-gray-100 p-7 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-5">
          <div>
            <div className="flex items-center gap-2 mb-2.5">
              <span className="px-3 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-full">
                Fixed Budget Project
              </span>
              <span className="px-3 py-1 bg-green-50 text-green-700 text-xs font-semibold rounded-full flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Escrow Protected
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 leading-tight">{project.title}</h1>
          </div>
          <div className="sm:text-right flex-shrink-0">
            <p className="text-2xl sm:text-3xl font-black text-gray-900">${parseFloat(project.budget)?.toLocaleString()}</p>
            <p className="text-xs text-gray-400 font-medium mt-0.5">Fixed Project Budget</p>
          </div>
        </div>

        {/* Meta Info Bar */}
        <div className="flex flex-wrap items-center gap-6 text-xs sm:text-sm text-gray-500 pt-4 border-t border-gray-100">
          <span className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-gray-400" /> Posted {new Date(project.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}
          </span>
          {project.approx_duration && (
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-gray-400" /> Duration: {project.approx_duration}
            </span>
          )}
          {project.client && (
            <span className="flex items-center gap-1.5">
              <User className="w-4 h-4 text-gray-400" /> Posted by {project.client.first_name || project.client.full_name || 'Client'} {project.client.client_profile?.company_name ? `(${project.client.client_profile.company_name})` : ''}
            </span>
          )}
        </div>
      </div>

      {/* Detailed Project Description Card (Narrow & Full text without any truncation) */}
      <div className="bg-white rounded-2xl border border-gray-100 p-7 sm:p-8 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-primary-600" /> Detailed Project Description
        </h2>
        <div className="text-gray-700 text-sm sm:text-base leading-relaxed whitespace-pre-line bg-gray-50/60 rounded-xl p-5 sm:p-6 border border-gray-100">
          {project.description || project.short_description || 'No detailed description provided by client.'}
        </div>
      </div>

      {/* Required Skills & Technologies */}
      {project.required_skills?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-7 sm:p-8 shadow-sm">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Tag className="w-5 h-5 text-primary-600" /> Required Skills & Technologies
          </h2>
          <div className="flex flex-wrap gap-2">
            {project.required_skills.map((skill, i) => (
              <span key={i} className="px-3.5 py-1.5 bg-gray-100 text-gray-800 text-xs sm:text-sm rounded-xl font-medium flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5 text-gray-400" /> {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Submit Proposal Section (Positioned at the last part in narrow style) */}
      <div className="bg-white rounded-2xl border border-gray-100 p-7 sm:p-8 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-1">Submit Proposal</h2>
        <p className="text-xs sm:text-sm text-gray-500 mb-6">Submit your bid and a short pitch explaining why you're interested.</p>

        {isBidded ? (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center space-y-2">
            <CheckCircle className="w-10 h-10 text-green-600 mx-auto" />
            <p className="font-bold text-green-900 text-base">Proposal Submitted!</p>
            <p className="text-xs sm:text-sm text-green-700">You have already submitted a proposal for this project. The client will review your bid.</p>
          </div>
        ) : (
          <form onSubmit={handleBidSubmit} className="space-y-5">
            {bidError && (
              <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs sm:text-sm text-red-700">
                {bidError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Your Bid Amount ($)
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 font-bold">$</span>
                <input
                  type="number"
                  value={bidForm.amount}
                  onChange={e => setBidForm({ ...bidForm, amount: e.target.value })}
                  required
                  min="1"
                  placeholder={project.budget}
                  className="w-full pl-9 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-semibold text-gray-900 bg-white"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Why You're a Great Fit
                </label>
                <span className="text-[11px] font-medium text-gray-400">
                  4–5 lines recommended
                </span>
              </div>
              <textarea
                value={bidForm.cover_letter}
                onChange={e => setBidForm({ ...bidForm, cover_letter: e.target.value })}
                required
                rows={4}
                placeholder="Briefly explain why you're interested in this project and your relevant experience (approx. 4–5 lines)..."
                className="w-full p-3.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm text-gray-900 resize-none bg-white"
              />
              <p className="text-[11px] text-gray-400 mt-1">
                Tip: Keep it short and focused. Clients prefer quick, relevant overviews.
              </p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full btn-primary py-3.5 text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-60 shadow-md shadow-primary-500/20 active:scale-99 transition-all cursor-pointer"
            >
              {submitting ? (
                'Submitting Proposal...'
              ) : (
                <>
                  <Send className="w-4 h-4" /> Send Proposal
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
