import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { deliverableAPI } from '../../api/worklogs'
import { contractsAPI } from '../../api/bids'
import { DetailPageSkeleton } from '../../components/common/Skeleton'
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ArrowPathIcon,
  DocumentTextIcon,
  PaperClipIcon,
  ClockIcon,
  UserIcon
} from '@heroicons/react/24/outline'
import { formatDate } from '../../utils/formatDate'
import { useToast, useConfirm } from '../../context/ModalToastContext'

const ClientDeliverableReviewPage = () => {
  const { deliverableId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const confirm = useConfirm()
  const [deliverable, setDeliverable] = useState(null)
  const [contract, setContract] = useState(null)
  const [loading, setLoading] = useState(true)
  const [feedback, setFeedback] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const [showChatTranscript, setShowChatTranscript] = useState(false)

  useEffect(() => {
    fetchDeliverable()
  }, [deliverableId])

  const fetchDeliverable = async () => {
    try {
      const response = await deliverableAPI.getDeliverableDetail(deliverableId)
      setDeliverable(response.data)
      
      // If contract is already embedded as an object, use it directly (0 additional latency)
      if (typeof response.data.contract === 'object' && response.data.contract !== null) {
        setContract(response.data.contract)
      } else if (response.data.contract) {
        const contractResponse = await contractsAPI.getContractDetail(response.data.contract)
        setContract(contractResponse.data)
      }
    } catch (error) {
      console.error('Error fetching deliverable:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!feedback.trim()) {
      const ok = await confirm({
        title: 'Approve Deliverable',
        message: 'Are you sure you want to approve without feedback?',
        confirmText: 'Approve',
        type: 'primary',
      })
      if (!ok) return
    }

    setActionLoading(true)
    try {
      await deliverableAPI.approveDeliverable(deliverableId, feedback)
      toast.success('Deliverable approved! Payment release is now enabled.')
      navigate(`/client/contracts/${deliverable.contract}`)
    } catch (error) {
      console.error('Error approving deliverable:', error)
      toast.error('Failed to approve deliverable')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRequestRevision = async () => {
    if (!feedback.trim()) {
      toast.warning('Please provide feedback explaining what needs to be revised')
      return
    }

    setActionLoading(true)
    try {
      await deliverableAPI.rejectDeliverable(deliverableId, feedback, 'request_revision')
      toast.success('Revision requested. The freelancer will be notified.')
      navigate(`/client/contracts/${deliverable.contract}`)
    } catch (error) {
      console.error('Error requesting revision:', error)
      toast.error('Failed to request revision')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async () => {
    if (!feedback.trim()) {
      toast.warning('Please provide feedback explaining why you are rejecting this deliverable')
      return
    }

    const ok = await confirm({
      title: 'Reject Deliverable',
      message: 'Are you sure you want to reject this deliverable? This action cannot be undone.',
      confirmText: 'Reject Deliverable',
      type: 'danger',
    })
    if (!ok) return

    setActionLoading(true)
    try {
      await deliverableAPI.rejectDeliverable(deliverableId, feedback, 'reject')
      toast.success('Deliverable rejected.')
      navigate(`/client/contracts/${deliverable.contract}`)
    } catch (error) {
      console.error('Error rejecting deliverable:', error)
      toast.error('Failed to reject deliverable')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <DetailPageSkeleton />
      </div>
    )
  }

  if (!deliverable) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Deliverable not found</p>
        </div>
      </div>
    )
  }

  const canReview = deliverable.status === 'SUBMITTED' || deliverable.status === 'UNDER_REVIEW'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <button
            onClick={() => navigate(`/client/contracts/${deliverable.contract}`)}
            className="text-sm text-indigo-600 hover:text-indigo-800 mb-2"
          >
            ← Back to Contract
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Review Deliverable
              </h1>
              <p className="text-gray-600 mt-1">
                {contract?.bid.project.title}
              </p>
            </div>
            <div>
              <span
                className={`px-4 py-2 rounded-full text-sm font-medium ${
                  deliverable.status === 'APPROVED'
                    ? 'bg-green-100 text-green-800'
                    : deliverable.status === 'SUBMITTED'
                    ? 'bg-yellow-100 text-yellow-800'
                    : deliverable.status === 'REVISION_REQUESTED'
                    ? 'bg-orange-100 text-orange-800'
                    : deliverable.status === 'REJECTED'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {deliverable.status.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Deliverable Info */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                {deliverable.title}
              </h2>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="flex items-center gap-2 text-gray-600">
                  <UserIcon className="w-5 h-5" />
                  <span className="text-sm">
                    {deliverable.freelancer.first_name} {deliverable.freelancer.last_name}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <ClockIcon className="w-5 h-5" />
                  <span className="text-sm">{deliverable.hours_logged} hours logged</span>
                </div>
                <div className="text-sm text-gray-600">
                  <strong>Submitted:</strong> {formatDate(deliverable.submitted_at)}
                </div>
                {deliverable.reviewed_at && (
                  <div className="text-sm text-gray-600">
                    <strong>Reviewed:</strong> {formatDate(deliverable.reviewed_at)}
                  </div>
                )}
              </div>

              <div className="border-t border-gray-200 pt-4">
                <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                <p className="text-gray-700 whitespace-pre-wrap">{deliverable.description}</p>
              </div>
            </div>

            {/* AI-Generated Report */}
            <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg shadow border border-indigo-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <DocumentTextIcon className="w-6 h-6 text-indigo-600" />
                <h3 className="text-lg font-semibold text-gray-900">
                  AI-Generated Professional Report
                </h3>
              </div>
              <div className="bg-white rounded-lg p-6 border border-indigo-100">
                <pre className="whitespace-pre-wrap text-gray-800 font-sans text-sm leading-relaxed">
                  {deliverable.ai_generated_report}
                </pre>
              </div>
            </div>

            {/* Attached Files */}
            {deliverable.attached_files && deliverable.attached_files.length > 0 && (
              <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <PaperClipIcon className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Attached Files</h3>
                </div>
                <div className="space-y-2">
                  {deliverable.attached_files.map((file, index) => (
                    <a
                      key={index}
                      href={file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <PaperClipIcon className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-indigo-600 hover:underline">
                        View Attachment {index + 1}
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* AI Chat Transcript */}
            {deliverable.ai_chat_transcript && deliverable.ai_chat_transcript.length > 0 && (
              <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                <button
                  onClick={() => setShowChatTranscript(!showChatTranscript)}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h3 className="font-semibold text-gray-900">
                    View AI Chat Transcript
                  </h3>
                  <span className="text-sm text-indigo-600">
                    {showChatTranscript ? 'Hide' : 'Show'}
                  </span>
                </button>
                
                {showChatTranscript && (
                  <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
                    {deliverable.ai_chat_transcript.map((message, index) => (
                      <div
                        key={index}
                        className={`flex ${
                          message.role === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                            message.role === 'user'
                              ? 'bg-indigo-100 text-indigo-900'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Previous Feedback */}
            {deliverable.client_feedback && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <h3 className="font-semibold text-yellow-900 mb-2">Previous Feedback</h3>
                <p className="text-yellow-800 whitespace-pre-wrap">{deliverable.client_feedback}</p>
              </div>
            )}
          </div>

          {/* Sidebar - Review Actions */}
          <div className="space-y-6">
            {canReview ? (
              <>
                {/* Feedback Form */}
                <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Your Feedback</h3>
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Add your feedback (optional for approval, required for rejection/revision)"
                    className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                    rows="6"
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    {feedback.length} characters
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="bg-white rounded-lg shadow border border-gray-200 p-6 space-y-3">
                  <h3 className="font-semibold text-gray-900 mb-4">Review Actions</h3>
                  
                  <button
                    onClick={handleApprove}
                    disabled={actionLoading}
                    className="w-full flex items-center justify-center gap-2 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    <CheckCircleIcon className="w-5 h-5" />
                    {actionLoading ? 'Processing...' : 'Approve Deliverable'}
                  </button>
                  
                  <button
                    onClick={handleRequestRevision}
                    disabled={actionLoading}
                    className="w-full flex items-center justify-center gap-2 bg-yellow-600 text-white py-3 rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    <ArrowPathIcon className="w-5 h-5" />
                    {actionLoading ? 'Processing...' : 'Request Revision'}
                  </button>
                  
                  <button
                    onClick={handleReject}
                    disabled={actionLoading}
                    className="w-full flex items-center justify-center gap-2 bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    <XCircleIcon className="w-5 h-5" />
                    {actionLoading ? 'Processing...' : 'Reject Deliverable'}
                  </button>
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">ℹ️ Review Guidelines</h4>
                  <ul className="text-sm text-blue-800 space-y-2">
                    <li>• <strong>Approve:</strong> Work meets requirements, payment release enabled</li>
                    <li>• <strong>Request Revision:</strong> Work needs changes, freelancer can resubmit</li>
                    <li>• <strong>Reject:</strong> Work doesn't meet requirements (final)</li>
                  </ul>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Status</h3>
                <p className="text-gray-600 text-sm">
                  {deliverable.status === 'APPROVED' && 
                    'This deliverable has been approved. You can now release payment.'}
                  {deliverable.status === 'REJECTED' && 
                    'This deliverable has been rejected.'}
                  {deliverable.status === 'DRAFT' && 
                    'This deliverable is still in draft status.'}
                  {deliverable.status === 'REVISION_REQUESTED' && 
                    'Revision has been requested. Waiting for freelancer to resubmit.'}
                </p>
                
                {deliverable.status === 'APPROVED' && (
                  <button
                    onClick={() => navigate(`/client/contracts/${deliverable.contract}`)}
                    className="w-full mt-4 bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    Go to Contract
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ClientDeliverableReviewPage
