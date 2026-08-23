import { useState, useEffect } from 'react'
import { Star, CheckCircle, Clock, MessageSquare, User, ChevronDown, ChevronUp, Send } from 'lucide-react'
import { deliverableAPI } from '../../api/worklogs'
import { contractsAPI, reviewsAPI } from '../../api/bids'
import { formatCurrency } from '../../utils/formatCurrency'

// ── Star Rating Input ─────────────────────────────────────────────────────────
const StarRatingInput = ({ value, onChange }) => (
  <div className="flex gap-1">
    {[1, 2, 3, 4, 5].map((star) => (
      <button
        key={star}
        type="button"
        onClick={() => onChange(star)}
        className="transition-transform hover:scale-110"
      >
        <Star
          className={`w-7 h-7 transition-colors ${
            star <= value ? 'text-yellow-400 fill-yellow-400' : 'text-gray-200 fill-gray-100'
          }`}
        />
      </button>
    ))}
  </div>
)

// ── Static Star Display ───────────────────────────────────────────────────────
const StarDisplay = ({ value, small }) => (
  <div className="flex gap-0.5">
    {[1, 2, 3, 4, 5].map((star) => (
      <Star
        key={star}
        className={`${small ? 'w-3.5 h-3.5' : 'w-4 h-4'} ${
          star <= Math.round(value) ? 'text-yellow-400 fill-yellow-400' : 'text-gray-200 fill-gray-200'
        }`}
      />
    ))}
  </div>
)

// ── Review Form Modal ─────────────────────────────────────────────────────────
const ReviewModal = ({ contract, onClose, onSuccess }) => {
  const [form, setForm] = useState({
    rating: 0,
    review_text: '',
    communication_rating: 0,
    quality_rating: 0,
    professionalism_rating: 0,
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.rating === 0) { setError('Please select an overall star rating.'); return }
    if (form.review_text.trim().length < 10) { setError('Review must be at least 10 characters.'); return }
    setSubmitting(true)
    setError('')
    try {
      await reviewsAPI.createReview({
        contract_id: contract.id,
        rating: form.rating,
        review_text: form.review_text,
        communication_rating: form.communication_rating || null,
        quality_rating: form.quality_rating || null,
        professionalism_rating: form.professionalism_rating || null,
        is_public: true,
      })
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit review.')
    } finally {
      setSubmitting(false)
    }
  }

  const freelancerName = contract.bid?.freelancer?.full_name || 'Freelancer'
  const freelancerAvatar = contract.bid?.freelancer?.avatar || contract.freelancer?.avatar

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-8 relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 text-2xl leading-none"
        >×</button>

        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center overflow-hidden flex-shrink-0">
            {freelancerAvatar ? (
              <img src={freelancerAvatar} alt={freelancerName} className="w-full h-full object-cover" />
            ) : (
              <User className="w-7 h-7 text-white" />
            )}
          </div>
          <div>
            <h2 className="text-xl font-black text-gray-900">Review {freelancerName}</h2>
            <p className="text-xs text-gray-500 mt-0.5">Contract: {contract.bid?.project?.title || 'Project'}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Overall Rating */}
          <div>
            <label className="text-sm font-bold text-gray-700 mb-2 block">Overall Rating *</label>
            <StarRatingInput value={form.rating} onChange={(v) => setForm(p => ({ ...p, rating: v }))} />
          </div>

          {/* Detailed Ratings */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { key: 'communication_rating', label: 'Communication' },
              { key: 'quality_rating', label: 'Quality' },
              { key: 'professionalism_rating', label: 'Professionalism' },
            ].map(({ key, label }) => (
              <div key={key} className="text-center bg-gray-50 rounded-2xl p-3">
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wide mb-2">{label}</p>
                <div className="flex flex-col items-center gap-1">
                  {[1,2,3,4,5].map(star => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setForm(p => ({ ...p, [key]: star }))}
                      className="p-0.5"
                    >
                      <Star className={`w-4 h-4 ${star <= form[key] ? 'text-yellow-400 fill-yellow-400' : 'text-gray-200 fill-gray-100'}`} />
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Review Text */}
          <div>
            <label className="text-sm font-bold text-gray-700 mb-2 block">Your Review *</label>
            <textarea
              rows={4}
              className="w-full border border-gray-200 rounded-2xl px-4 py-3 text-sm text-gray-800 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
              placeholder="Share your experience working with this freelancer..."
              value={form.review_text}
              onChange={(e) => setForm(p => ({ ...p, review_text: e.target.value }))}
            />
          </div>

          {error && <p className="text-xs text-red-600 font-semibold bg-red-50 rounded-xl px-4 py-2">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold py-3.5 rounded-2xl hover:from-indigo-600 hover:to-purple-700 disabled:opacity-60 transition-all"
          >
            <Send className="w-4 h-4" />
            {submitting ? 'Submitting...' : 'Submit Review'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Main Review Page ──────────────────────────────────────────────────────────
const ClientReviewPage = () => {
  const [deliverables, setDeliverables] = useState([])
  const [contracts, setContracts] = useState([])
  const [givenReviews, setGivenReviews] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('pending')
  const [reviewContract, setReviewContract] = useState(null)
  const [expandedReview, setExpandedReview] = useState(null)

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    setIsLoading(true)
    try {
      const [delivRes, contractRes, reviewRes] = await Promise.allSettled([
        deliverableAPI.getDeliverables(null, null),
        contractsAPI.getContracts(),
        reviewsAPI.getGiven(),
      ])

      if (delivRes.status === 'fulfilled') {
        setDeliverables(delivRes.value.data?.results || delivRes.value.data || [])
      }
      if (contractRes.status === 'fulfilled') {
        setContracts(contractRes.value.data?.results || contractRes.value.data || [])
      }
      if (reviewRes.status === 'fulfilled') {
        setGivenReviews(reviewRes.value.data?.results || reviewRes.value.data || [])
      }
    } catch (err) {
      console.error('Failed to fetch review data:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Compute stats
  const pending = deliverables.filter(d => d.status === 'SUBMITTED').length
  const approved = deliverables.filter(d => d.status === 'APPROVED').length
  const reviewableContracts = contracts.filter(c => !c.is_active && c.status === 'COMPLETED')
  const reviewedIds = new Set(givenReviews.map(r => r.contract?.id))
  const awaitingReview = reviewableContracts.filter(c => !reviewedIds.has(c.id))

  const tabs = [
    { key: 'pending', label: `Pending Deliverables (${pending})` },
    { key: 'approved', label: `Approved (${approved})` },
    { key: 'leave_review', label: `Leave Review (${awaitingReview.length})` },
    { key: 'given', label: `Reviews Given (${givenReviews.length})` },
  ]

  const filteredDeliverables = (() => {
    if (activeTab === 'pending') return deliverables.filter(d => d.status === 'SUBMITTED')
    if (activeTab === 'approved') return deliverables.filter(d => d.status === 'APPROVED')
    return []
  })()

  return (
    <div className="flex-1 p-8 min-h-screen bg-gray-50">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-black text-gray-900 tracking-tight">Review Center</h1>
        <p className="text-gray-500 mt-1 text-sm">Review deliverables and rate freelancers you've worked with</p>
      </div>

      {/* Stats Row */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 flex items-center gap-4 shadow-sm">
            <div className="w-12 h-12 bg-yellow-50 rounded-xl flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-500" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">Pending Review</p>
              <p className="text-3xl font-black text-gray-900">{pending}</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 p-6 flex items-center gap-4 shadow-sm">
            <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">Approved</p>
              <p className="text-3xl font-black text-gray-900">{approved}</p>
            </div>
          </div>

          <div
            onClick={() => setActiveTab('leave_review')}
            className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 flex items-center gap-4 shadow-sm cursor-pointer hover:from-indigo-600 hover:to-purple-700 transition-all"
          >
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Star className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xs text-white/70 font-semibold uppercase tracking-wide">Awaiting Your Review</p>
              <p className="text-3xl font-black text-white">{awaitingReview.length}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-2xl mb-6 w-full overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 min-w-max py-2 px-4 rounded-xl text-sm font-bold transition-all ${
              activeTab === tab.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {/* Deliverables Tabs */}
          {(activeTab === 'pending' || activeTab === 'approved') && (
            <>
              {filteredDeliverables.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
                  <CheckCircle className="w-12 h-12 text-gray-200 mx-auto mb-3" />
                  <p className="text-gray-400 font-semibold">
                    {activeTab === 'pending' ? 'No pending deliverables' : 'No approved deliverables yet'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredDeliverables.map(d => {
                    const freelancerName = d.freelancer?.full_name || d.freelancer?.email || 'Freelancer'
                    const freelancerAvatar = d.freelancer?.avatar
                    return (
                      <div key={d.id} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center overflow-hidden flex-shrink-0">
                          {freelancerAvatar ? (
                            <img src={freelancerAvatar} alt={freelancerName} className="w-full h-full object-cover" />
                          ) : (
                            <User className="w-5 h-5 text-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-gray-900 text-sm truncate">{d.title}</p>
                          <p className="text-xs text-gray-500">{freelancerName} · {new Date(d.created_at).toLocaleDateString()}</p>
                        </div>
                        <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                          d.status === 'SUBMITTED' ? 'bg-yellow-50 text-yellow-700' :
                          d.status === 'APPROVED' ? 'bg-green-50 text-green-700' :
                          'bg-gray-50 text-gray-600'
                        }`}>{d.status}</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {/* Leave Review Tab */}
          {activeTab === 'leave_review' && (
            <>
              {awaitingReview.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
                  <Star className="w-12 h-12 text-gray-200 mx-auto mb-3" />
                  <p className="text-gray-400 font-semibold">No completed contracts awaiting review</p>
                  <p className="text-gray-400 text-xs mt-1">Reviews become available when a contract is marked complete</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {awaitingReview.map(c => {
                    const freelancerName = c.bid?.freelancer?.full_name || c.freelancer?.full_name || 'Freelancer'
                    const freelancerAvatar = c.bid?.freelancer?.avatar || c.freelancer?.avatar
                    const projectTitle = c.bid?.project?.title || c.project?.title || 'Project'
                    return (
                      <div key={c.id} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center overflow-hidden flex-shrink-0">
                          {freelancerAvatar ? (
                            <img src={freelancerAvatar} alt={freelancerName} className="w-full h-full object-cover" />
                          ) : (
                            <User className="w-6 h-6 text-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-gray-900 text-sm">{freelancerName}</p>
                          <p className="text-xs text-gray-500">{projectTitle}</p>
                          <p className="text-xs text-gray-400">Amount: {formatCurrency(c.agreed_amount)}</p>
                        </div>
                        <button
                          onClick={() => setReviewContract(c)}
                          className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-bold px-4 py-2 rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all flex-shrink-0"
                        >
                          <Star className="w-3.5 h-3.5" />
                          Rate Now
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {/* Reviews Given Tab */}
          {activeTab === 'given' && (
            <>
              {givenReviews.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
                  <MessageSquare className="w-12 h-12 text-gray-200 mx-auto mb-3" />
                  <p className="text-gray-400 font-semibold">You haven't left any reviews yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {givenReviews.map(r => {
                    const revieweeName = r.reviewee?.full_name || 'Freelancer'
                    const revieweeAvatar = r.reviewee?.avatar
                    const isExpanded = expandedReview === r.id
                    return (
                      <div key={r.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                        <div
                          className="p-5 flex items-center gap-4 cursor-pointer"
                          onClick={() => setExpandedReview(isExpanded ? null : r.id)}
                        >
                          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center overflow-hidden flex-shrink-0">
                            {revieweeAvatar ? (
                              <img src={revieweeAvatar} alt={revieweeName} className="w-full h-full object-cover" />
                            ) : (
                              <User className="w-5 h-5 text-white" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-gray-900 text-sm">{revieweeName}</p>
                            <StarDisplay value={r.rating} small />
                          </div>
                          <p className="text-xs text-gray-400 mr-2">{new Date(r.created_at).toLocaleDateString()}</p>
                          {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                        </div>
                        {isExpanded && (
                          <div className="px-5 pb-5 border-t border-gray-50 pt-4">
                            <p className="text-sm text-gray-700 leading-relaxed">{r.review_text}</p>
                            {(r.communication_rating || r.quality_rating || r.professionalism_rating) && (
                              <div className="flex flex-wrap gap-4 mt-4">
                                {[['Communication', r.communication_rating], ['Quality', r.quality_rating], ['Professionalism', r.professionalism_rating]].map(([label, val]) => val ? (
                                  <div key={label} className="text-center">
                                    <p className="text-[10px] text-gray-400 font-bold uppercase mb-0.5">{label}</p>
                                    <StarDisplay value={val} small />
                                  </div>
                                ) : null)}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* Review Modal */}
      {reviewContract && (
        <ReviewModal
          contract={reviewContract}
          onClose={() => setReviewContract(null)}
          onSuccess={() => {
            setReviewContract(null)
            fetchAll()
          }}
        />
      )}
    </div>
  )
}

export default ClientReviewPage
