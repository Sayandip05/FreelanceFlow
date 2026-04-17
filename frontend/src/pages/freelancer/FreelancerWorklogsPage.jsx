import { useState, useEffect } from 'react'
import { deliverableAPI, worklogAPI } from '../../api/worklogs'
import AIChatBox from '../../components/worklogs/AIChatBox'
import DeliverableCard from '../../components/worklogs/DeliverableCard'
import { PlusIcon, DocumentTextIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'

const FreelancerWorklogsPage = () => {
  const [contracts, setContracts] = useState([])
  const [selectedContract, setSelectedContract] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [worklogs, setWorklogs] = useState([])
  const [activeTab, setActiveTab] = useState('deliverables')
  const [showChat, setShowChat] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Fetch contracts on mount
  useEffect(() => {
    fetchContracts()
  }, [])

  // Fetch deliverables when contract changes
  useEffect(() => {
    if (selectedContract) {
      fetchDeliverables()
      fetchWorklogs()
    }
  }, [selectedContract])

  const fetchContracts = async () => {
    try {
      // This would be replaced with actual contracts API call
      // For now, using mock data
      setContracts([
        { id: 1, project: { title: 'E-commerce Website' }, client: { full_name: 'John Doe' } },
        { id: 2, project: { title: 'Mobile App Development' }, client: { full_name: 'Jane Smith' } },
      ])
      if (contracts.length > 0) {
        setSelectedContract(contracts[0])
      }
    } catch (error) {
      console.error('Failed to fetch contracts:', error)
    }
  }

  const fetchDeliverables = async () => {
    setIsLoading(true)
    try {
      const response = await deliverableAPI.getDeliverables(selectedContract.id)
      setDeliverables(response.data.results || [])
    } catch (error) {
      console.error('Failed to fetch deliverables:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchWorklogs = async () => {
    try {
      const response = await worklogAPI.getWorkLogs(selectedContract.id)
      setWorklogs(response.data.results || [])
    } catch (error) {
      console.error('Failed to fetch worklogs:', error)
    }
  }

  const handleDeliverableCreated = (newDeliverable) => {
    setDeliverables((prev) => [newDeliverable, ...prev])
    setShowChat(false)
    setActiveTab('deliverables')
  }

  const getStatusCounts = () => {
    return {
      draft: deliverables.filter((d) => d.status === 'DRAFT').length,
      pending: deliverables.filter((d) => d.status === 'SUBMITTED').length,
      approved: deliverables.filter((d) => d.status === 'APPROVED').length,
      total: deliverables.length,
    }
  }

  const counts = getStatusCounts()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">My Worklogs</h1>
              <p className="text-gray-600 mt-1">
                Track your work and submit deliverables for approval
              </p>
            </div>
            <button
              onClick={() => setShowChat(true)}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              New Deliverable
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Contract Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Contract
          </label>
          <select
            value={selectedContract?.id || ''}
            onChange={(e) => {
              const contract = contracts.find((c) => c.id === parseInt(e.target.value))
              setSelectedContract(contract)
            }}
            className="w-full max-w-md border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {contracts.map((contract) => (
              <option key={contract.id} value={contract.id}>
                {contract.project.title} - {contract.client.full_name}
              </option>
            ))}
          </select>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Total Deliverables</p>
            <p className="text-2xl font-bold text-gray-900">{counts.total}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Drafts</p>
            <p className="text-2xl font-bold text-yellow-600">{counts.draft}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Pending Review</p>
            <p className="text-2xl font-bold text-blue-600">{counts.pending}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Approved</p>
            <p className="text-2xl font-bold text-green-600">{counts.approved}</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Deliverables/Worklogs */}
          <div className="lg:col-span-2">
            {/* Tabs */}
            <div className="flex gap-4 mb-6 border-b border-gray-200">
              <button
                onClick={() => setActiveTab('deliverables')}
                className={`flex items-center gap-2 pb-3 text-sm font-medium transition-colors ${
                  activeTab === 'deliverables'
                    ? 'text-indigo-600 border-b-2 border-indigo-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <DocumentTextIcon className="w-5 h-5" />
                Deliverables ({deliverables.length})
              </button>
              <button
                onClick={() => setActiveTab('worklogs')}
                className={`flex items-center gap-2 pb-3 text-sm font-medium transition-colors ${
                  activeTab === 'worklogs'
                    ? 'text-indigo-600 border-b-2 border-indigo-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <ChatBubbleLeftRightIcon className="w-5 h-5" />
                Work Logs ({worklogs.length})
              </button>
            </div>

            {/* Content */}
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            ) : activeTab === 'deliverables' ? (
              <div className="space-y-4">
                {deliverables.length === 0 ? (
                  <div className="text-center py-12 bg-white rounded-lg shadow">
                    <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No deliverables yet
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Start by creating a new deliverable using the AI assistant
                    </p>
                    <button
                      onClick={() => setShowChat(true)}
                      className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      Create First Deliverable
                    </button>
                  </div>
                ) : (
                  deliverables.map((deliverable) => (
                    <DeliverableCard
                      key={deliverable.id}
                      deliverable={deliverable}
                      userRole="FREELANCER"
                      onStatusChange={fetchDeliverables}
                    />
                  ))
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {worklogs.length === 0 ? (
                  <div className="text-center py-12 bg-white rounded-lg shadow">
                    <p className="text-gray-600">No work logs yet</p>
                  </div>
                ) : (
                  worklogs.map((log) => (
                    <div
                      key={log.id}
                      className="bg-white rounded-lg shadow p-4 border-l-4 border-indigo-500"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-500">
                          {new Date(log.date).toLocaleDateString()}
                        </span>
                        <span className="text-sm font-medium text-indigo-600">
                          {log.hours_worked}h
                        </span>
                      </div>
                      <p className="text-gray-800">{log.description}</p>
                      {log.status === 'APPROVED' && (
                        <span className="inline-flex items-center gap-1 mt-2 text-xs text-green-600">
                          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                          Approved
                        </span>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Right Column - AI Chat */}
          <div className="lg:col-span-1">
            {showChat ? (
              <AIChatBox
                contractId={selectedContract?.id}
                projectName={selectedContract?.project?.title}
                onDeliverableCreated={handleDeliverableCreated}
              />
            ) : (
              <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6 text-center">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ChatBubbleLeftRightIcon className="w-8 h-8 text-indigo-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  AI Worklog Assistant
                </h3>
                <p className="text-gray-600 text-sm mb-4">
                  Chat with our AI to document your work. Just describe what you've done, 
                  upload screenshots, and the AI will generate a professional deliverable report.
                </p>
                <button
                  onClick={() => setShowChat(true)}
                  className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Start Chat
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FreelancerWorklogsPage
