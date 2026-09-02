import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, FileText, Briefcase, DollarSign,
  MessageSquare, Clock, CheckCircle, XCircle, AlertCircle
} from 'lucide-react'
import { bidsAPI } from '../../api/bids'

const STATUS_CONFIG = {
  PENDING: { label: 'Pending', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  ACCEPTED: { label: 'Accepted', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: 'bg-red-100 text-red-600', icon: XCircle },
  WITHDRAWN: { label: 'Withdrawn', color: 'bg-gray-100 text-gray-600', icon: AlertCircle },
}

const FreelancerBidsPage = () => {
  const navigate = useNavigate()
  const [bids, setBids] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('ALL')

  useEffect(() => {
    const fetchBids = async () => {
      try {
        const res = await bidsAPI.getMyBids()
        setBids(res.data?.results || res.data || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchBids()
  }, [])

  const handleWithdraw = async (bidId) => {
    try {
      await bidsAPI.withdrawBid(bidId)
      setBids(prev => prev.filter(b => b.id !== bidId))
    } catch (e) {
      console.error(e)
    }
  }

  const tabs = ['ALL', 'PENDING', 'ACCEPTED', 'REJECTED']
  const filtered = activeTab === 'ALL' ? bids : bids.filter(b => b.status === activeTab)

  const counts = {
    ALL: bids.length,
    PENDING: bids.filter(b => b.status === 'PENDING').length,
    ACCEPTED: bids.filter(b => b.status === 'ACCEPTED').length,
    REJECTED: bids.filter(b => b.status === 'REJECTED').length,
  }

  return (

    <div className="flex-1 p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Bids</h1>
          <p className="text-gray-600 mt-1">Track all your submitted proposals</p>
        </div>
        <button onClick={() => navigate('/freelancer/browse')} className="btn-primary flex items-center gap-2 rounded-none">
          <Search className="w-4 h-4" /> Browse Projects
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-none p-1 mb-6 w-fit">
        {tabs.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-none text-sm font-medium transition-all ${activeTab === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}>
            {tab === 'ALL' ? 'All' : tab.charAt(0) + tab.slice(1).toLowerCase()} ({counts[tab]})
          </button>
        ))}
      </div>

      {/* Bids */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-32 bg-gray-100 rounded-none animate-pulse" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-none border border-gray-100">
          <FileText className="w-14 h-14 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No {activeTab !== 'ALL' ? activeTab.toLowerCase() : ''} bids</h3>
          <p className="text-gray-500">Start bidding on projects to see them here</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(bid => {
            const config = STATUS_CONFIG[bid.status] || STATUS_CONFIG.PENDING
            const StatusIcon = config.icon
            return (
              <div key={bid.id} className="bg-white rounded-none border border-gray-200 p-6 shadow-sm">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{bid.project?.title || `Project #${bid.project}`}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      Submitted {new Date(bid.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2.5 py-1 rounded-none font-medium flex items-center gap-1 ${config.color}`}>
                      <StatusIcon className="w-3.5 h-3.5" /> {config.label}
                    </span>
                    <span className="text-lg font-bold text-gray-900">${bid.amount}</span>
                  </div>
                </div>
                {bid.cover_letter && (
                  <p className="text-sm text-gray-600 bg-gray-50 rounded-none p-3 mb-4 line-clamp-2">{bid.cover_letter}</p>
                )}
                <div className="flex items-center gap-3">
                  {bid.status === 'ACCEPTED' && (
                    <button onClick={() => navigate(`/freelancer/contracts/${bid.contract_id}`)}
                      className="btn-primary text-sm px-4 py-2 rounded-none">
                      View Contract →
                    </button>
                  )}
                  {bid.status === 'PENDING' && (
                    <button onClick={() => handleWithdraw(bid.id)}
                      className="text-sm text-red-600 hover:text-red-700 font-medium px-3 py-1.5 rounded-none hover:bg-red-50 transition-colors">
                      Withdraw Bid
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default FreelancerBidsPage
