import React, { useState, useEffect } from 'react'
import { Wallet, Plus, ArrowUpRight, ArrowDownLeft, Download, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react'
import { paymentsAPI } from '../../api/payments'
import { useAuth } from '../../context/AuthContext'
import { formatCurrency } from '../../utils/formatCurrency'
import { DashboardSkeleton } from '../../components/common/Skeleton'

export default function ClientWalletPage() {
  const { user } = useAuth()
  const [balance, setBalance] = useState(0.0)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [showLoadModal, setShowLoadModal] = useState(false)
  const [loadAmount, setLoadAmount] = useState('')
  const [processing, setProcessing] = useState(false)
  const [generatingId, setGeneratingId] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const fetchWalletDetails = async () => {
    try {
      const res = await paymentsAPI.getClientWallet()
      setBalance(res.data.balance)
      setHistory(res.data.history)
    } catch (err) {
      console.error(err)
      setError('Failed to load wallet details.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWalletDetails()
  }, [])

  const handleAddFunds = async (e) => {
    e.preventDefault()
    if (!loadAmount || parseFloat(loadAmount) <= 0) {
      setError('Please enter a valid amount.')
      return
    }

    setProcessing(true)
    setError('')
    setSuccess('')

    try {
      const res = await paymentsAPI.depositClientWallet(loadAmount)
      const { order_id, is_mock, amount } = res.data

      if (is_mock) {
        // Direct simulated success path
        await paymentsAPI.confirmClientDeposit(order_id, `pay_mock_${Math.random().toString(36).substr(2, 9)}`)
        setSuccess(`Successfully loaded ${formatCurrency(loadAmount)} to your wallet (Simulation)!`)
        setLoadAmount('')
        setShowLoadModal(false)
        fetchWalletDetails()
      } else {
        // Razorpay checkout modal path
        const options = {
          key: import.meta.env.VITE_RAZORPAY_KEY_ID || 'rzp_test_TSUnxYrEPrLAdv',
          amount: Math.round(amount * 100),
          currency: 'INR',
          name: 'FreelanceFlow',
          description: 'Wallet Pre-funding deposit',
          order_id: order_id,
          handler: async (response) => {
            try {
              await paymentsAPI.confirmClientDeposit(order_id, response.razorpay_payment_id)
              setSuccess('Funds loaded successfully!')
              setLoadAmount('')
              setShowLoadModal(false)
              fetchWalletDetails()
            } catch (err) {
              setError('Failed to confirm transaction. Please contact support.')
            }
          },
          prefill: {
            name: user?.get_full_name || user?.email,
            email: user?.email,
          },
          theme: {
            color: '#4f46e5',
          },
          modal: {
            ondismiss: () => {
              setProcessing(false)
            }
          }
        }
        const rzp = new window.Razorpay(options)
        rzp.open()
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to initiate deposit.')
    } finally {
      setProcessing(false)
    }
  }

  const handleDownloadReceipt = async (id, type) => {
    try {
      setGeneratingId(id);
      await paymentsAPI.generateReceipt(id, type);
    } catch (err) {
      alert('Failed to request receipt generation.');
      console.error(err);
    } finally {
      setGeneratingId(null);
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-4">
        <DashboardSkeleton />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-200">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">My Platform Wallet</h1>
          <p className="text-xs font-semibold text-gray-500 mt-1">Pre-fund milestones, track deposits, and download tax invoices.</p>
        </div>
        <button
          onClick={() => {
            setError('')
            setSuccess('')
            setShowLoadModal(true)
          }}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm px-4 py-2.5 rounded-xl transition-colors flex items-center gap-2 shadow-sm"
        >
          <Plus className="w-4 h-4" /> Add Funds
        </button>
      </div>

      {success && (
        <div className="p-3 bg-green-50 border border-green-200 text-green-700 rounded-xl text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> {success}
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-semibold flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
        </div>
      )}

      {/* Main Balance Card */}
      <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-indigo-900 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 bottom-0 translate-y-1/4 translate-x-1/4 opacity-10">
          <Wallet className="w-96 h-96" />
        </div>
        <div className="relative z-10 space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-200">Available Pre-funded Balance</span>
          <h2 className="text-4xl font-black">{formatCurrency(balance)}</h2>
          <div className="pt-2 flex items-center gap-2 text-xs font-semibold text-indigo-200 bg-white/5 border border-white/10 rounded-xl px-4 py-3 max-w-md">
            <AlertCircle className="w-4.5 h-4.5 text-indigo-300 flex-shrink-0" />
            <span>Pre-funded balances let you lock milestone payouts instantly without re-entering bank details during checkout.</span>
          </div>
        </div>
      </div>

      {/* Transaction History Section */}
      <div className="bg-white border border-gray-100 rounded-3xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-50 flex justify-between items-center">
          <h3 className="text-sm font-bold text-gray-900">Transaction History</h3>
          <span className="text-[10px] bg-gray-50 border border-gray-100 rounded-full px-2.5 py-1 text-gray-500 font-bold uppercase tracking-wider">Deposits & Escrow Payments</span>
        </div>

        <div className="divide-y divide-gray-50">
          {history.length === 0 ? (
            <div className="p-8 text-center text-gray-400 font-medium text-xs">
              No transactions recorded in your platform wallet.
            </div>
          ) : (
            history.map((tx) => (
              <div key={`${tx.type}-${tx.id}`} className="p-5 flex justify-between items-center hover:bg-gray-50/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    tx.type === 'DEPOSIT' ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600'
                  }`}>
                    {tx.type === 'DEPOSIT' ? <ArrowUpRight className="w-5 h-5" /> : <ArrowDownLeft className="w-5 h-5" />}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-gray-900">{tx.description}</p>
                    <span className="text-[10px] text-gray-400 font-semibold mt-0.5 block">
                      {new Date(tx.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div>
                    <p className={`text-sm font-bold ${tx.type === 'DEPOSIT' ? 'text-green-600' : 'text-gray-900'}`}>
                      {tx.type === 'DEPOSIT' ? '+' : '-'}{formatCurrency(tx.amount)}
                    </p>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold mt-1 inline-block ${
                      tx.status === 'COMPLETED' ? 'bg-green-50 text-green-700' :
                      tx.status === 'PENDING' ? 'bg-yellow-50 text-yellow-700' : 'bg-red-50 text-red-700'
                    }`}>
                      {tx.status}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDownloadReceipt(tx.id, tx.type)}
                    disabled={generatingId === tx.id}
                    className="p-2 border border-gray-150 hover:bg-gray-50 text-gray-500 hover:text-gray-700 rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center"
                    title="Download PDF Invoice"
                  >
                    {generatingId === tx.id ? (
                      <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Funds Modal */}
      {showLoadModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-md rounded-3xl p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-base font-extrabold text-gray-900 mb-2 flex items-center gap-2">
              <Plus className="w-5 h-5 text-indigo-600" /> Add Funds to Wallet
            </h3>
            <p className="text-xs text-gray-500 mb-6 font-semibold">Enter the amount in INR (₹) you wish to add to your pre-funded platform balance.</p>
            
            <form onSubmit={handleAddFunds} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-2">Deposit Amount (₹)</label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 font-bold">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    min="1.00"
                    value={loadAmount}
                    onChange={e => setLoadAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full pl-8 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                    required
                  />
                </div>
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowLoadModal(false)}
                  className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 font-bold text-sm py-2.5 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={processing || !loadAmount || parseFloat(loadAmount) <= 0}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white font-bold text-sm py-2.5 rounded-xl transition-colors flex items-center justify-center gap-1.5"
                >
                  {processing ? 'Processing...' : 'Load Funds'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
