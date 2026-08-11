import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, FileText, Briefcase, DollarSign,
  MessageSquare, TrendingUp, Clock, CheckCircle, ArrowRight,
  ArrowUpRight, Calendar, ShieldCheck, User, Edit3, MapPin, Wrench, Globe, X,
  Camera, Image as ImageIcon, Upload, Trash2
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { bidsAPI, contractsAPI } from '../../api/bids'
import { paymentsAPI } from '../../api/payments'
import { usersAPI } from '../../api/auth'

const StatCard = ({ icon: Icon, label, value, subtext, color, bg }) => (
  <div className="bg-white rounded-2xl border border-gray-100 p-6 flex items-center gap-4 shadow-sm">
    <div className={`w-12 h-12 ${bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
      <Icon className={`w-6 h-6 ${color}`} />
    </div>
    <div>
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-2xl font-extrabold text-gray-900 mt-0.5">{value}</p>
      {subtext && <p className="text-xs text-gray-400 mt-0.5">{subtext}</p>}
    </div>
  </div>
)

/* ── Edit Profile Modal Component ────────────────────────────────────────── */
const EditProfileModal = ({ onClose, onSaveSuccess }) => {
  const { user, setUser, fetchUser } = useAuth()
  const profile = user?.freelancer_profile || {}

  const [firstName, setFirstName] = useState(user?.first_name || '')
  const [lastName, setLastName] = useState(user?.last_name || '')
  const [city, setCity] = useState(profile.city || '')
  const [country, setCountry] = useState(profile.country || '')
  const [address, setAddress] = useState(profile.address || '')
  const [skills, setSkills] = useState(profile.skills || [])
  const [customSkill, setCustomSkill] = useState('')
  const [hourlyRate, setHourlyRate] = useState(profile.hourly_rate || '')
  const [bio, setBio] = useState(profile.bio || '')
  const [portfolioWebsite, setPortfolioWebsite] = useState(profile.portfolio_website || '')
  const [experienceLevel, setExperienceLevel] = useState(profile.experience_level || 'Intermediate')

  // Avatar & Banner State
  const [avatarFile, setAvatarFile] = useState(null)
  const [bannerFile, setBannerFile] = useState(null)
  const [avatarPreview, setAvatarPreview] = useState(profile.avatar || null)
  const [bannerPreview, setBannerPreview] = useState(profile.banner_image || null)
  const avatarInputRef = useRef(null)
  const bannerInputRef = useRef(null)

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const toggleSkill = (s) => {
    if (skills.includes(s)) {
      setSkills(skills.filter(x => x !== s))
    } else {
      setSkills([...skills, s])
    }
  }

  const addCustomSkill = (e) => {
    e.preventDefault()
    if (!customSkill.trim()) return
    const trimmed = customSkill.trim()
    if (!skills.includes(trimmed)) {
      setSkills([...skills, trimmed])
    }
    setCustomSkill('')
  }

  const isValidUrl = (url) => {
    if (!url || !url.trim()) return true
    const trimmed = url.trim()
    const fullUrl = (trimmed.startsWith('http://') || trimmed.startsWith('https://'))
      ? trimmed
      : `https://${trimmed}`
    try {
      const parsed = new URL(fullUrl)
      return Boolean(parsed.hostname && parsed.hostname.includes('.'))
    } catch {
      return false
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!city.trim() || !country.trim()) {
      setError('City and Country are required details.')
      return
    }
    if (skills.length === 0) {
      setError('Please select at least 1 primary skill.')
      return
    }
    if (hourlyRate !== '' && hourlyRate !== null) {
      const rateNum = parseFloat(hourlyRate)
      if (isNaN(rateNum) || rateNum < 0 || rateNum > 1000) {
        setError('Hourly rate must be between $0 and $1,000 / hr.')
        return
      }
    }
    if (portfolioWebsite.trim() && !isValidUrl(portfolioWebsite)) {
      setError('Please enter a valid portfolio or GitHub URL (e.g. https://github.com/username or https://myportfolio.com).')
      return
    }

    setSaving(true)
    setError('')
    try {
      // 1. Upload Avatar if selected
      if (avatarFile) {
        try {
          const res = await usersAPI.uploadImage(avatarFile, 'avatar')
          if (res?.data?.user) setUser(res.data.user)
        } catch (imgErr) {
          console.warn('Avatar upload error:', imgErr)
        }
      }

      // 2. Upload Banner if selected
      if (bannerFile) {
        try {
          const res = await usersAPI.uploadImage(bannerFile, 'banner')
          if (res?.data?.user) setUser(res.data.user)
        } catch (imgErr) {
          console.warn('Banner upload error:', imgErr)
        }
      }

      // 3. Update Text Profile Details
      let formattedPortfolio = portfolioWebsite.trim()
      if (formattedPortfolio && !formattedPortfolio.startsWith('http://') && !formattedPortfolio.startsWith('https://')) {
        formattedPortfolio = `https://${formattedPortfolio}`
      }

      const updateRes = await usersAPI.updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        city: city.trim(),
        country: country.trim(),
        address: address.trim(),
        skills,
        hourly_rate: hourlyRate && !isNaN(parseFloat(hourlyRate)) ? parseFloat(hourlyRate) : null,
        bio: bio.trim(),
        portfolio_website: formattedPortfolio,
        experience_level: experienceLevel || 'Intermediate',
        is_onboarded: true,
      })

      if (updateRes?.data) {
        setUser(updateRes.data)
      } else {
        await fetchUser()
      }

      onSaveSuccess()
      onClose()
    } catch (err) {
      console.error(err)
      const data = err.response?.data
      let msg = 'Failed to update profile details.'
      if (typeof data === 'string') msg = data
      else if (data?.message) msg = data.message
      else if (data?.detail) msg = data.detail
      else if (typeof data === 'object') {
        const firstErrKey = Object.keys(data)[0]
        if (firstErrKey) {
          const val = data[firstErrKey]
          msg = `${firstErrKey}: ${Array.isArray(val) ? val.join(', ') : val}`
        }
      }
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-1.5 rounded-xl hover:bg-gray-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600 font-bold">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">Edit Personal & Professional Details</h3>
            <p className="text-xs text-gray-500">Update your profile photos, location, skills, and rates</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* ── Photo & Banner Upload Section ─────────────────────────────── */}
          <div className="space-y-4 pb-4 border-b border-gray-100">
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500">Profile Visuals</h4>

            {/* Banner Upload Box */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Cover / Banner Image</label>
              <div
                onClick={() => bannerInputRef.current?.click()}
                className="relative w-full h-28 bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl overflow-hidden cursor-pointer hover:border-primary-400 transition-all group flex items-center justify-center"
              >
                {bannerPreview ? (
                  <img src={bannerPreview} alt="Cover Preview" className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center justify-center gap-1 text-gray-400">
                    <ImageIcon className="w-6 h-6" />
                    <span className="text-xs font-medium">Click to upload cover banner (1200×300 recommended)</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 text-white font-semibold text-xs">
                  <Upload className="w-4 h-4" /> Change Cover Image
                </div>
              </div>
              <input
                ref={bannerInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={e => {
                  const file = e.target.files?.[0]
                  if (file) {
                    setBannerFile(file)
                    setBannerPreview(URL.createObjectURL(file))
                  }
                }}
              />
            </div>

            {/* Avatar Upload */}
            <div className="flex items-center gap-5 pt-1">
              <div
                onClick={() => avatarInputRef.current?.click()}
                className="relative w-20 h-20 rounded-2xl bg-gray-100 border-2 border-dashed border-gray-300 overflow-hidden cursor-pointer hover:border-primary-400 transition-all group flex-shrink-0 flex items-center justify-center shadow-sm"
              >
                {avatarPreview ? (
                  <img src={avatarPreview} alt="Avatar Preview" className="w-full h-full object-cover" />
                ) : (
                  <Camera className="w-7 h-7 text-gray-400" />
                )}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-2xl text-white">
                  <Upload className="w-5 h-5" />
                </div>
              </div>
              <div>
                <p className="text-xs font-bold text-gray-800">Profile Photo</p>
                <p className="text-[11px] text-gray-500 mt-0.5">Upload a professional headshot. Square JPG, PNG, or WebP.</p>
                <button
                  type="button"
                  onClick={() => avatarInputRef.current?.click()}
                  className="mt-1.5 text-xs font-semibold text-primary-600 hover:text-primary-800 underline underline-offset-2"
                >
                  Choose new photo…
                </button>
              </div>
              <input
                ref={avatarInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={e => {
                  const file = e.target.files?.[0]
                  if (file) {
                    setAvatarFile(file)
                    setAvatarPreview(URL.createObjectURL(file))
                  }
                }}
              />
            </div>
          </div>

          {/* Name */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">First Name</label>
              <input
                type="text"
                value={firstName}
                onChange={e => setFirstName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Last Name</label>
              <input
                type="text"
                value={lastName}
                onChange={e => setLastName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Location */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                City <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={city}
                onChange={e => setCity(e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Country <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={country}
                onChange={e => setCountry(e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Skills */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Primary Skills <span className="text-red-500">*</span> ({skills.length} selected)
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {skills.map(s => (
                <span key={s} className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-lg flex items-center gap-1">
                  {s}
                  <button type="button" onClick={() => toggleSkill(s)} className="text-primary-400 hover:text-primary-900 font-bold ml-1">×</button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={customSkill}
                onChange={e => setCustomSkill(e.target.value)}
                placeholder="Add skill tag (e.g. React, Python)..."
                className="flex-1 px-3 py-1.5 border border-gray-200 rounded-xl text-xs"
              />
              <button type="button" onClick={addCustomSkill} className="btn-secondary text-xs px-3 py-1.5">
                Add Tag
              </button>
            </div>
          </div>

          {/* Hourly Rate & Experience Level */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-gray-700">Hourly Rate ($ / hr)</label>
                <span className="text-[10px] text-gray-400">Max $1,000 / hr</span>
              </div>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1000"
                value={hourlyRate}
                onChange={e => setHourlyRate(e.target.value)}
                placeholder="45.00"
                className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Experience Level</label>
              <select
                value={experienceLevel}
                onChange={e => setExperienceLevel(e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500"
              >
                <option value="Entry">Entry Level</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Expert">Expert</option>
              </select>
            </div>
          </div>

          {/* Portfolio Link */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Portfolio / Website / GitHub URL</label>
            <input
              type="text"
              value={portfolioWebsite}
              onChange={e => setPortfolioWebsite(e.target.value)}
              placeholder="https://github.com/username or yourportfolio.com"
              className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Bio */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Professional Bio / Overview</label>
            <textarea
              rows={3}
              value={bio}
              onChange={e => setBio(e.target.value)}
              placeholder="Summary of your technical expertise..."
              className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-gray-100">
            <button type="button" onClick={onClose} className="btn-secondary py-2 px-4 text-xs font-semibold">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-primary py-2 px-6 text-xs font-semibold">
              {saving ? 'Saving...' : 'Save Profile Details'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function FreelancerOverviewPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [bids, setBids] = useState([])
  const [contracts, setContracts] = useState([])
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [showEditModal, setShowEditModal] = useState(false)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      const [bidsRes, contractsRes, paymentsRes] = await Promise.allSettled([
        bidsAPI.getMyBids(),
        contractsAPI.getContracts(),
        paymentsAPI.getPayments(),
      ])
      if (bidsRes.status === 'fulfilled') {
        const d = bidsRes.value.data
        setBids(Array.isArray(d) ? d : (d?.results || []))
      }
      if (contractsRes.status === 'fulfilled') {
        const d = contractsRes.value.data
        setContracts(Array.isArray(d) ? d : (d?.results || []))
      }
      if (paymentsRes.status === 'fulfilled') {
        const d = paymentsRes.value.data
        setPayments(Array.isArray(d) ? d : (d?.results || []))
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const activeContracts = contracts.filter(c => c.is_active)
  const pendingBids = bids.filter(b => b.status === 'PENDING')

  // Earnings calculations
  const releasedPayments = payments.filter(p => p.status === 'RELEASED')
  const totalEarned = releasedPayments.reduce((s, p) => {
    return s + parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
  }, 0)

  const pendingEscrow = payments
    .filter(p => p.status === 'ESCROWED')
    .reduce((s, p) => s + parseFloat(p.total_amount * 0.9 || 0), 0)

  // Monthly breakdown grouping
  const monthlyData = releasedPayments.reduce((acc, p) => {
    const month = new Date(p.created_at).toLocaleString('default', { month: 'short', year: 'numeric' })
    const net = parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
    acc[month] = (acc[month] || 0) + net
    return acc
  }, {})

  // Profile Completeness Calculation
  const profile = user?.freelancer_profile || {}
  let score = 0
  if (user?.first_name) score += 15
  if (profile.city && profile.country) score += 25
  if (profile.skills?.length > 0) score += 25
  if (profile.hourly_rate) score += 15
  if (profile.bio) score += 10
  if (profile.portfolio_website) score += 10

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Freelancer Dashboard</h1>
          <p className="text-gray-600 mt-1">Overview of your active work, bids, and total earnings</p>
        </div>
        <button onClick={() => navigate('/freelancer/browse')} className="btn-primary flex items-center gap-2 self-start sm:self-auto">
          <Search className="w-4 h-4" /> Find Projects
        </button>
      </div>

      {/* Profile Completeness & Personal Details Card */}
      <div
        className="text-white rounded-2xl p-6 sm:p-7 shadow-xl relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border border-white/10 bg-cover bg-center transition-all duration-300"
        style={{
          backgroundImage: profile.banner_image
            ? `linear-gradient(to right, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.88) 55%, rgba(15, 23, 42, 0.72) 100%), url(${profile.banner_image})`
            : undefined,
          backgroundColor: !profile.banner_image ? '#0f172a' : undefined,
        }}
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5 max-w-2xl">
          {/* Avatar / Profile Photo Circle */}
          <div
            onClick={() => setShowEditModal(true)}
            className="relative w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-white/10 border-2 border-white/20 overflow-hidden flex-shrink-0 shadow-lg cursor-pointer group flex items-center justify-center"
            title="Click to edit profile & photo"
          >
            {profile.avatar ? (
              <img src={profile.avatar} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary-600 to-indigo-700 text-white font-extrabold text-xl sm:text-2xl">
                {user?.first_name ? user.first_name[0].toUpperCase() : (user?.email?.[0]?.toUpperCase() || 'F')}
              </div>
            )}
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white">
              <Camera className="w-5 h-5" />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 bg-primary-500/20 border border-primary-400/30 text-primary-300 text-xs font-extrabold rounded-full uppercase tracking-wider">
                Profile {score}% Complete
              </span>
              {score < 100 && (
                <span className="text-[11px] text-amber-300 font-medium">
                  • Complete all details for higher visibility!
                </span>
              )}
            </div>

            <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
              {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.email}
            </h2>

            <p className="text-xs text-gray-300 flex flex-wrap items-center gap-3">
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-primary-400" />
                {profile.city && profile.country ? `${profile.city}, ${profile.country}` : 'Location missing'}
              </span>
              <span className="flex items-center gap-1">
                <DollarSign className="w-3.5 h-3.5 text-green-400" />
                {profile.hourly_rate ? `$${profile.hourly_rate}/hr` : 'Hourly rate not set'}
              </span>
              <span className="flex items-center gap-1">
                <Wrench className="w-3.5 h-3.5 text-yellow-400" />
                {profile.skills?.length || 0} Skills
              </span>
              {profile.portfolio_website && (
                <span className="flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-indigo-400" />
                  Portfolio linked
                </span>
              )}
            </p>

            {/* Progress bar */}
            <div className="w-full sm:w-80 bg-white/10 h-1.5 rounded-full overflow-hidden mt-1">
              <div className="bg-primary-500 h-full rounded-full transition-all duration-500" style={{ width: `${score}%` }} />
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowEditModal(true)}
          className="bg-white text-gray-900 hover:bg-gray-100 font-bold text-xs px-5 py-2.5 rounded-xl transition-all shadow-md flex items-center gap-2 flex-shrink-0 self-start md:self-center"
        >
          <Edit3 className="w-3.5 h-3.5 text-primary-600" /> Edit Personal Details
        </button>
      </div>

      {/* Top 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Briefcase}
          label="Active Contracts"
          value={loading ? '—' : activeContracts.length}
          subtext="Ongoing client work"
          color="text-primary-600"
          bg="bg-primary-50"
        />
        <StatCard
          icon={FileText}
          label="Pending Proposals"
          value={loading ? '—' : pendingBids.length}
          subtext="Awaiting client response"
          color="text-yellow-600"
          bg="bg-yellow-50"
        />
        <StatCard
          icon={DollarSign}
          label="Total Earned"
          value={loading ? '—' : `$${totalEarned.toLocaleString()}`}
          subtext={`${releasedPayments.length} released payments`}
          color="text-green-600"
          bg="bg-green-50"
        />
        <StatCard
          icon={Clock}
          label="Pending in Escrow"
          value={loading ? '—' : `$${pendingEscrow.toLocaleString()}`}
          subtext="Awaiting work approval"
          color="text-indigo-600"
          bg="bg-indigo-50"
        />
      </div>

      {/* Main Grid: Active Contracts & Transaction History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (2 Cols): Active Contracts + Transaction History */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Active Contracts Card */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Active Contracts</h2>
                <p className="text-xs text-gray-500">Your current ongoing client projects</p>
              </div>
              <button
                onClick={() => navigate('/freelancer/contracts')}
                className="text-sm text-primary-600 hover:text-primary-700 font-semibold flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {loading ? (
              <div className="space-y-3">
                {[...Array(2)].map((_, i) => (
                  <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : activeContracts.length === 0 ? (
              <div className="text-center py-10 bg-gray-50 rounded-xl">
                <Briefcase className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-600">No active contracts yet</p>
                <button onClick={() => navigate('/freelancer/browse')} className="text-xs text-primary-600 hover:underline mt-1 font-semibold">
                  Browse open projects to place bids →
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {activeContracts.map(contract => (
                  <div
                    key={contract.id}
                    onClick={() => navigate(`/freelancer/contracts/${contract.id}`)}
                    className="p-4 border border-gray-100 rounded-xl hover:border-primary-200 transition-all flex items-center justify-between cursor-pointer group"
                  >
                    <div>
                      <h4 className="font-bold text-gray-900 text-sm group-hover:text-primary-600 transition-colors">
                        {contract.project_title || 'Untitled Project'}
                      </h4>
                      <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                        <span>Client: {contract.client_name || 'Client'}</span>
                        <span>•</span>
                        <span>Started {new Date(contract.start_date || contract.created_at).toLocaleDateString()}</span>
                      </p>
                    </div>
                    <div className="text-right flex items-center gap-3">
                      <div>
                        <p className="text-sm font-extrabold text-gray-900">${parseFloat(contract.agreed_amount)?.toLocaleString()}</p>
                        <span className="inline-block text-[10px] font-bold px-2 py-0.5 bg-green-50 text-green-700 rounded-full">
                          Active
                        </span>
                      </div>
                      <ArrowUpRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Transaction History & Released Earnings Table */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Earnings & Transaction History</h2>
                <p className="text-xs text-gray-500">Record of all Razorpay Escrow payouts and released funds</p>
              </div>
              <span className="text-xs font-semibold text-green-700 bg-green-50 px-2.5 py-1 rounded-lg flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Razorpay Escrow Protected
              </span>
            </div>

            {releasedPayments.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-xl">
                <DollarSign className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-xs text-gray-500">No released transactions yet.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 text-gray-400 font-semibold uppercase tracking-wider">
                      <th className="pb-3">Contract / Project</th>
                      <th className="pb-3">Date</th>
                      <th className="pb-3 text-right">Gross Amount</th>
                      <th className="pb-3 text-right">Fee (10%)</th>
                      <th className="pb-3 text-right">Net Payout</th>
                      <th className="pb-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {releasedPayments.map(payment => {
                      const gross = parseFloat(payment.total_amount || 0)
                      const net = parseFloat(payment.freelancer_amount || gross * 0.9 || 0)
                      const fee = gross - net
                      return (
                        <tr key={payment.id} className="hover:bg-gray-50/50">
                          <td className="py-3 font-semibold text-gray-900">{payment.contract_title || `Payment #${payment.id}`}</td>
                          <td className="py-3 text-gray-500">{new Date(payment.created_at).toLocaleDateString()}</td>
                          <td className="py-3 text-right text-gray-600">${gross.toFixed(2)}</td>
                          <td className="py-3 text-right text-red-500">-${fee.toFixed(2)}</td>
                          <td className="py-3 text-right font-bold text-green-700">${net.toFixed(2)}</td>
                          <td className="py-3 text-right">
                            <span className="px-2 py-0.5 bg-green-50 text-green-700 rounded-full font-bold text-[10px]">
                              RELEASED
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

        {/* Right Column (1 Col): Monthly Summary & Pending Bids */}
        <div className="space-y-6">
          
          {/* Monthly Breakdown */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="text-base font-bold text-gray-900 mb-1">Monthly Earnings</h3>
            <p className="text-xs text-gray-500 mb-4">Summary of monthly released payouts</p>
            {Object.keys(monthlyData).length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-4">No monthly payouts recorded</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(monthlyData).map(([m, amt]) => (
                  <div key={m} className="flex items-center justify-between text-xs py-2 border-b border-gray-50 last:border-none">
                    <span className="font-medium text-gray-700 flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-gray-400" /> {m}
                    </span>
                    <span className="font-extrabold text-gray-900">${amt.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Pending Proposals Quick View */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-900">Submitted Proposals</h3>
              <button onClick={() => navigate('/freelancer/bids')} className="text-xs text-primary-600 hover:underline font-semibold">
                View Bids →
              </button>
            </div>
            {pendingBids.length === 0 ? (
              <div className="text-center py-6 bg-gray-50 rounded-xl">
                <FileText className="w-8 h-8 text-gray-300 mx-auto mb-1" />
                <p className="text-xs text-gray-500">No pending proposals right now</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {pendingBids.slice(0, 3).map(bid => (
                  <div key={bid.id} className="p-3 bg-gray-50 rounded-xl flex items-center justify-between text-xs">
                    <div className="min-w-0 pr-2">
                      <p className="font-bold text-gray-900 truncate">{bid.project_title || 'Project'}</p>
                      <p className="text-[11px] text-gray-400">${parseFloat(bid.bid_amount)?.toLocaleString()} proposed</p>
                    </div>
                    <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded-md font-semibold text-[10px] flex-shrink-0">
                      PENDING
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Edit Profile Modal */}
      {showEditModal && (
        <EditProfileModal
          onClose={() => setShowEditModal(false)}
          onSaveSuccess={() => {
            // refresh data if needed
          }}
        />
      )}
    </div>
  )
}
