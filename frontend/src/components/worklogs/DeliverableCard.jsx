import { useState } from 'react'
import { deliverableAPI } from '../../api/worklogs'
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon, 
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

const statusConfig = {
  DRAFT: { color: 'bg-gray-100 text-gray-800', icon: DocumentTextIcon, label: 'Draft' },
  SUBMITTED: { color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon, label: 'Pending Review' },
  UNDER_REVIEW: { color: 'bg-blue-100 text-blue-800', icon: ChatBubbleLeftRightIcon, label: 'Under Review' },
  APPROVED: { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon, label: 'Approved' },
  REJECTED: { color: 'bg-red-100 text-red-800', icon: XCircleIcon, label: 'Rejected' },
  REVISION_REQUESTED: { color: 'bg-orange-100 text-orange-800', icon: ArrowPathIcon, label: 'Revision Requested' },
}

const DeliverableCard = ({ deliverable, userRole, onStatusChange }) => {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [action, setAction] = useState(null)

  const status = statusConfig[deliverable.status] || statusConfig.DRAFT
  const StatusIcon = status.icon

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      await deliverableAPI.submitDeliverable(deliverable.id)
      onStatusChange?.()
    } catch (error) {
      alert('Failed to submit deliverable')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleApprove = async () => {
    setIsSubmitting(true)
    try {
      await deliverableAPI.approveDeliverable(deliverable.id, feedback)
      setShowFeedbackModal(false)
      onStatusChange?.()
    } catch (error) {
      alert('Failed to approve deliverable')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReject = async (requestRevision = true) => {
    if (!feedback.trim()) {
      alert('Please provide feedback')
      return
    }
    setIsSubmitting(true)
    try {
      await deliverableAPI.rejectDeliverable(deliverable.id, feedback, requestRevision)
      setShowFeedbackModal(false)
      setFeedback('')
      onStatusChange?.()
    } catch (error) {
      alert('Failed to reject deliverable')
    } finally {
      setIsSubmitting(false)
    }
  }

  const openFeedbackModal = (actionType) => {
    setAction(actionType)
    setShowFeedbackModal(true)
  }

  const parseAIReport = () => {
    try {
      return JSON.parse(deliverable.ai_generated_report)
    } catch {
      return null
    }
  }

  const aiReport = parseAIReport()

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
            <StatusIcon className="w-4 h-4" />
            {status.label}
          </span>
          <h3 className="font-semibold text-gray-900">{deliverable.title}</h3>
        </div>
        <span className="text-sm text-gray-500">
          {deliverable.hours_logged}h logged
        </span>
      </div>

      {/* Content */}
      <div className="p-4">
        <p className="text-gray-700 text-sm mb-4">{deliverable.description}</p>

        {/* AI Report Summary */}
        {aiReport && (
          <div className="bg-indigo-50 rounded-lg p-3 mb-4">
            <h4 className="text-indigo-900 font-medium text-sm mb-2">AI Summary</h4>
            <div className="space-y-1 text-sm text-indigo-800">
              {aiReport.tasks_completed?.length > 0 && (
                <div>
                  <span className="font-medium">Tasks:</span>
                  <ul className="list-disc list-inside ml-2">
                    {aiReport.tasks_completed.map((task, i) => (
                      <li key={i}>{task}</li>
                    ))}
                  </ul>
                </div>
              )}
              {aiReport.technologies_used?.length > 0 && (
                <div>
                  <span className="font-medium">Technologies:</span>{' '}
                  {aiReport.technologies_used.join(', ')}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Attached Files */}
        {deliverable.attached_files?.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Attached Files</h4>
            <div className="flex flex-wrap gap-2">
              {deliverable.attached_files.map((file, index) => (
                <a
                  key={index}
                  href={file}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm text-gray-700 transition-colors"
                >
                  <DocumentTextIcon className="w-4 h-4" />
                  File {index + 1}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Client Feedback */}
        {deliverable.client_feedback && (
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <h4 className="text-gray-700 font-medium text-sm mb-1">Client Feedback</h4>
            <p className="text-gray-600 text-sm">{deliverable.client_feedback}</p>
          </div>
        )}

        {/* Timestamps */}
        <div className="text-xs text-gray-400 space-y-1">
          {deliverable.submitted_at && (
            <p>Submitted: {new Date(deliverable.submitted_at).toLocaleString()}</p>
          )}
          {deliverable.reviewed_at && (
            <p>Reviewed: {new Date(deliverable.reviewed_at).toLocaleString()}</p>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
        {userRole === 'FREELANCER' && deliverable.status === 'DRAFT' && (
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50"
          >
            {isSubmitting ? 'Submitting...' : 'Submit for Review'}
          </button>
        )}

        {userRole === 'FREELANCER' && deliverable.status === 'REVISION_REQUESTED' && (
          <div className="flex gap-2">
            <button
              onClick={() => onStatusChange?.('edit')}
              className="flex-1 bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
            >
              Edit & Resubmit
            </button>
          </div>
        )}

        {userRole === 'CLIENT' && deliverable.status === 'SUBMITTED' && (
          <div className="flex gap-2">
            <button
              onClick={() => openFeedbackModal('approve')}
              disabled={isSubmitting}
              className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50"
            >
              Approve
            </button>
            <button
              onClick={() => openFeedbackModal('revision')}
              disabled={isSubmitting}
              className="flex-1 bg-orange-600 text-white py-2 rounded-lg hover:bg-orange-700 transition-colors font-medium disabled:opacity-50"
            >
              Request Changes
            </button>
            <button
              onClick={() => openFeedbackModal('reject')}
              disabled={isSubmitting}
              className="px-4 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        )}
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold mb-4">
              {action === 'approve' ? 'Approve Deliverable' : 
               action === 'revision' ? 'Request Revision' : 'Reject Deliverable'}
            </h3>
            
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder={
                action === 'approve' 
                  ? 'Optional feedback for the freelancer...' 
                  : 'Provide feedback on what needs to be changed...'
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={4}
            />
            
            <div className="flex gap-2">
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (action === 'approve') handleApprove()
                  else if (action === 'revision') handleReject(true)
                  else handleReject(false)
                }}
                disabled={isSubmitting || (action !== 'approve' && !feedback.trim())}
                className={`flex-1 py-2 rounded-lg transition-colors font-medium disabled:opacity-50 ${
                  action === 'approve' 
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : action === 'revision'
                    ? 'bg-orange-600 text-white hover:bg-orange-700'
                    : 'bg-red-600 text-white hover:bg-red-700'
                }`}
              >
                {isSubmitting ? 'Processing...' : 
                 action === 'approve' ? 'Approve' : 
                 action === 'revision' ? 'Request Revision' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DeliverableCard
