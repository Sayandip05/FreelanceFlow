import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, FileText, Briefcase, DollarSign,
  Clock, CheckCircle, ArrowRight, User, Edit3, MapPin, Wrench, Globe,
  Camera, Image as ImageIcon, Upload, Sparkles, AlertCircle, RefreshCw, X, ExternalLink
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { bidsAPI, contractsAPI } from '../../api/bids'
import { paymentsAPI } from '../../api/payments'
import { usersAPI } from '../../api/auth'
import { DashboardSkeleton } from '../../components/common/Skeleton'

const POPULAR_SKILLS = [
  'React', 'Node.js', 'Python', 'TypeScript', 'Next.js',
  'Django', 'PostgreSQL', 'Tailwind CSS', 'Docker', 'AWS', 'UI/UX Design'
]

export default function FreelancerOverviewPage() {
  const navigate = useNavigate()
  const { user, setUser, fetchUser } = useAuth()
  
  // Dashboard Metrics State
  const [bids, setBids] = useState([])
  const [contracts, setContracts] = useState([])
  const [payments, setPayments] = useState([])
  const [loadingMetrics, setLoadingMetrics] = useState(true)

  // Edit Mode Toggle
  const [isEditing, setIsEditing] = useState(false)

  // Profile Form State
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
  const formSectionRef = useRef(null)

  // Feedback State
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState('')
  const [saveError, setSaveError] = useState('')

  // Sync state when user object loads/updates
  useEffect(() => {
    if (user) {
      setFirstName(user.first_name || '')
      setLastName(user.last_name || '')
      const p = user.freelancer_profile || {}
      setCity(p.city || '')
      setCountry(p.country || '')
      setAddress(p.address || '')
      setSkills(Array.isArray(p.skills) ? p.skills : [])
      setHourlyRate(p.hourly_rate ?? '')
      setBio(p.bio || '')
      setPortfolioWebsite(p.portfolio_website || '')
      setExperienceLevel(p.experience_level || 'Intermediate')
      setAvatarPreview(p.avatar || null)
      setBannerPreview(p.banner_image || null)
    }
  }, [user])

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoadingMetrics(true)
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
      console.error('Error fetching metrics:', e)
    } finally {
      setLoadingMetrics(false)
    }
  }

  const activeContracts = contracts.filter(c => c.is_active)
  const pendingBids = bids.filter(b => b.status === 'PENDING')
  const releasedPayments = payments.filter(p => p.status === 'RELEASED')
  const totalEarned = releasedPayments.reduce((s, p) => {
    return s + parseFloat(p.freelancer_amount || p.total_amount * 0.9 || 0)
  }, 0)
  const pendingEscrow = payments
    .filter(p => p.status === 'ESCROWED')
    .reduce((s, p) => s + parseFloat(p.total_amount * 0.9 || 0), 0)

  // Skill management
  const toggleSkill = (s) => {
    if (!isEditing) return
    if (skills.includes(s)) {
      setSkills(skills.filter(x => x !== s))
    } else {
      setSkills([...skills, s])
    }
  }

  const addCustomSkill = (e) => {
    e?.preventDefault()
    if (!isEditing || !customSkill.trim()) return
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

  const handleReset = () => {
    if (user) {
      setFirstName(user.first_name || '')
      setLastName(user.last_name || '')
      const p = user.freelancer_profile || {}
      setCity(p.city || '')
      setCountry(p.country || '')
      setAddress(p.address || '')
      setSkills(Array.isArray(p.skills) ? p.skills : [])
      setHourlyRate(p.hourly_rate ?? '')
      setBio(p.bio || '')
      setPortfolioWebsite(p.portfolio_website || '')
      setExperienceLevel(p.experience_level || 'Intermediate')
      setAvatarFile(null)
      setBannerFile(null)
      setAvatarPreview(p.avatar || null)
      setBannerPreview(p.banner_image || null)
      setSaveError('')
    }
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setSaveSuccess('')
    setSaveError('')

    if (!city.trim() || !country.trim()) {
      setSaveError('City and Country are required.')
      return
    }
    if (skills.length === 0) {
      setSaveError('Please select or add at least 1 primary skill.')
      return
    }
    if (hourlyRate !== '' && hourlyRate !== null) {
      const rateNum = parseFloat(hourlyRate)
      if (isNaN(rateNum) || rateNum < 0 || rateNum > 1000) {
        setSaveError('Hourly rate must be between $0 and $1,000 / hr.')
        return
      }
    }
    if (portfolioWebsite.trim() && !isValidUrl(portfolioWebsite)) {
      setSaveError('Please enter a valid portfolio or GitHub URL (e.g. https://github.com/username).')
      return
    }

    setSaving(true)
    try {
      // 1. Upload Avatar if selected
      if (avatarFile) {
        try {
          const res = await usersAPI.uploadImage(avatarFile, 'avatar')
          if (res?.data?.user) setUser(res.data.user)
        } catch (imgErr) {
          console.warn('Avatar upload warning:', imgErr)
        }
      }

      // 2. Upload Banner if selected
      if (bannerFile) {
        try {
          const res = await usersAPI.uploadImage(bannerFile, 'banner')
          if (res?.data?.user) setUser(res.data.user)
        } catch (imgErr) {
          console.warn('Banner upload warning:', imgErr)
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

      setSaveSuccess('Profile details saved successfully!')
      setAvatarFile(null)
      setBannerFile(null)
      setIsEditing(false)

      setTimeout(() => {
        setSaveSuccess('')
      }, 5000)
    } catch (err) {
      console.error('Error saving profile:', err)
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
      setSaveError(msg)
    } finally {
      setSaving(false)
    }
  }

  if (loadingMetrics && !user) {
    return (
      <div className="max-w-6xl mx-auto pt-4 pb-16 space-y-8">
        <DashboardSkeleton />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto pt-4 pb-16 space-y-8">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
            Freelancer Dashboard
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Overview of your active work, bids, total earnings, and personal profile
          </p>
        </div>
        <button
          onClick={() => navigate('/freelancer/browse')}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto shadow-sm"
        >
          <Search className="w-4 h-4" /> Find Projects
        </button>
      </div>

      {/* ── 4 Stat Cards Serially Aligned ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Active Contracts</p>
            <p className="text-2xl font-black text-gray-900 my-0.5">{loadingMetrics ? '—' : activeContracts.length}</p>
            <p className="text-xs text-gray-500 font-medium">Ongoing client work</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600 shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Pending Proposals</p>
            <p className="text-2xl font-black text-gray-900 my-0.5">{loadingMetrics ? '—' : pendingBids.length}</p>
            <p className="text-xs text-gray-500 font-medium">Awaiting client response</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 shrink-0">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Earned</p>
            <p className="text-2xl font-black text-gray-900 my-0.5">
              {loadingMetrics ? '—' : `$${totalEarned.toLocaleString()}`}
            </p>
            <p className="text-xs text-gray-500 font-medium">{releasedPayments.length} released payments</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-sky-50 flex items-center justify-center text-sky-600 shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Pending in Escrow</p>
            <p className="text-2xl font-black text-gray-900 my-0.5">
              {loadingMetrics ? '—' : `$${pendingEscrow.toLocaleString()}`}
            </p>
            <p className="text-xs text-gray-500 font-medium">Awaiting milestone approval</p>
          </div>
        </div>
      </div>

      {/* ── Downside Embedded Profile Form Section ────────────────────────────── */}
      <div
        ref={formSectionRef}
        id="profile-settings-section"
        className="bg-white/90 backdrop-blur-md rounded-none border border-gray-200 shadow-sm p-6 sm:p-8 space-y-8 scroll-mt-6"
      >
        {/* Section Header with Edit Profile Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600 font-bold shrink-0">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Profile & Account Details</h2>
              <p className="text-xs text-gray-500">
                {isEditing
                  ? 'Edit your personal details, rates, skills, and portfolio below'
                  : 'Your public profile, skills, rates, and contact information'}
              </p>
            </div>
          </div>

          {/* Edit / Cancel Toggle Action */}
          <div>
            {!isEditing ? (
              <button
                type="button"
                onClick={() => {
                  setIsEditing(true)
                  setSaveError('')
                  setSaveSuccess('')
                }}
                className="btn-secondary py-2 px-4 text-xs font-bold flex items-center gap-2 hover:bg-gray-100 transition-all active:scale-95 shadow-2xs"
              >
                <Edit3 className="w-3.5 h-3.5 text-primary-600" /> Edit Profile
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-700 text-xs font-semibold rounded-xl border border-amber-200">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                  Editing
                </span>
                <button
                  type="button"
                  onClick={() => {
                    handleReset()
                    setIsEditing(false)
                  }}
                  className="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-xl transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Feedback Alerts */}
        {saveSuccess && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-2xl flex items-center gap-2.5 animate-in fade-in">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{saveSuccess}</span>
          </div>
        )}

        {saveError && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-800 text-xs rounded-2xl flex items-center gap-2.5 animate-in fade-in">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{saveError}</span>
          </div>
        )}

        <form onSubmit={handleSaveProfile} className="space-y-8">
          
          {/* 1. Visual Branding (Banner & Avatar) */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-primary-500" /> Visual Branding
            </h3>

            {/* Banner Upload Box */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Cover Banner</label>
              <div
                onClick={() => {
                  if (isEditing) bannerInputRef.current?.click()
                }}
                className={`relative w-full h-32 sm:h-36 bg-gray-50 border-2 rounded-2xl overflow-hidden transition-all flex items-center justify-center shadow-inner ${
                  isEditing
                    ? 'border-dashed border-gray-300 hover:border-primary-400 cursor-pointer group'
                    : 'border-solid border-gray-100 cursor-default'
                }`}
              >
                {bannerPreview ? (
                  <img src={bannerPreview} alt="Cover Preview" className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center justify-center gap-1.5 text-gray-400 p-4 text-center">
                    <ImageIcon className="w-7 h-7 text-gray-300" />
                    <span className="text-xs font-medium">
                      {isEditing ? 'Click to upload cover banner (1200×300 recommended)' : 'No cover banner uploaded'}
                    </span>
                  </div>
                )}
                {isEditing && (
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 text-white font-semibold text-xs">
                    <Upload className="w-4 h-4" /> Change Banner Image
                  </div>
                )}
              </div>
              <input
                ref={bannerInputRef}
                type="file"
                accept="image/*"
                disabled={!isEditing}
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
            <div className="flex items-center gap-5 pt-2">
              <div
                onClick={() => {
                  if (isEditing) avatarInputRef.current?.click()
                }}
                className={`relative w-20 h-20 rounded-2xl bg-gray-100 border-2 overflow-hidden transition-all shrink-0 flex items-center justify-center shadow-sm ${
                  isEditing
                    ? 'border-dashed border-gray-300 hover:border-primary-400 cursor-pointer group'
                    : 'border-solid border-gray-200 cursor-default'
                }`}
              >
                {avatarPreview ? (
                  <img src={avatarPreview} alt="Avatar Preview" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black text-2xl">
                    {firstName ? firstName[0].toUpperCase() : (user?.email?.[0]?.toUpperCase() || 'F')}
                  </div>
                )}
                {isEditing && (
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-2xl text-white">
                    <Upload className="w-5 h-5" />
                  </div>
                )}
              </div>
              <div>
                <p className="text-xs font-bold text-gray-800">Profile Photo</p>
                <p className="text-[11px] text-gray-500 mt-0.5">
                  {isEditing ? 'Upload a professional square headshot (JPG, PNG, WebP).' : 'Your public freelancer avatar.'}
                </p>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => avatarInputRef.current?.click()}
                    className="mt-1.5 text-xs font-semibold text-primary-600 hover:text-primary-800 underline underline-offset-2"
                  >
                    Choose new photo…
                  </button>
                )}
              </div>
              <input
                ref={avatarInputRef}
                type="file"
                accept="image/*"
                disabled={!isEditing}
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

          <hr className="border-gray-100" />

          {/* 2. Personal Information */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Personal Information</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">First Name</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={firstName}
                  onChange={e => setFirstName(e.target.value)}
                  placeholder="e.g. John"
                  className={`w-full px-4 py-2 rounded-xl text-sm transition-all border ${
                    isEditing
                      ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                      : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                  }`}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Last Name</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={lastName}
                  onChange={e => setLastName(e.target.value)}
                  placeholder="e.g. Doe"
                  className={`w-full px-4 py-2 rounded-xl text-sm transition-all border ${
                    isEditing
                      ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                      : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                  }`}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  City {isEditing && <span className="text-red-500">*</span>}
                </label>
                <input
                  type="text"
                  required
                  disabled={!isEditing}
                  value={city}
                  onChange={e => setCity(e.target.value)}
                  placeholder="e.g. San Francisco"
                  className={`w-full px-4 py-2 rounded-xl text-sm transition-all border ${
                    isEditing
                      ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                      : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                  }`}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Country {isEditing && <span className="text-red-500">*</span>}
                </label>
                <input
                  type="text"
                  required
                  disabled={!isEditing}
                  value={country}
                  onChange={e => setCountry(e.target.value)}
                  placeholder="e.g. United States"
                  className={`w-full px-4 py-2 rounded-xl text-sm transition-all border ${
                    isEditing
                      ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                      : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                  }`}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Full Street Address (Optional)</label>
              <input
                type="text"
                disabled={!isEditing}
                value={address}
                onChange={e => setAddress(e.target.value)}
                placeholder={isEditing ? "e.g. 123 Tech Boulevard, Suite 400" : "Not specified"}
                className={`w-full px-4 py-2 rounded-xl text-sm transition-all border ${
                  isEditing
                    ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                    : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                }`}
              />
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* 3. Professional Rates & Links */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Professional Rates & Details</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-gray-700">Hourly Rate ($ / hr)</label>
                  {isEditing && <span className="text-[10px] text-gray-400">Max $1,000 / hr</span>}
                </div>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 font-medium text-sm">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1000"
                    disabled={!isEditing}
                    value={hourlyRate}
                    onChange={e => setHourlyRate(e.target.value)}
                    placeholder="45.00"
                    className={`w-full pl-8 pr-4 py-2 rounded-xl text-sm transition-all border ${
                      isEditing
                        ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                        : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default font-semibold'
                    }`}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Experience Level</label>
                <select
                  disabled={!isEditing}
                  value={experienceLevel}
                  onChange={e => setExperienceLevel(e.target.value)}
                  className={`w-full px-4 py-2 rounded-xl text-sm transition-all border ${
                    isEditing
                      ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                      : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                  }`}
                >
                  <option value="Entry">Entry Level</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Expert">Expert</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Portfolio / Website / GitHub URL</label>
              <div className="relative">
                <Globe className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  disabled={!isEditing}
                  value={portfolioWebsite}
                  onChange={e => setPortfolioWebsite(e.target.value)}
                  placeholder={isEditing ? "https://github.com/username or yourportfolio.com" : "Not specified"}
                  className={`w-full pl-10 pr-4 py-2 rounded-xl text-sm transition-all border ${
                    isEditing
                      ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                      : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                  }`}
                />
              </div>
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* 4. Skills & Expertise */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-gray-700">
                Primary Skills {isEditing && <span className="text-red-500">*</span>} ({skills.length} listed)
              </label>
              {isEditing && <span className="text-[11px] text-gray-400">Click a tag to remove</span>}
            </div>

            {/* Active Skills Badges */}
            <div className="flex flex-wrap gap-1.5 min-h-[36px] p-2 bg-gray-50 border border-gray-100 rounded-2xl">
              {skills.length === 0 ? (
                <span className="text-xs text-gray-400 italic p-1">No skills added yet.</span>
              ) : (
                skills.map(s => (
                  <span
                    key={s}
                    className="px-3 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-xl flex items-center gap-1.5 border border-primary-100 shadow-2xs"
                  >
                    {s}
                    {isEditing && (
                      <button
                        type="button"
                        onClick={() => toggleSkill(s)}
                        className="text-primary-400 hover:text-primary-900 font-bold ml-0.5 text-sm"
                      >
                        ×
                      </button>
                    )}
                  </span>
                ))
              )}
            </div>

            {/* Custom Skill Input (Visible during edit mode) */}
            {isEditing && (
              <div className="flex gap-2 pt-1">
                <input
                  type="text"
                  value={customSkill}
                  onChange={e => setCustomSkill(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      addCustomSkill()
                    }
                  }}
                  placeholder="Type custom skill tag (e.g. React, GraphQL, Tailwind)..."
                  className="flex-1 px-3.5 py-2 border border-gray-200 rounded-xl text-xs focus:ring-2 focus:ring-primary-500"
                />
                <button
                  type="button"
                  onClick={addCustomSkill}
                  className="btn-secondary text-xs px-4 py-2 font-semibold"
                >
                  Add Skill
                </button>
              </div>
            )}

            {/* Popular Suggestions (Visible during edit mode) */}
            {isEditing && (
              <div className="pt-2">
                <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Suggested Skills:</p>
                <div className="flex flex-wrap gap-1.5">
                  {POPULAR_SKILLS.map(skill => {
                    const isSelected = skills.includes(skill)
                    return (
                      <button
                        key={skill}
                        type="button"
                        onClick={() => toggleSkill(skill)}
                        className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-all ${
                          isSelected
                            ? 'bg-primary-600 text-white shadow-xs'
                            : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                        }`}
                      >
                        {isSelected ? `✓ ${skill}` : `+ ${skill}`}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          <hr className="border-gray-100" />

          {/* 5. Bio / Summary */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-gray-700">Professional Bio / Overview</label>
              {isEditing && <span className="text-[11px] text-gray-400">{bio.length} characters</span>}
            </div>
            <textarea
              rows={4}
              disabled={!isEditing}
              value={bio}
              onChange={e => setBio(e.target.value)}
              placeholder={isEditing ? "Tell clients about your experience, past projects, technical stack, and what value you provide..." : "No bio provided yet."}
              className={`w-full px-4 py-3 rounded-xl text-sm resize-none transition-all border ${
                isEditing
                  ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                  : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
              }`}
            />
          </div>

          {/* Form Actions (Bottom - Only shown when editing) */}
          {isEditing && (
            <div className="pt-4 flex items-center justify-end gap-3 border-t border-gray-100 animate-in fade-in">
              <button
                type="button"
                onClick={() => {
                  handleReset()
                  setIsEditing(false)
                }}
                disabled={saving}
                className="btn-secondary py-2.5 px-5 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="btn-primary py-2.5 px-8 text-xs font-semibold shadow-sm flex items-center gap-2"
              >
                {saving ? 'Saving Profile...' : 'Save Profile Details'}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
