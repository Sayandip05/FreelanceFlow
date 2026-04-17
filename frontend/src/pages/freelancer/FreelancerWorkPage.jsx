import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { contractsAPI } from '../../api/bids'
import { deliverableAPI } from '../../api/worklogs'
import AIChatBox from '../../components/worklogs/AIChatBox'
import DeliverableCard from '../../components/worklogs/DeliverableCard'
import { 
  DocumentTextIcon, 
  ChatBubbleLeftRightIcon,
  ClockIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'

const FreelancerWorkPage = () => {
  const { contractId } = useParams()
  const navigate = useNavigate()
  const [contract, setContract] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('chat') // 'chat' or 'deliverables'

  useEffect(() => {
    fetchContractData()
    fetchDeliverables()
  }, [contractId])

  const fetchContractData = async () => {
    try {
      const response = await contractsAPI.getContractDetail(contractId)
      setContract(response.data)
    } catch (error) {
      console.error('Error fetching contract:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchDeliverables = async () => {
    try {
      const response = await deliverableAPI.getDeliverables(contractId)
      setDeliverables(response.data)
    } catch (error) {
      console.error('Error fetching deliverables:', error)
    }
  }

  const handleDeliverableCreated = (newDeliverable) => {
    setDeliverables((prev) => [newDeliverable, ...prev])
    setActiveTab('deliverables')
  }

  const handleDeliverableSubmit = async (deliverableId) => {
    try {
      await deliverableAPI.submitDeliverable(deliverableId)
      fetchDeliverables()
    } catch (error) {
      console.error('Error submitting deliverable:', error)
      alert('Failed to submit deliverable')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Contract not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => navigate(`/freelancer/contracts/${contractId}`)}
                className="text-sm text-indigo-600 hover:text-indigo-800 mb-2"
              >
                ← Back to Contract
              </button>
              <h1 className="text-3xl font-bold text-gray-900">
                Document Your Work
              </h1>
              <p className="text-gray-600 mt-1">
                {contract.bid.project.title}
              </p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <ClockIcon className="w-5 h-5" />
                <span>Contract Amount: ${contract.agreed_amount}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-green-600 mt-1">
                <CheckCircleIcon className="w-5 h-5" />
                <span>{deliverables.filter(d => d.status === 'APPROVED').length} Approved Deliverables</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'chat'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <ChatBubbleLeftRightIcon className="w-5 h-5" />
                AI Chat Assistant
              </div>
            </button>
            <button
              onClick={() => setActiveTab('deliverables')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'deliverables'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <DocumentTextIcon className="w-5 h-5" />
                My Deliverables ({deliverables.length})
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'chat' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* AI Chat - Main Column */}
            <div className="lg:col-span-2">
              <AIChatBox
                contractId={contractId}
                projectName={contract.bid.project.title}
                onDeliverableCreated={handleDeliverableCreated}
              />
            </div>

            {/* Instructions - Sidebar */}
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  How It Works
                </h3>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-semibold">
                      1
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Describe Your Work</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Tell the AI what you've been working on in natural language
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-semibold">
                      2
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Answer Questions</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        The AI will ask clarifying questions to understand your work better
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-semibold">
                      3
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Upload Proof</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Attach screenshots or files to support your work
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center font-semibold">
                      4
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Generate Report</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        AI creates a professional deliverable report for client review
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">💡 Pro Tips</h4>
                <ul className="text-sm text-blue-800 space-y-2">
                  <li>• Be specific about what you accomplished</li>
                  <li>• Mention any challenges you overcame</li>
                  <li>• Include technical details when relevant</li>
                  <li>• Upload screenshots as proof of work</li>
                </ul>
              </div>

              {deliverables.length > 0 && (
                <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Recent Deliverables</h4>
                  <div className="space-y-2">
                    {deliverables.slice(0, 3).map((deliverable) => (
                      <div
                        key={deliverable.id}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="text-gray-700 truncate">
                          {deliverable.title}
                        </span>
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            deliverable.status === 'APPROVED'
                              ? 'bg-green-100 text-green-800'
                              : deliverable.status === 'SUBMITTED'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {deliverable.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'deliverables' && (
          <div className="space-y-6">
            {deliverables.length === 0 ? (
              <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center">
                <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Deliverables Yet
                </h3>
                <p className="text-gray-600 mb-6">
                  Start by chatting with the AI assistant to create your first deliverable
                </p>
                <button
                  onClick={() => setActiveTab('chat')}
                  className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Start AI Chat
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6">
                {deliverables.map((deliverable) => (
                  <DeliverableCard
                    key={deliverable.id}
                    deliverable={deliverable}
                    onSubmit={handleDeliverableSubmit}
                    onView={() => navigate(`/freelancer/deliverables/${deliverable.id}`)}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default FreelancerWorkPage
