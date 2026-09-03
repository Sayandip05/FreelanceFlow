import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, FileText, Briefcase, IndianRupee,
  MessageSquare, Clock, TrendingUp, ArrowUpRight, Calendar, CheckCircle,
  Wallet, ArrowDownRight, RefreshCw, AlertCircle, X, Download
} from 'lucide-react'
import { paymentsAPI } from '../../api/payments'
import { usersAPI } from '../../api/auth'
import { useNotifications } from '../../context/NotificationContext'
import { DashboardSkeleton } from '../../components/common/Skeleton'
import { formatCurrency } from '../../utils/formatCurrency'

const FreelancerEarningsPage = () => {
  const { notifications } = useNotifications() || { notifications: [] }
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [wallet, setWallet] = useState({ balance: '0.00', withdrawn_amount: '0.00', payout_linked: false })
  const [withdrawals, setWithdrawals] = useState([])
  const [showWithdrawModal, setShowWithdrawModal] = useState(false)
  const [showLinkModalOnly, setShowLinkModalOnly] = useState(false)
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawing, setWithdrawing] = useState(false)
  const [generatingId, setGeneratingId] = useState(null)
  const [withdrawError, setWithdrawError] = useState('')
  const [withdrawSuccess, setWithdrawSuccess] = useState('')

  // Bank Form State
  const [bankForm, setBankForm] = useState({
    account_holder_name: '',
    account_number: '',
    confirm_account: '',
    ifsc: ''
  })
  const [linking, setLinking] = useState(false)

  const fetchWalletAndPayments = async () => {
    try {
      const [paymentsRes, walletRes] = await Promise.all([
        paymentsAPI.getPayments(),
        paymentsAPI.getWallet()
      ])
      setPayments(paymentsRes.data?.results || paymentsRes.data || [])
      if (walletRes.data) {
        setWallet(walletRes.data.wallet)
        setWithdrawals(walletRes.data.withdrawals || [])
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWalletAndPayments()
  }, [])

  // Auto-refresh wallet when new notifications arrive (real-time websocket integration)
  useEffect(() => {
    if (notifications.length > 0) {
      fetchWalletAndPayments()
    }
  }, [notifications])

  const handleLinkBank = async (e) => {
    e.preventDefault()
    if (bankForm.account_number !== bankForm.confirm_account) {
      setWithdrawError('Account numbers do not match.')
      return
    }
    setLinking(true)
    setWithdrawError('')
    setWithdrawSuccess('')
    try {
      const res = await usersAPI.linkPayoutAccount({
        account_holder_name: bankForm.account_holder_name,
        account_number: bankForm.account_number,
        ifsc: bankForm.ifsc
      })
      setWithdrawSuccess('Bank account linked successfully!')
      setWallet(prev => ({
        ...prev,
        payout_linked: true,
        payout_bank_name: res.data.bank_name,
        payout_masked_account: res.data.masked_account,
        payout_account_holder: res.data.account_holder
      }))
      setTimeout(() => {
        setWithdrawSuccess('')
        setShowLinkModalOnly(false)
      }, 2000)
    } catch (err) {
      setWithdrawError(err.response?.data?.error || 'Failed to link bank account. Verify details and try again.')
    } finally {
      setLinking(false)
    }
  }

  const handleWithdraw = async (e) => {
    e.preventDefault()
    if (!withdrawAmount || parseFloat(withdrawAmount) <= 0) {
      setWithdrawError('Please enter a valid amount.')
      return
    }
    if (parseFloat(withdrawAmount) > parseFloat(wallet.balance)) {
      setWithdrawError('Amount exceeds available balance.')
      return
    }

    setWithdrawing(true)
    setWithdrawError('')
    setWithdrawSuccess('')
    try {
      await paymentsAPI.withdrawFunds(withdrawAmount)
      setWithdrawSuccess('Withdrawal initiated successfully!')
      setWithdrawAmount('')
      setTimeout(() => {
        setShowWithdrawModal(false)
        setWithdrawSuccess('')
      }, 2000)
      fetchWalletAndPayments()
    } catch (err) {
      setWithdrawError(err.response?.data?.error || 'Failed to initiate withdrawal.')
    } finally {
      setWithdrawing(false)
    }
  }

  const releasedPayments = payments.filter(p => p.status === 'RELEASED')
  const totalEarned = releasedPayments.reduce((s, p) => {
    const net = parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
    return s + net
  }, 0)
  const pendingAmount = payments
    .filter(p => p.status === 'ESCROWED')
    .reduce((s, p) => s + parseFloat(p.total_amount * 0.9 || 0), 0)

  // Monthly summary (simple grouping)
  const monthlyData = releasedPayments.reduce((acc, p) => {
    const month = new Date(p.created_at).toLocaleString('default', { month: 'long', year: 'numeric' })
    const net = parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
    acc[month] = (acc[month] || 0) + net
    return acc
  }, {})

  if (loading) {
    return (
      <div className="flex-1 p-8">
        <DashboardSkeleton />
      </div>
    )
  }

  return (
      <div className="flex-1 p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Wallet</h1>
            <p className="text-gray-600 mt-1">Your payment history, wallet balance and payout setup</p>
          </div>
          <button
            onClick={() => {
              setLoading(true)
              fetchWalletAndPayments()
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 border border-gray-200 rounded-xl hover:bg-gray-50 text-sm font-semibold text-gray-700 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Card 1 */}
          <div className="bg-blue-600 text-white rounded-2xl p-6 relative overflow-hidden shadow-md">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-blue-100 text-sm font-semibold">Total Earned (Net)</p>
                <h3 className="text-3xl font-bold mt-1">{formatCurrency(totalEarned)}</h3>
              </div>
              <div className="p-2 bg-white/10 rounded-lg">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
            </div>
            <p className="text-blue-100 text-xs font-semibold">{releasedPayments.length} payments received</p>
          </div>

          {/* Card 2 - Platform Wallet Balance */}
          <div className="bg-white border border-gray-100 rounded-2xl p-6 relative overflow-hidden shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-gray-500 text-sm font-semibold">Wallet Balance</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-1">{formatCurrency(wallet.balance)}</h3>
              </div>
              <div className="p-2 bg-blue-50 rounded-lg">
                <Wallet className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <button
              onClick={() => {
                setWithdrawError('')
                setWithdrawSuccess('')
                setShowWithdrawModal(true)
              }}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-xl text-xs transition-colors flex items-center justify-center gap-1.5"
            >
              Withdraw Funds
            </button>
          </div>

          {/* Card 3 */}
          <div className="bg-white border border-gray-100 rounded-2xl p-6 relative overflow-hidden shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-gray-500 text-sm font-semibold">Pending in Escrow</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-1">{formatCurrency(pendingAmount)}</h3>
              </div>
              <div className="p-2 bg-yellow-50 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
            </div>
            <p className="text-gray-400 text-xs font-semibold">Awaiting release</p>
          </div>

          {/* Card 4 */}
          <div className="bg-white border border-gray-100 rounded-2xl p-6 relative overflow-hidden shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-gray-500 text-sm font-semibold">Platform Fee</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-1">10%</h3>
              </div>
              <div className="p-2 bg-green-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <p className="text-gray-400 text-xs font-semibold">Deducted on payment release</p>
          </div>
        </div>

        {/* Content Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Area: Transaction History */}
          <div className="lg:col-span-2">
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-6">Transaction History</h3>
              {releasedPayments.length === 0 ? (
                <div className="text-center py-12">
                  <IndianRupee className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 font-semibold text-sm">No transaction history found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {releasedPayments.map(p => {
                    const net = parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
                    return (
                      <div key={p.id} className="flex items-center justify-between p-4 bg-gray-50/50 rounded-xl hover:bg-gray-50 transition-colors border border-gray-50">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center text-green-600">
                            <ArrowUpRight className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="font-bold text-gray-900 text-sm">Contract #{p.contract}</p>
                            <span className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                              <Calendar className="w-3 h-3" /> {new Date(p.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-green-600">+${net.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                          <span className="text-[10px] font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded">Received</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar: Monthly Summary & Withdrawal History */}
          <div className="space-y-6">
            {/* Payout Settings Card */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Wallet className="w-4 h-4 text-blue-600" /> Payout Settings
              </h3>
              {wallet.payout_linked ? (
                <div className="space-y-4">
                  <div className="p-3 bg-gray-50 border border-gray-100 rounded-xl flex items-center gap-2.5">
                    <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 flex-shrink-0 font-bold text-xs">
                      {wallet.payout_bank_name?.substring(0, 2).toUpperCase() || 'BK'}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-gray-900 truncate">{wallet.payout_bank_name || 'Linked Bank'}</p>
                      <p className="text-[10px] text-gray-500 font-semibold mt-0.5 truncate">Holder: {wallet.payout_account_holder}</p>
                      <p className="text-[10px] text-gray-500 font-semibold mt-0.5">Account: {wallet.payout_masked_account || '****'}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setWithdrawError('')
                      setWithdrawSuccess('')
                      setBankForm({
                        account_holder_name: wallet.payout_account_holder || '',
                        account_number: '',
                        confirm_account: '',
                        ifsc: ''
                      })
                      setShowLinkModalOnly(true)
                    }}
                    className="w-full bg-gray-50 hover:bg-gray-100 border border-gray-150 text-gray-700 font-bold py-2 rounded-xl text-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    Update Bank Account
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-gray-500 font-medium">Link your bank account to receive wallet withdrawals.</p>
                  <button
                    onClick={() => {
                      setWithdrawError('')
                      setWithdrawSuccess('')
                      setBankForm({
                        account_holder_name: '',
                        account_number: '',
                        confirm_account: '',
                        ifsc: ''
                      })
                      setShowLinkModalOnly(true)
                    }}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-xl text-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    Link Bank Account
                  </button>
                </div>
              )}
            </div>
            {/* Withdrawal History */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-gray-900 mb-4">Withdrawal History</h3>
              {withdrawals.length === 0 ? (
                <p className="text-xs text-gray-400 font-medium">No previous withdrawals</p>
              ) : (
                <div className="space-y-4">
                  {withdrawals.map(w => (
                    <div key={w.id} className="flex justify-between items-center text-xs font-semibold pb-3 border-b border-gray-50 last:border-b-0 last:pb-0">
                      <div className="flex items-center gap-3">
                        <button
                          className="p-1.5 border border-gray-150 hover:bg-gray-50 text-gray-500 hover:text-indigo-600 rounded-lg transition-colors flex-shrink-0 disabled:opacity-50 flex items-center justify-center"
                          title="Download Receipt"
                          disabled={generatingId === w.id}
                          onClick={async () => {
                            try {
                              setGeneratingId(w.id);
                              await paymentsAPI.generateReceipt(w.id, 'withdrawal');
                            } catch (err) {
                              alert('Failed to request receipt generation.');
                            } finally {
                              setGeneratingId(null);
                            }
                          }}
                        >
                          {generatingId === w.id ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-600" />
                          ) : (
                            <Download className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <div>
                          <p className="text-gray-900">Withdrawal #{w.id}</p>
                          <span className="text-[10px] text-gray-400 mt-0.5 block">{new Date(w.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-gray-900">{formatCurrency(w.amount)}</p>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          w.status === 'COMPLETED' ? 'bg-green-50 text-green-700' :
                          w.status === 'PENDING' ? 'bg-yellow-50 text-yellow-700' : 'bg-red-50 text-red-700'
                        }`}>
                          {w.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Withdrawal Modal */}
        {showWithdrawModal && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-md rounded-2xl p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
              <button
                onClick={() => setShowWithdrawModal(false)}
                className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>

              <h3 className="text-lg font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Wallet className="w-5 h-5 text-blue-600" /> Withdraw Funds
              </h3>
              
              <p className="text-sm text-gray-500 mb-6">
                {wallet.payout_linked 
                  ? `Transfer your available earnings to your linked account.` 
                  : `Please link your bank account details securely via RazorpayX to begin payouts.`
                }
              </p>

              {withdrawError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-semibold flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" /> {withdrawError}
                </div>
              )}

              {withdrawSuccess && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 animate-pulse">
                  <CheckCircle className="w-4 h-4 flex-shrink-0 animate-bounce" /> {withdrawSuccess}
                </div>
              )}

              {wallet.payout_linked ? (
                // ── AMOUNT WITHDRAWAL FORM ──
                <form onSubmit={handleWithdraw} className="space-y-4">
                  <div className="p-3 bg-gray-50 border border-gray-100 rounded-xl mb-2 flex items-center gap-2.5">
                    <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 flex-shrink-0 font-bold text-xs">
                      {wallet.payout_bank_name?.substring(0, 2).toUpperCase() || 'BK'}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-gray-900 truncate">{wallet.payout_bank_name || 'Linked Bank'}</p>
                      <p className="text-[10px] text-gray-500 font-semibold mt-0.5">Account: {wallet.payout_masked_account || '****'}</p>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-bold text-gray-700 mb-2">
                      <span>Amount to Withdraw (₹)</span>
                      <span className="text-gray-400">Available: {formatCurrency(wallet.balance)}</span>
                    </div>
                    <div className="relative">
                      <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 font-bold">₹</span>
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        max={wallet.balance}
                        value={withdrawAmount}
                        onChange={e => setWithdrawAmount(e.target.value)}
                        placeholder="0.00"
                        className="w-full pl-8 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                        required
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex gap-3">
                    <button
                      type="button"
                      onClick={() => setShowWithdrawModal(false)}
                      className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 font-bold text-sm py-2.5 rounded-xl transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={withdrawing || !withdrawAmount || parseFloat(withdrawAmount) <= 0 || parseFloat(withdrawAmount) > parseFloat(wallet.balance)}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white font-bold text-sm py-2.5 rounded-xl transition-colors flex items-center justify-center"
                    >
                      {withdrawing ? 'Processing...' : 'Confirm Withdrawal'}
                    </button>
                  </div>
                </form>
              ) : (
                // ── BANK ACCOUNT LINKING FORM ──
                <form onSubmit={handleLinkBank} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2">Account Holder Name</label>
                    <input
                      type="text"
                      value={bankForm.account_holder_name}
                      onChange={e => setBankForm({ ...bankForm, account_holder_name: e.target.value })}
                      placeholder="e.g. John Doe"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-gray-700 mb-2">Bank Account Number</label>
                      <input
                        type="password"
                        value={bankForm.account_number}
                        onChange={e => setBankForm({ ...bankForm, account_number: e.target.value })}
                        placeholder="••••••••••••"
                        className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-700 mb-2">Confirm Account Number</label>
                      <input
                        type="text"
                        value={bankForm.confirm_account}
                        onChange={e => setBankForm({ ...bankForm, confirm_account: e.target.value })}
                        placeholder="Confirm account number"
                        className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2">Bank IFSC Code</label>
                    <input
                      type="text"
                      value={bankForm.ifsc}
                      onChange={e => setBankForm({ ...bankForm, ifsc: e.target.value })}
                      placeholder="e.g. HDFC0000123"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900 uppercase"
                      required
                    />
                  </div>

                  <div className="pt-2 flex gap-3">
                    <button
                      type="button"
                      onClick={() => setShowWithdrawModal(false)}
                      className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 font-bold text-sm py-2.5 rounded-xl transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={linking}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white font-bold text-sm py-2.5 rounded-xl transition-colors flex items-center justify-center"
                    >
                      {linking ? 'Linking Account...' : 'Link Bank & Continue'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Standalone Link/Update Payout Bank Account Modal */}
        {showLinkModalOnly && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-md rounded-2xl p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
              <button
                onClick={() => setShowLinkModalOnly(false)}
                className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>

              <h3 className="text-lg font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Wallet className="w-5 h-5 text-blue-600" /> {wallet.payout_linked ? 'Update Bank Details' : 'Link Payout Account'}
              </h3>
              
              <p className="text-sm text-gray-500 mb-6">
                Fill in your bank account details below to receive direct wallet transfers securely.
              </p>

              {withdrawError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-semibold flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" /> {withdrawError}
                </div>
              )}

              {withdrawSuccess && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 animate-pulse">
                  <CheckCircle className="w-4 h-4 flex-shrink-0 animate-bounce" /> {withdrawSuccess}
                </div>
              )}

              <form onSubmit={handleLinkBank} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">Account Holder Name</label>
                  <input
                    type="text"
                    value={bankForm.account_holder_name}
                    onChange={e => setBankForm({ ...bankForm, account_holder_name: e.target.value })}
                    placeholder="e.g. John Doe"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2">Bank Account Number</label>
                    <input
                      type="password"
                      value={bankForm.account_number}
                      onChange={e => setBankForm({ ...bankForm, account_number: e.target.value })}
                      placeholder="••••••••••••"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2">Confirm Account Number</label>
                    <input
                      type="text"
                      value={bankForm.confirm_account}
                      onChange={e => setBankForm({ ...bankForm, confirm_account: e.target.value })}
                      placeholder="Confirm account number"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">Bank IFSC Code</label>
                  <input
                    type="text"
                    value={bankForm.ifsc}
                    onChange={e => setBankForm({ ...bankForm, ifsc: e.target.value })}
                    placeholder="e.g. HDFC0000123"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-gray-50 focus:bg-white transition-all text-gray-900 uppercase"
                    required
                  />
                </div>

                <div className="pt-2 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setShowLinkModalOnly(false)}
                    className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 font-bold text-sm py-2.5 rounded-xl transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={linking}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white font-bold text-sm py-2.5 rounded-xl transition-colors flex items-center justify-center"
                  >
                    {linking ? 'Linking Account...' : 'Link Bank Details'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
  )
}

export default FreelancerEarningsPage
