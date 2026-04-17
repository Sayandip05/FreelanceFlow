import { useState, useEffect } from 'react'
import { deliverableAPI } from '../../api/worklogs'
import DeliverableCard from '../../components/worklogs/DeliverableCard'
import { ClipboardDocumentListIcon, CheckCircleIcon, ClockIcon } from '@heroicons/react/24/outline'

const ClientReviewPage = () => {
  const [deliverables, setDeliverables] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState('pending')

  useEffect(() => {
    fetchDeliverables()
  }, [filter])

  const fetchDeliverables = async () => {
    setIsLoading(true)
    try {
      const statusMap = {
        pending: 'SUBMITTED',
        approved: 'APPROVED',
        all: null,
      }
      const response = await deliverableAPI.getDeliverables(null, statusMap[filter])
      setDeliverables(response.data.results || [])
    } catch (error) {
      console.error('Failed to fetch deliverables:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStats = () => {
    const pending = deliverables.filter((d) => d.status === 'SUBMITTED').length
    const approved = deliverables.filter((d) => d.status === 'APPROVED').length
    const totalHours = deliverables
      .filter((d) => d.status === 'APPROVED')
      .reduce((sum, d) => sum + parseFloat(d.hours_logged || 0), 0)
    return { pending, approved, totalHours }
  }

  const stats = getStats()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Review Deliverables</h1>
          <p className="text-gray-600 mt-1">
            Review and approve work submitted by your freelancers
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
              <ClockIcon className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Pending Review</p>
              <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircleIcon className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Approved</p>
              <p className="text-2xl font-bold text-gray-900">{stats.approved}</p>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
              <ClipboardDocumentListIcon className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Hours Approved</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalHours}h</p>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setFilter('pending')}
            className={`pb-3 text-sm font-medium transition-colors ${
              filter === 'pending'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Pending Review
          </button>
          <button
            onClick={() => setFilter('approved')}
            className={`pb-3 text-sm font-medium transition-colors ${
              filter === 'approved'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Approved
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`pb-3 text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            All Deliverables
          </button>
        </div>

        {/* Deliverables List */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : deliverables.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <ClipboardDocumentListIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No deliverables to review
            </h3>
            <p className="text-gray-600">
              {filter === 'pending'
                ? 'You have no pending deliverables to review'
                : filter === 'approved'
                ? 'No approved deliverables yet'
                : 'No deliverables found'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {deliverables.map((deliverable) => (
              <DeliverableCard
                key={deliverable.id}
                deliverable={deliverable}
                userRole="CLIENT"
                onStatusChange={fetchDeliverables}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ClientReviewPage
