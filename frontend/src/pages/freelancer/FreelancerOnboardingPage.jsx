import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MapPin, Wrench, DollarSign, Globe, Briefcase,
  CheckCircle, ArrowRight, ArrowLeft, SkipForward, Plus, X,
  Camera, Image as ImageIcon, Upload
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { usersAPI } from '../../api/auth'
import api from '../../api/axiosConfig'

const POPULAR_SKILLS = [
  'React', 'Node.js', 'Python', 'Django', 'TypeScript',
  'JavaScript', 'UI/UX Design', 'Tailwind CSS', 'PostgreSQL',
  'Figma', 'Next.js', 'REST API', 'GraphQL', 'Docker'
]

export default function FreelancerOnboardingPage() {
  const navigate = useNavigate()
  const { user, setUser, fetchUser } = useAuth()

  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Form State
  const profile = user?.freelancer_profile || {}

  const [city, setCity] = useState(profile.city || '')
  const [country, setCountry] = useState(profile.country || '')
  const [address, setAddress] = useState(profile.address || '')

  const [skills, setSkills] = useState(profile.skills || [])
  const [customSkill, setCustomSkill] = useState('')

  const [hourlyRate, setHourlyRate] = useState(profile.hourly_rate || '')
  const [bio, setBio] = useState(profile.bio || '')

  const [portfolioWebsite, setPortfolioWebsite] = useState(profile.portfolio_website || '')
  const [experienceLevel, setExperienceLevel] = useState(profile.experience_level || 'Intermediate')

  // Step 5: Avatar & Banner
  const [avatarFile, setAvatarFile] = useState(null)
  const [bannerFile, setBannerFile] = useState(null)
  const [avatarPreview, setAvatarPreview] = useState(profile.avatar || null)
  const [bannerPreview, setBannerPreview] = useState(profile.banner_image || null)
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  const [uploadingBanner, setUploadingBanner] = useState(false)
  const avatarInputRef = useRef(null)
  const bannerInputRef = useRef(null)

  // Toggle skill selection
  const toggleSkill = (skillName) => {
    if (skills.includes(skillName)) {
      setSkills(skills.filter(s => s !== skillName))
    } else {
      setSkills([...skills, skillName])
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

  // Validate URL format (http/https or valid domain)
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

  // Format URL helper
  const formatUrl = (url) => {
    if (!url || !url.trim()) return ''
    const trimmed = url.trim()
    return (trimmed.startsWith('http://') || trimmed.startsWith('https://'))
      ? trimmed
      : `https://${trimmed}`
  }

  // Save profile state to backend
  const handleSubmitProfile = async (completedOnboarding = true) => {
    // Validate hourly rate
    if (hourlyRate !== '' && hourlyRate !== null) {
      const rateNum = parseFloat(hourlyRate)
      if (isNaN(rateNum) || rateNum < 0 || rateNum > 1000) {
        setError('Hourly rate must be between $0 and $1,000 / hr.')
        return
      }
    }

    // Validate portfolio URL
    if (portfolioWebsite.trim() && !isValidUrl(portfolioWebsite)) {
      setError('Please enter a valid portfolio or GitHub URL (e.g. https://github.com/username or https://myportfolio.com).')
      return
    }

    setLoading(true)
    setError('')
    try {
      // 1. Save profile fields to backend first (instant)
      const formattedPortfolio = formatUrl(portfolioWebsite)
      const payload = {
        city: city.trim(),
        country: country.trim(),
        address: address.trim(),
        skills: skills,
        hourly_rate: hourlyRate && !isNaN(parseFloat(hourlyRate)) ? parseFloat(hourlyRate) : null,
        bio: bio.trim(),
        portfolio_website: formattedPortfolio,
        experience_level: experienceLevel || 'Intermediate',
        is_onboarded: completedOnboarding,
      }

      const res = await usersAPI.updateProfile(payload)
      if (res?.data) {
        setUser(res.data)
      } else {
        await fetchUser()
      }

      // 2. Fire image uploads in the background — no await, user goes to dashboard immediately
      if (avatarFile) {
        uploadImage(avatarFile, 'avatar', setUploadingAvatar)
      }
      if (bannerFile) {
        uploadImage(bannerFile, 'banner', setUploadingBanner)
      }

      // 3. Navigate instantly — images will finish uploading in the browser background
      navigate('/freelancer/browse')
    } catch (err) {
      console.error('Onboarding profile submit error:', err)
      const data = err.response?.data
      let msg = 'Failed to save profile details. Please check inputs.'
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
      setLoading(false)
    }
  }

  // Upload image to Azure via SAS token — runs silently in background after navigation
  const uploadImage = async (file, imageType, setUploading) => {
    if (!file) return
    setUploading(true)
    try {
      const res = await usersAPI.uploadImage(file, imageType)
      if (res?.data?.user) {
        setUser(res.data.user)
      }
    } catch (err) {
      console.warn('Image upload error:', err.response?.data)
    } finally {
      setUploading(false)
    }
  }

  // Step 1 Validation (Mandatory: City & Country)
  const canProceedStep1 = city.trim() !== '' && country.trim() !== ''

  // Step 2 Validation (Mandatory: At least 1 Skill)
  const canProceedStep2 = skills.length > 0

  return (
    <div className="min-h-screen bg-white flex flex-col justify-between p-6 sm:p-12">
      {/* ── Top Navigation & Brand Bar ───────────────────────────────────── */}
      <header className="max-w-3xl mx-auto w-full flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <img src="/logo.png" alt="FreelanceFlow" className="w-8 h-8 object-contain" />
          <span className="text-lg font-extrabold text-gray-900 tracking-tight">
            Freelance<span className="text-primary-600">Flow</span>
          </span>
        </div>
        <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
          Step {step} of 5
        </span>
      </header>

      {/* ── Main Content Area ───────────────────────────────────────────── */}
      <main className="max-w-3xl mx-auto w-full py-10 space-y-8 flex-1 flex flex-col justify-center">
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-gray-900 h-full transition-all duration-300 rounded-full"
            style={{ width: `${(step / 5) * 100}%` }}
          />
        </div>

        {/* Step Headings */}
        <div className="space-y-2">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight">
            {step === 1 && 'Where are you located?'}
            {step === 2 && 'What are your top skills?'}
            {step === 3 && 'Set your hourly rate & bio'}
            {step === 4 && 'Add portfolio & experience level'}
            {step === 5 && 'Add your profile photo & banner'}
          </h1>
          <p className="text-base text-gray-500 font-normal">
            {step === 1 && 'Address details are required for client contract compliance.'}
            {step === 2 && 'Select at least 1 primary skill to match with relevant project opportunities.'}
            {step === 3 && 'Optional: You can set your hourly rate & bio now or skip and edit anytime later.'}
            {step === 4 && 'Optional: Share your portfolio link or skip to finish setup.'}
            {step === 5 && 'Optional: Upload a profile photo and cover banner — you can always change them later.'}
          </p>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl font-medium">
            {error}
          </div>
        )}

        {/* ── STEP 1: Address Details (Mandatory) ───────────────────────── */}
        {step === 1 && (
          <div className="space-y-6 pt-2 animate-in fade-in duration-200">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                  City <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={city}
                  onChange={e => setCity(e.target.value)}
                  placeholder="e.g. San Francisco, New York, Mumbai"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                  Country <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={country}
                  onChange={e => setCountry(e.target.value)}
                  placeholder="e.g. United States, India, United Kingdom"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                Street Address (Optional)
              </label>
              <input
                type="text"
                value={address}
                onChange={e => setAddress(e.target.value)}
                placeholder="Street address or locality"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium transition-all"
              />
            </div>

            <div className="pt-6 flex justify-end">
              <button
                type="button"
                disabled={!canProceedStep1}
                onClick={() => setStep(2)}
                className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next: Skills & Expertise <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 2: Skills & Expertise (Mandatory) ────────────────────── */}
        {step === 2 && (
          <div className="space-y-6 pt-2 animate-in fade-in duration-200">
            {/* Selected Skills Summary Container */}
            {skills.length > 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-2xl p-4 space-y-2.5">
                <div className="flex items-center justify-between text-xs font-bold text-gray-700">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-primary-600" />
                    Your Selected Skills ({skills.length})
                  </span>
                  <span className="text-gray-400 font-medium text-[11px]">Click × on tag to remove</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {skills.map(s => (
                    <span
                      key={s}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-900 text-white rounded-xl text-xs font-semibold shadow-sm animate-in fade-in zoom-in-95 duration-150"
                    >
                      {s}
                      <button
                        type="button"
                        onClick={() => toggleSkill(s)}
                        className="hover:bg-white/20 rounded-full p-0.5 text-gray-300 hover:text-white transition-colors"
                        title="Remove skill"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-3.5 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium rounded-xl flex items-center gap-2">
                <span>Please select at least 1 skill or add your custom skills below to proceed.</span>
              </div>
            )}

            {/* Custom Skill Input */}
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700">
                Add Custom Skill
              </label>
              <div className="flex gap-2.5">
                <input
                  type="text"
                  value={customSkill}
                  onChange={e => setCustomSkill(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      addCustomSkill(e)
                    }
                  }}
                  placeholder="Type any skill (e.g. AWS, Kubernetes, Vue.js, Go) and press Add..."
                  className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium"
                />
                <button
                  type="button"
                  onClick={addCustomSkill}
                  disabled={!customSkill.trim()}
                  className="bg-gray-900 hover:bg-black text-white font-bold text-xs px-5 rounded-xl transition-all shadow-sm disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Skill
                </button>
              </div>
            </div>

            {/* Popular Skills Pills */}
            <div className="space-y-2.5 pt-2">
              <span className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                Or pick from popular skills:
              </span>
              <div className="flex flex-wrap gap-2">
                {POPULAR_SKILLS.map(skill => {
                  const isSelected = skills.includes(skill)
                  return (
                    <button
                      key={skill}
                      type="button"
                      onClick={() => toggleSkill(skill)}
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all border ${
                        isSelected
                          ? 'bg-primary-50 border-primary-400 text-primary-800 shadow-sm'
                          : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {isSelected ? '✓ ' : '+ '}{skill}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="pt-6 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-gray-500 hover:text-gray-900 text-sm font-semibold flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                type="button"
                disabled={!canProceedStep2}
                onClick={() => setStep(3)}
                className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next: Bio & Rate <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 3: Bio & Hourly Rate (Optional) ──────────────────────── */}
        {step === 3 && (
          <div className="space-y-6 pt-2 animate-in fade-in duration-200">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700">
                  Hourly Rate ($ / hour)
                </label>
                <span className="text-[11px] text-gray-400 font-medium">Max $1,000 / hr</span>
              </div>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold text-base">$</span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1000"
                  value={hourlyRate}
                  onChange={e => setHourlyRate(e.target.value)}
                  placeholder="e.g. 45.00"
                  className={`w-full pl-9 pr-4 py-3 border rounded-xl focus:outline-none focus:ring-2 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium ${
                    parseFloat(hourlyRate) > 1000 || parseFloat(hourlyRate) < 0
                      ? 'border-red-400 focus:ring-red-500'
                      : 'border-gray-200 focus:ring-gray-900'
                  }`}
                />
              </div>
              {parseFloat(hourlyRate) > 1000 && (
                <p className="text-red-600 text-xs mt-1.5 font-medium">
                  Hourly rate cannot exceed $1,000 / hr.
                </p>
              )}
              {parseFloat(hourlyRate) < 0 && (
                <p className="text-red-600 text-xs mt-1.5 font-medium">
                  Hourly rate cannot be negative.
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                Professional Overview / Bio
              </label>
              <textarea
                rows={4}
                value={bio}
                onChange={e => setBio(e.target.value)}
                placeholder="Describe your background, core technical skills, and experience..."
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium resize-none"
              />
            </div>

            <div className="pt-6 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="text-gray-500 hover:text-gray-900 text-sm font-semibold flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => setStep(4)}
                  className="text-gray-400 hover:text-gray-700 font-semibold text-sm flex items-center gap-1"
                >
                  Skip step <SkipForward className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  disabled={parseFloat(hourlyRate) > 1000 || parseFloat(hourlyRate) < 0}
                  onClick={() => setStep(4)}
                  className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next: Portfolio <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 4: Portfolio & Experience Level (Optional) ────────────── */}
        {step === 4 && (
          <div className="space-y-6 pt-2 animate-in fade-in duration-200">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                Portfolio Website / GitHub Link
              </label>
              <input
                type="text"
                value={portfolioWebsite}
                onChange={e => setPortfolioWebsite(e.target.value)}
                placeholder="https://github.com/yourusername or yourportfolio.com"
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium ${
                  portfolioWebsite.trim() && !isValidUrl(portfolioWebsite)
                    ? 'border-red-400 focus:ring-red-500'
                    : 'border-gray-200 focus:ring-gray-900'
                }`}
              />
              {portfolioWebsite.trim() && !isValidUrl(portfolioWebsite) && (
                <p className="text-red-600 text-xs mt-1.5 font-medium">
                  Please enter a valid URL (e.g. https://github.com/username or https://myportfolio.com)
                </p>
              )}
              {portfolioWebsite.trim() && isValidUrl(portfolioWebsite) && (
                <p className="text-emerald-600 text-xs mt-1.5 font-medium flex items-center gap-1">
                  ✓ Valid link format
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                Experience Level
              </label>
              <select
                value={experienceLevel}
                onChange={e => setExperienceLevel(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium"
              >
                <option value="Entry">Entry Level (1-2 years experience)</option>
                <option value="Intermediate">Intermediate (3-5 years experience)</option>
                <option value="Expert">Expert (5+ years experience)</option>
              </select>
            </div>

            <div className="pt-6 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(3)}
                className="text-gray-500 hover:text-gray-900 text-sm font-semibold flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => setStep(5)}
                  className="text-gray-400 hover:text-gray-700 font-semibold text-sm flex items-center gap-1"
                >
                  Skip <SkipForward className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => setStep(5)}
                  className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2"
                >
                  Next: Photos <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 5: Profile Photo & Banner (Optional) ──────────────────── */}
        {step === 5 && (
          <div className="space-y-8 pt-2 animate-in fade-in duration-200">

            {/* Banner Upload */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-3">
                Cover / Banner Image
              </label>
              <div
                onClick={() => bannerInputRef.current?.click()}
                className="relative w-full h-36 bg-gray-100 border-2 border-dashed border-gray-300 rounded-2xl overflow-hidden cursor-pointer hover:border-gray-500 transition-all group"
              >
                {bannerPreview ? (
                  <img src={bannerPreview} alt="Banner" className="w-full h-full object-cover" />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-gray-400">
                    <ImageIcon className="w-8 h-8" />
                    <span className="text-xs font-semibold">Click to upload cover image</span>
                    <span className="text-[10px]">Recommended: 1200×300px JPG/PNG</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <Upload className="w-6 h-6 text-white" />
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
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-3">
                Profile Photo
              </label>
              <div className="flex items-center gap-6">
                <div
                  onClick={() => avatarInputRef.current?.click()}
                  className="relative w-24 h-24 rounded-full bg-gray-200 border-4 border-white shadow-md overflow-hidden cursor-pointer hover:opacity-80 transition-all group flex-shrink-0"
                >
                  {avatarPreview ? (
                    <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Camera className="w-7 h-7 text-gray-400" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-full">
                    <Upload className="w-5 h-5 text-white" />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Upload profile picture</p>
                  <p className="text-xs text-gray-500 mt-0.5">Square image, min 200×200px. JPG/PNG/WebP.</p>
                  <button
                    type="button"
                    onClick={() => avatarInputRef.current?.click()}
                    className="mt-2 text-xs font-bold text-gray-900 underline underline-offset-2 hover:text-gray-600"
                  >
                    Choose file…
                  </button>
                </div>
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

            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(4)}
                className="text-gray-500 hover:text-gray-900 text-sm font-semibold flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  disabled={loading || uploadingAvatar || uploadingBanner}
                  onClick={() => handleSubmitProfile(true)}
                  className="text-gray-400 hover:text-gray-700 font-semibold text-sm flex items-center gap-1"
                >
                  Skip & Finish <SkipForward className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  disabled={loading || uploadingAvatar || uploadingBanner}
                  onClick={async () => {
                    // Upload images first (non-blocking if no Azure)
                    if (avatarFile) await uploadImage(avatarFile, 'avatar', setUploadingAvatar)
                    if (bannerFile) await uploadImage(bannerFile, 'banner', setUploadingBanner)
                    await handleSubmitProfile(true)
                  }}
                  className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2 disabled:opacity-60"
                >
                  {(loading || uploadingAvatar || uploadingBanner) ? 'Saving...' : 'Finish Setup & Go Home'} <CheckCircle className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* ── Minimal Footer ─────────────────────────────────────────────── */}
      <footer className="max-w-3xl mx-auto w-full text-center text-xs text-gray-400 pt-6">
        © {new Date().getFullYear()} FreelanceFlow Inc. All rights reserved.
      </footer>
    </div>
  )
}
