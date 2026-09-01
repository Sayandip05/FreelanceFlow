import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, Clock, DollarSign, Tag, User, ShieldCheck, CheckCircle,
  Briefcase, Send, AlertCircle
} from 'lucide-react'
import { projectsAPI } from '../../api/projects'
import { bidsAPI } from '../../api/bids'

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
    setSubmitting(true)
    setBidError('')
    try {
      await bidsAPI.submitBid(projectId, parseFloat(bidForm.amount), bidForm.cover_letter)
      setIsBidded(true)
    } catch (err) {
      if (err.response?.data) {
        // If it's a generic detail error
        if (err.response.data.detail) {
          setBidError(err.response.data.detail)
        } 
        // If it's field-level validation errors from Django (e.g. { cover_letter: ["Must be at least 50 chars"] })
        else if (typeof err.response.data === 'object') {
          const firstErrorKey = Object.keys(err.response.data)[0]
          const firstErrorMsg = err.response.data[firstErrorKey]
          // If it's an array (typical DRF format), get the first item, otherwise just stringify
          const errorText = Array.isArray(firstErrorMsg) ? firstErrorMsg[0] : String(firstErrorMsg)
          
          // Capitalize the field name for display (e.g. "cover_letter" -> "Cover letter: ")
          const fieldName = firstErrorKey.replace('_', ' ')
          const capitalizedField = fieldName.charAt(0).toUpperCase() + fieldName.slice(1)
          
          setBidError(`${capitalizedField}: ${errorText}`)
        } else {
          setBidError('Failed to submit proposal. Please try again.')
        }
      } else {
        setBidError('Failed to submit proposal. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-pulse">
        <div className="h-6 w-32 bg-gray-200 rounded" />
        <div className="h-10 w-3/4 bg-gray-200 rounded-xl" />
        <div className="h-44 bg-gray-100 rounded-2xl" />
        <div className="h-64 bg-gray-100 rounded-2xl" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center bg-white rounded-2xl border border-gray-100 p-8">
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
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/freelancer/browse')}
        className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Browse Projects
      </button>

      {/* Main Header Card */}
      <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-full">
                Fixed Budget Project
              </span>
              <span className="px-3 py-1 bg-green-50 text-green-700 text-xs font-semibold rounded-full flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Escrow Protected
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-gray-900 leading-tight">{project.title}</h1>
          </div>
          <div className="sm:text-right flex-shrink-0">
            <p className="text-3xl font-black text-gray-900">${parseFloat(project.budget)?.toLocaleString()}</p>
            <p className="text-xs text-gray-400 font-medium mt-0.5">Fixed Project Budget</p>
          </div>
        </div>

        {/* Short Summary Preview */}
        {project.short_description && (
          <div className="bg-primary-50/50 border border-primary-100 rounded-xl p-4 mb-6">
            <p className="text-xs font-semibold text-primary-800 uppercase tracking-wider mb-1">Short Preview</p>
            <p className="text-sm text-primary-950 font-medium leading-relaxed">{project.short_description}</p>
          </div>
        )}

        {/* Meta Info Bar */}
        <div className="flex flex-wrap items-center gap-6 text-sm text-gray-500 pt-4 border-t border-gray-100">
          <span className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-gray-400" /> Posted {new Date(project.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}
          </span>
          {project.client && (
            <span className="flex items-center gap-1.5">
              <User className="w-4 h-4 text-gray-400" /> Posted by {project.client.first_name || project.client.full_name || 'Client'} {project.client.client_profile?.company_name ? `(${project.client.client_profile.company_name})` : ''}
            </span>
          )}
        </div>
      </div>

      {/* Grid: Full Description + Proposal Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Full Detailed Paragraph & Skills */}
        <div className="lg:col-span-2 space-y-6">
          {/* Detailed Paragraph */}
          <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-primary-600" /> Detailed Project Description
            </h2>
            <div className="text-gray-700 text-base leading-relaxed whitespace-pre-line bg-gray-50/50 rounded-xl p-5 border border-gray-100">
              {project.description}
            </div>
          </div>

          {/* Required Skills */}
          {project.required_skills?.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Tag className="w-5 h-5 text-primary-600" /> Required Skills & Technologies
              </h2>
              <div className="flex flex-wrap gap-2">
                {project.required_skills.map((skill, i) => (
                  <span key={i} className="px-3.5 py-1.5 bg-gray-100 text-gray-800 text-sm rounded-xl font-medium flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5 text-gray-400" /> {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Submit Proposal Section */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm sticky top-20">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Submit Proposal</h2>
            <p className="text-xs text-gray-500 mb-5">Submit your bid and a short pitch explaining why you're interested.</p>

            {isBidded ? (
              <div className="bg-green-50 border border-green-200 rounded-xl p-5 text-center space-y-2">
                <CheckCircle className="w-10 h-10 text-green-600 mx-auto" />
                <p className="font-bold text-green-900 text-sm">Proposal Submitted!</p>
                <p className="text-xs text-green-700">You have already submitted a proposal for this project. The client will review your bid.</p>
              </div>
            ) : (
              <form onSubmit={handleBidSubmit} className="space-y-4">
                {bidError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                    {bidError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                    Your Bid Amount ($)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 font-bold">$</span>
                    <input
                      type="number"
                      value={bidForm.amount}
                      onChange={e => setBidForm({ ...bidForm, amount: e.target.value })}
                      required
                      min="1"
                      placeholder={project.budget}
                      className="w-full pl-8 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-semibold text-gray-900"
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
                    className="w-full p-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm text-gray-900 resize-none"
                  />
                  <p className="text-[11px] text-gray-400 mt-1">
                    Tip: Keep it short and focused. Clients prefer quick, relevant overviews.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full btn-primary py-3 text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-60"
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

      </div>
    </div>
  )
}
