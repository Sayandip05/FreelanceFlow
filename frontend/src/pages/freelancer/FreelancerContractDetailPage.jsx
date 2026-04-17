import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { contractsAPI } from '../../api/bids'
import { deliverableAPI } from '../../api/worklogs'
import { paymentsAPI } from '../../api/payments'
import DeliverableCard from '../../components/worklogs/DeliverableCard'
import { 
  BanknotesIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  CheckCircleIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline'
import { formatDate } from '../../utils/formatDate'
import { formatCurrency } from '../../utils/formatCurrency'

const FreelancerContractDetailPage = () => {
  const { contractId } = useParams()
  const navigate = useNavigate()
  const [contract, setContract] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [payment, setPayment] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchContractData()
    fetchDeliverables()
    fetchPaymentStatus()
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

  const fetchPaymentStatus = async () => {
    try {
      const response = await paymentsAPI.getPaymentByContract(contractId)
      setPayment(response.data)
    } catch (error) {
      // Payment might not exist yet
      console.log('No payment found for contract')
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

  const approvedDeliverables = deliverables.filter(d => d.status === 'APPROVED')
  const pendingDeliverables = deliverables.filter(d => d.status === 'SUBMITTED' || d.status === 'UNDER_REVIEW')
  const totalHoursLogged = deliverables.reduce((sum, d) => sum + parseFloat(d.hours_logged || 0), 0)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <button
            onClick={() => navigate('/freelancer/contracts')}
            className="text-sm text-indigo-600 hover:text-indigo-800 mb-2"
          >
            ← Back to Contracts
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {contract.bid.project.title}
              </h1>
              <p className="text-gray-600 mt-1">
                Contract with {contract.bid.project.client.first_name} {contract.bid.project.client.last_name}
              </p>
            </div>
            <div>
              <span
                className={`px-4 py-2 rounded-full text-sm font-medium ${
                  contract.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {contract.is_active ? 'Active' : 'Completed'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-100 rounded-lg">
                <CurrencyDollarIcon className="w-6 h-6 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Contract Amount</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(contract.agreed_amount)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircleIcon className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Approved</p>
                <p className="text-2xl font-bold text-gray-900">
                  {approvedDeliverables.length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <ClockIcon className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Pending Review</p>
                <p className="text-2xl font-bold text-gray-900">
                  {pendingDeliverables.length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-100 rounded-lg">
                <ClockIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Hours Logged</p>
                <p className="text-2xl font-bold text-gray-900">
                  {totalHoursLogged.toFixed(1)}h
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Actions */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg shadow-lg p-6 text-white">
              <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => navigate(`/freelancer/contracts/${contractId}/work`)}
                  className="bg-white text-indigo-600 py-3 px-4 rounded-lg hover:bg-indigo-50 transition-colors font-medium flex items-center justify-center gap-2"
                >
                  <DocumentTextIcon className="w-5 h-5" />
                  Document Work
                </button>
                <button
                  onClick={() => navigate(`/freelancer/messages?contract=${contractId}`)}
                  className="bg-white bg-opacity-20 text-white py-3 px-4 rounded-lg hover:bg-opacity-30 transition-colors font-medium flex items-center justify-center gap-2 backdrop-blur-sm"
                >
                  <ChatBubbleLeftRightIcon className="w-5 h-5" />
                  Message Client
                </button>
              </div>
            </div>

            {/* Deliverables */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Deliverables</h2>
                <button
                  onClick={() => navigate(`/freelancer/contracts/${contractId}/work`)}
                  className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  + Create New
                </button>
              </div>

              {deliverables.length === 0 ? (
                <div className="text-center py-12">
                  <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Deliverables Yet
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Start documenting your work with our AI assistant
                  </p>
                  <button
                    onClick={() => navigate(`/freelancer/contracts/${contractId}/work`)}
                    className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    Create First Deliverable
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {deliverables.map((deliverable) => (
                    <DeliverableCard
                      key={deliverable.id}
                      deliverable={deliverable}
                      onView={() => navigate(`/freelancer/deliverables/${deliverable.id}`)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Payment Status */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <BanknotesIcon className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold text-gray-900">Payment Status</h3>
              </div>
              
              {payment ? (
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Status:</span>
                    <span
                      className={`font-medium ${
                        payment.status === 'RELEASED'
                          ? 'text-green-600'
                          : payment.status === 'ESCROWED'
                          ? 'text-blue-600'
                          : 'text-yellow-600'
                      }`}
                    >
                      {payment.status}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Total Amount:</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(payment.total_amount)}
                    </span>
                  </div>
                  {payment.status === 'RELEASED' && (
                    <>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Platform Fee (10%):</span>
                        <span className="font-medium text-gray-900">
                          -{formatCurrency(payment.total_amount * 0.1)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm pt-2 border-t border-gray-200">
                        <span className="text-gray-900 font-semibold">You Receive:</span>
                        <span className="font-bold text-green-600">
                          {formatCurrency(payment.total_amount * 0.9)}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-600">
                  Waiting for client to fund escrow
                </p>
              )}
            </div>

            {/* Contract Details */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Contract Details</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-600">Started:</span>
                  <p className="font-medium text-gray-900">
                    {formatDate(contract.start_date)}
                  </p>
                </div>
                {contract.end_date && (
                  <div>
                    <span className="text-gray-600">Completed:</span>
                    <p className="font-medium text-gray-900">
                      {formatDate(contract.end_date)}
                    </p>
                  </div>
                )}
                <div>
                  <span className="text-gray-600">Project Budget:</span>
                  <p className="font-medium text-gray-900">
                    {formatCurrency(contract.bid.project.budget)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Your Bid:</span>
                  <p className="font-medium text-gray-900">
                    {formatCurrency(contract.bid.amount)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Agreed Amount:</span>
                  <p className="font-bold text-indigo-600">
                    {formatCurrency(contract.agreed_amount)}
                  </p>
                </div>
              </div>
            </div>

            {/* Project Description */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Project Description</h3>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {contract.bid.project.description}
              </p>
            </div>

            {/* Client Info */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Client</h3>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                  <span className="text-indigo-600 font-semibold text-lg">
                    {contract.bid.project.client.first_name[0]}
                    {contract.bid.project.client.last_name[0]}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {contract.bid.project.client.first_name} {contract.bid.project.client.last_name}
                  </p>
                  <p className="text-sm text-gray-600">
                    {contract.bid.project.client.email}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FreelancerContractDetailPage
