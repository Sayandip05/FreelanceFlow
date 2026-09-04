import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Briefcase, FileText, IndianRupee, Clock, Plus, ArrowRight,
  User, Edit3, Building2, MapPin, Globe, Users, Sparkles,
  CheckCircle, AlertCircle, Upload
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { projectsAPI } from '../../api/projects'
import { paymentsAPI } from '../../api/payments'
import { usersAPI } from '../../api/auth'
import { DashboardSkeleton } from '../../components/common/Skeleton'
import { formatCurrency } from '../../utils/formatCurrency'

const INDUSTRIES = [
  'Technology', 'Healthcare', 'Finance', 'Education', 'E-commerce',
  'Marketing', 'Real Estate', 'Media & Entertainment', 'Manufacturing',
  'Logistics', 'Legal', 'Non-Profit', 'Government', 'Other',
]

const COMPANY_SIZES = [
  { value: 'SOLO',       label: 'Just Me',         desc: 'Solo / Freelancer' },
  { value: 'SMALL',      label: '2–10',            desc: 'Small team' },
  { value: 'MEDIUM',     label: '11–50',           desc: 'Growing company' },
  { value: 'LARGE',      label: '51–200',          desc: 'Mid-size company' },
  { value: 'ENTERPRISE', label: '200+',          desc: 'Enterprise' },
]

export default function ClientOverviewPage() {
  const navigate = useNavigate()
  const { user, setUser, fetchUser } = useAuth()

  // Dashboard Metrics State
  const [projects, setProjects] = useState([])
  const [payments, setPayments] = useState([])
  const [loadingMetrics, setLoadingMetrics] = useState(true)

  // Edit Mode Toggle
  const [isEditing, setIsEditing] = useState(false)

  // Profile Form State
  const profile = user?.client_profile || {}
  const [firstName, setFirstName] = useState(user?.first_name || '')
  const [lastName, setLastName] = useState(user?.last_name || '')
  const [companyName, setCompanyName] = useState(profile.company_name || '')
  const [companySize, setCompanySize] = useState(profile.company_size || 'SOLO')
  const [industries, setIndustries] = useState(
    profile.industry ? profile.industry.split(',').map(s => s.trim()).filter(Boolean) : []
  )
  const [website, setWebsite] = useState(profile.website || '')
  const [city, setCity] = useState(profile.city || '')
  const [country, setCountry] = useState(profile.country || '')
  const [bio, setBio] = useState(profile.bio || '')

  // Avatar / Logo State
  const [avatarFile, setAvatarFile] = useState(null)
  const [avatarPreview, setAvatarPreview] = useState(profile.avatar || null)
  const avatarInputRef = useRef(null)
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
      const p = user.client_profile || {}
      setCompanyName(p.company_name || '')
      setCompanySize(p.company_size || 'SOLO')
      setIndustries(p.industry ? p.industry.split(',').map(s => s.trim()).filter(Boolean) : [])
      setWebsite(p.website || '')
      setCity(p.city || '')
      setCountry(p.country || '')
      setBio(p.bio || '')
      setAvatarPreview(p.avatar || null)
    }
  }, [user])

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoadingMetrics(true)
    try {
      const [projRes, payRes] = await Promise.allSettled([
        projectsAPI.getMyProjects(),
        paymentsAPI.getPayments(),
      ])
      if (projRes.status === 'fulfilled') {
        const d = projRes.value.data
        setProjects(Array.isArray(d) ? d : (d?.results || []))
      }
      if (payRes.status === 'fulfilled') {
        const d = payRes.value.data
        setPayments(Array.isArray(d) ? d : (d?.results || []))
      }
    } catch (e) {
      console.error('Error fetching client dashboard metrics:', e)
    } finally {
      setLoadingMetrics(false)
    }
  }

  const activeProjects = projects.filter(p => p.status === 'OPEN' || p.status === 'IN_PROGRESS')
  const releasedPayments = payments.filter(p => p.status === 'RELEASED')
  const totalSpent = releasedPayments.reduce((s, p) => s + parseFloat(p.total_amount || 0), 0)
  const pendingEscrow = payments
    .filter(p => p.status === 'ESCROWED')
    .reduce((s, p) => s + parseFloat(p.total_amount || 0), 0)

  const recentProjects = projects.slice(0, 5)

  const toggleIndustry = (ind) => {
    if (!isEditing) return
    if (industries.includes(ind)) {
      setIndustries(industries.filter(x => x !== ind))
    } else {
      setIndustries([...industries, ind])
    }
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
      const p = user.client_profile || {}
      setCompanyName(p.company_name || '')
      setCompanySize(p.company_size || 'SOLO')
      setIndustries(p.industry ? p.industry.split(',').map(s => s.trim()).filter(Boolean) : [])
      setWebsite(p.website || '')
      setCity(p.city || '')
      setCountry(p.country || '')
      setBio(p.bio || '')
      setAvatarFile(null)
      setAvatarPreview(p.avatar || null)
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
    if (industries.length === 0) {
      setSaveError('Please select at least 1 industry/sector.')
      return
    }
    if (website.trim() && !isValidUrl(website)) {
      setSaveError('Please enter a valid website URL (e.g. https://yourcompany.com).')
      return
    }

    setSaving(true)
    try {
      // 1. Upload Avatar/Logo if selected
      if (avatarFile) {
        try {
          const res = await usersAPI.uploadImage(avatarFile, 'avatar')
          if (res?.data?.user) setUser(res.data.user)
        } catch (imgErr) {
          console.warn('Avatar upload warning:', imgErr)
        }
      }

      // 2. Update Profile Details
      let formattedWebsite = website.trim()
      if (formattedWebsite && !formattedWebsite.startsWith('http://') && !formattedWebsite.startsWith('https://')) {
        formattedWebsite = `https://${formattedWebsite}`
      }

      const updateRes = await usersAPI.updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        company_name: companyName.trim(),
        company_size: companySize,
        industry: industries.join(', '),
        city: city.trim(),
        country: country.trim(),
        website: formattedWebsite,
        bio: bio.trim(),
        is_onboarded: true,
      })

      if (updateRes?.data) {
        setUser(updateRes.data)
      } else {
        await fetchUser()
      }

      setSaveSuccess('Company profile saved successfully!')
      setAvatarFile(null)
      setIsEditing(false)

      setTimeout(() => {
        setSaveSuccess('')
      }, 5000)
    } catch (err) {
      console.error('Error saving client profile:', err)
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
            Client Dashboard
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Overview of your active projects, total spending, and company profile
          </p>
        </div>
        <button
          onClick={() => navigate('/client/projects')}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto shadow-sm"
        >
          <Plus className="w-4 h-4" /> Post a Project
        </button>
      </div>

      {/* ── 4 Stat Cards Serially Aligned ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Active Projects</p>
            <p className="text-2xl font-black text-gray-900 my-0.5">{loadingMetrics ? '—' : activeProjects.length}</p>
            <p className="text-xs text-gray-500 font-medium">Currently in progress</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Projects</p>
            <p className="text-2xl font-black text-gray-900 my-0.5">{loadingMetrics ? '—' : projects.length}</p>
            <p className="text-xs text-gray-500 font-medium">All posted projects</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 shrink-0">
            <IndianRupee className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Spent</p>
            <p className="text-2xl font-black text-gray-900 my-0.5">
              {loadingMetrics ? '—' : formatCurrency(totalSpent)}
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
              {loadingMetrics ? '—' : formatCurrency(pendingEscrow)}
            </p>
            <p className="text-xs text-gray-500 font-medium">Held securely in escrow</p>
          </div>
        </div>
      </div>

      {/* ── Downside Embedded Company Profile Form Section ────────────────────────────── */}
      <div
        ref={formSectionRef}
        id="profile-settings-section"
        className="bg-white/90 backdrop-blur-md rounded-none border border-gray-200 shadow-sm p-6 sm:p-8 space-y-8 scroll-mt-6"
      >
        {/* Section Header with Edit Profile Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600 font-bold shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Company & Profile Details</h2>
              <p className="text-xs text-gray-500">
                {isEditing
                  ? 'Edit your company information, team size, sectors, and contact details below'
                  : 'Your organization details, team size, hiring sectors, and contact information'}
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
          {/* 1. Visual Branding (Logo/Avatar Only) */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-primary-500" /> Company Avatar & Logo
            </h3>

            {/* Avatar / Logo Upload */}
            <div className="flex items-center gap-5 pt-1">
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
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-indigo-600 to-purple-700 text-white font-black text-2xl">
                    {companyName ? companyName[0].toUpperCase() : (firstName ? firstName[0].toUpperCase() : (user?.email?.[0]?.toUpperCase() || 'C'))}
                  </div>
                )}
                {isEditing && (
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-2xl text-white">
                    <Upload className="w-5 h-5" />
                  </div>
                )}
              </div>
              <div>
                <p className="text-xs font-bold text-gray-800">Company Logo / Profile Photo</p>
                <p className="text-[11px] text-gray-500 mt-0.5">
                  {isEditing ? 'Upload a square logo or professional photo (JPG, PNG, WebP).' : 'Your public company avatar or logo.'}
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

          {/* 2. Personal Contact Information */}
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
                  placeholder="e.g. Jane"
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

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address</label>
              <input
                type="email"
                disabled
                value={user?.email || ''}
                className="w-full px-4 py-2 rounded-xl text-sm border border-gray-100 bg-gray-50/70 text-gray-500 cursor-not-allowed"
              />
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* 3. Company & Team Details */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Organization & Team</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Company / Organization Name</label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    disabled={!isEditing}
                    value={companyName}
                    onChange={e => setCompanyName(e.target.value)}
                    placeholder="e.g. Acme Innovations"
                    className={`w-full pl-10 pr-4 py-2 rounded-xl text-sm transition-all border ${
                      isEditing
                        ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                        : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                    }`}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Company Website</label>
                <div className="relative">
                  <Globe className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="url"
                    disabled={!isEditing}
                    value={website}
                    onChange={e => setWebsite(e.target.value)}
                    placeholder="https://yourcompany.com"
                    className={`w-full pl-10 pr-4 py-2 rounded-xl text-sm transition-all border ${
                      isEditing
                        ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                        : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                    }`}
                  />
                </div>
              </div>
            </div>

            {/* Company Size Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-2">Team / Company Size</label>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                {COMPANY_SIZES.map(s => (
                  <button
                    key={s.value}
                    type="button"
                    disabled={!isEditing}
                    onClick={() => setCompanySize(s.value)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      companySize === s.value
                        ? 'border-gray-900 bg-gray-900 text-white shadow-sm'
                        : isEditing
                          ? 'border-gray-200 bg-white hover:border-gray-400 text-gray-700'
                          : 'border-gray-100 bg-gray-50 text-gray-600 cursor-default'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <Users className="w-3.5 h-3.5 opacity-70" />
                      <span className="text-xs font-bold">{s.label}</span>
                    </div>
                    <p className={`text-[10px] ${companySize === s.value ? 'text-gray-300' : 'text-gray-400'}`}>
                      {s.desc}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* 4. Location Details */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Location</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  City {isEditing && <span className="text-red-500">*</span>}
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    disabled={!isEditing}
                    value={city}
                    onChange={e => setCity(e.target.value)}
                    placeholder="e.g. San Francisco"
                    className={`w-full pl-10 pr-4 py-2 rounded-xl text-sm transition-all border ${
                      isEditing
                        ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                        : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                    }`}
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Country {isEditing && <span className="text-red-500">*</span>}
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    disabled={!isEditing}
                    value={country}
                    onChange={e => setCountry(e.target.value)}
                    placeholder="e.g. United States"
                    className={`w-full pl-10 pr-4 py-2 rounded-xl text-sm transition-all border ${
                      isEditing
                        ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                        : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                    }`}
                  />
                </div>
              </div>
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* 5. Industry & Sectors (Multi-select) */}
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Industry / Sectors</h3>
              <p className="text-[11px] text-gray-500 mb-3">
                {isEditing ? 'Select one or more sectors that match your business operations.' : 'Primary operating sectors.'}
              </p>
              <div className="flex flex-wrap gap-2">
                {INDUSTRIES.map(ind => {
                  const isSelected = industries.includes(ind)
                  if (!isEditing && !isSelected) return null
                  return (
                    <button
                      key={ind}
                      type="button"
                      disabled={!isEditing}
                      onClick={() => toggleIndustry(ind)}
                      className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                        isSelected
                          ? 'bg-gray-900 text-white border-gray-900 shadow-sm'
                          : 'border-gray-200 text-gray-600 hover:border-gray-400 bg-white'
                      } ${!isEditing ? 'cursor-default' : ''}`}
                    >
                      {isSelected && '✓ '}{ind}
                    </button>
                  )
                })}
                {!isEditing && industries.length === 0 && (
                  <span className="text-xs text-gray-400 italic">No industry sectors specified</span>
                )}
              </div>
            </div>
          </div>

          <hr className="border-gray-100" />

          {/* 6. Company About & Bio */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">About & Background</h3>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Company Bio / Description</label>
              <textarea
                rows={4}
                disabled={!isEditing}
                value={bio}
                onChange={e => setBio(e.target.value)}
                placeholder="Tell freelancers about your company, mission, and the types of projects you usually hire for..."
                className={`w-full px-4 py-3 rounded-xl text-sm transition-all border resize-none ${
                  isEditing
                    ? 'border-gray-200 focus:ring-2 focus:ring-primary-500 bg-white'
                    : 'border-gray-100 bg-gray-50/70 text-gray-800 cursor-default'
                }`}
              />
            </div>
          </div>

          {/* Save Profile Button Action Bar */}
          {isEditing && (
            <div className="pt-4 border-t border-gray-100 flex items-center justify-end gap-3 animate-in fade-in">
              <button
                type="button"
                onClick={() => {
                  handleReset()
                  setIsEditing(false)
                }}
                className="btn-secondary py-2.5 px-5 text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="btn-primary py-2.5 px-6 text-xs font-bold flex items-center gap-2 shadow-sm disabled:opacity-60"
              >
                {saving ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Saving Changes…
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" /> Save Profile Changes
                  </>
                )}
              </button>
            </div>
          )}
        </form>
      </div>

      {/* ── Recent Projects (Full Width) ────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Recent Projects</h2>
            <p className="text-xs text-gray-500 mt-0.5">Manage and view recent project postings and proposals</p>
          </div>
          <button
            onClick={() => navigate('/client/projects')}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
          >
            View all projects <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {loadingMetrics ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : recentProjects.length === 0 ? (
          <div className="text-center py-12">
            <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-600 mb-4">No projects posted yet</p>
            <button onClick={() => navigate('/client/projects')} className="btn-primary text-sm">
              Post Your First Project
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {recentProjects.map((project) => (
              <div
                key={project.id}
                onClick={() => navigate(`/client/projects/${project.id}`)}
                className="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-900">{project.title}</p>
                  <p className="text-sm text-gray-500">Budget: {formatCurrency(project.budget)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                    project.status === 'OPEN' ? 'bg-green-100 text-green-700' :
                    project.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {project.status}
                  </span>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
