import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Building2, MapPin, Briefcase, User, Globe, Users,
  ArrowRight, ArrowLeft, CheckCircle, SkipForward
} from 'lucide-react'
import api from '../../api/axiosConfig'
import { useAuth } from '../../context/AuthContext'

const STEPS = [
  { id: 1, label: 'Your Details',   desc: 'Tell us about yourself' },
  { id: 2, label: 'Company Info',   desc: 'About your organization' },
  { id: 3, label: 'Background',     desc: "What you're looking for" },
]

const INDUSTRIES = [
  'Technology', 'Healthcare', 'Finance', 'Education', 'E-commerce',
  'Marketing', 'Real Estate', 'Media & Entertainment', 'Manufacturing',
  'Logistics', 'Legal', 'Non-Profit', 'Government', 'Other',
]

const COMPANY_SIZES = [
  { value: 'SOLO',    label: 'Just Me',         desc: 'Solo / Freelancer' },
  { value: 'SMALL',   label: '2–10',             desc: 'Small team' },
  { value: 'MEDIUM',  label: '11–50',            desc: 'Growing company' },
  { value: 'LARGE',   label: '51–200',           desc: 'Mid-size company' },
  { value: 'ENTERPRISE', label: '200+',          desc: 'Enterprise' },
]

const HIRING_FOR = [
  'Web Development', 'Mobile Apps', 'UI/UX Design', 'Data Science / AI',
  'DevOps / Cloud', 'Content Writing', 'Digital Marketing', 'Video / Animation',
  'Cybersecurity', 'Business Analysis', 'Finance & Accounting', 'Other',
]

/* ── Progress Bar ─────────────────────────────────────────────────────────── */
const StepBar = ({ current, total }) => (
  <div className="flex items-center gap-2 mb-8">
    {[...Array(total)].map((_, i) => (
      <div key={i} className="flex items-center gap-2 flex-1">
        <div className={`w-full h-1.5 rounded-full transition-all duration-500 ${
          i < current ? 'bg-gray-900' : 'bg-gray-200'
        }`} />
      </div>
    ))}
  </div>
)

/* ── Main ─────────────────────────────────────────────────────────────────── */
const extractNames = (u) => {
  if (!u) return { fName: '', lName: '' }
  let fName = (u.first_name || '').trim()
  let lName = (u.last_name || '').trim()
  if (!fName && u.full_name && !u.full_name.includes('@')) {
    const parts = u.full_name.trim().split(' ')
    fName = parts[0] || ''
    lName = parts.slice(1).join(' ') || ''
  }
  if (!fName && u.email) {
    const prefix = u.email.split('@')[0].replace(/[._-]/g, ' ')
    fName = prefix.charAt(0).toUpperCase() + prefix.slice(1)
  }
  return { fName, lName }
}

const ClientOnboardingPage = () => {
  const navigate = useNavigate()
  const { user, setUser, fetchUser } = useAuth()

  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const initialNames = extractNames(user)

  // Step 1 — Personal
  const [firstName, setFirstName] = useState(initialNames.fName)
  const [lastName, setLastName] = useState(initialNames.lName)
  const [city, setCity] = useState(user?.client_profile?.city || '')
  const [country, setCountry] = useState(user?.client_profile?.country || '')

  // Step 2 — Company
  const [companyName, setCompanyName] = useState(user?.client_profile?.company_name || '')
  const [companySize, setCompanySize] = useState(user?.client_profile?.company_size || '')
  const [industries, setIndustries] = useState(
    user?.client_profile?.industry
      ? user.client_profile.industry.split(',').map(s => s.trim()).filter(Boolean)
      : []
  )
  const [website, setWebsite] = useState(user?.client_profile?.website || '')

  // Step 3 — Background / Hiring intent
  const [hiringFor, setHiringFor] = useState([])
  const [bio, setBio] = useState(user?.client_profile?.bio || '')

  // Sync state whenever user in AuthContext updates
  useEffect(() => {
    if (user) {
      const { fName, lName } = extractNames(user)
      if (fName) setFirstName(prev => prev || fName)
      if (lName) setLastName(prev => prev || lName)
      const cp = user.client_profile || {}
      if (cp.city) setCity(prev => prev || cp.city)
      if (cp.country) setCountry(prev => prev || cp.country)
      if (cp.company_name) setCompanyName(prev => prev || cp.company_name)
      if (cp.company_size) setCompanySize(prev => prev || cp.company_size)
      if (cp.industry) {
        const parsed = cp.industry.split(',').map(s => s.trim()).filter(Boolean)
        if (parsed.length > 0) setIndustries(prev => prev.length > 0 ? prev : parsed)
      }
      if (cp.website) setWebsite(prev => prev || cp.website)
      if (cp.bio) setBio(prev => prev || cp.bio)
    }
  }, [user])

  // Also fetch fresh profile on mount to guarantee fields are populated
  useEffect(() => {
    api.get('/users/me/')
      .then(res => {
        if (res.data) {
          setUser(res.data)
          const { fName, lName } = extractNames(res.data)
          if (fName) setFirstName(prev => prev || fName)
          if (lName) setLastName(prev => prev || lName)
          const cp = res.data.client_profile || {}
          if (cp.city) setCity(prev => prev || cp.city)
          if (cp.country) setCountry(prev => prev || cp.country)
          if (cp.company_name) setCompanyName(prev => prev || cp.company_name)
          if (cp.company_size) setCompanySize(prev => prev || cp.company_size)
          if (cp.industry) {
            const parsed = cp.industry.split(',').map(s => s.trim()).filter(Boolean)
            if (parsed.length > 0) setIndustries(prev => prev.length > 0 ? prev : parsed)
          }
          if (cp.website) setWebsite(prev => prev || cp.website)
          if (cp.bio) setBio(prev => prev || cp.bio)
        }
      })
      .catch(err => {
        console.warn('Could not fetch user profile in onboarding:', err)
      })
  }, [setUser])

  const canStep1 = firstName.trim() && city.trim() && country.trim()
  const canStep2 = companySize && industries.length > 0

  const toggleIndustry = (ind) => {
    setIndustries(prev =>
      prev.includes(ind) ? prev.filter(i => i !== ind) : [...prev, ind]
    )
  }

  const toggleHiringFor = (item) => {
    setHiringFor(prev =>
      prev.includes(item) ? prev.filter(h => h !== item) : [...prev, item]
    )
  }

  const handleSubmit = async (skip = false) => {
    setLoading(true)
    setError('')
    try {
      const payload = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        city,
        country,
        company_name: companyName.trim(),
        company_size: companySize,
        industry: industries.join(', '),
        website: website.trim(),
        bio: skip ? '' : bio.trim(),
        is_onboarded: true,
      }
      const res = await api.patch('/users/me/', payload)
      setUser(res.data)
      navigate('/client/home')
    } catch (err) {
      console.error('Client onboarding error:', err)
      const data = err.response?.data
      let msg = 'Something went wrong. Please try again.'
      if (typeof data === 'string') msg = data
      else if (data?.detail) msg = data.detail
      else if (data?.message) msg = data.message
      else if (data && typeof data === 'object') {
        const key = Object.keys(data)[0]
        if (key) {
          const val = data[key]
          msg = `${key}: ${Array.isArray(val) ? val.join(', ') : val}`
        }
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <header className="h-14 border-b border-gray-100 px-6 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <img src="/logo.png" alt="FreelanceFlow" className="w-8 h-8 object-contain" />
          <span className="text-base font-extrabold text-gray-900 tracking-tight">
            Freelance<span className="text-indigo-600">Flow</span>
          </span>
        </div>
        <span className="text-xs text-gray-400 font-medium">Step {step} of {STEPS.length}</span>
      </header>

      {/* ── Main content ────────────────────────────────────────────────── */}
      <main className="flex-1 flex items-start justify-center px-4 py-10">
        <div className="w-full max-w-xl">
          {/* Step indicator */}
          <StepBar current={step} total={STEPS.length} />

          {/* Step title */}
          <div className="mb-8">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-1">
              {STEPS[step - 1].desc}
            </p>
            <h1 className="text-3xl font-extrabold text-gray-900">
              {STEPS[step - 1].label}
            </h1>
          </div>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
              {error}
            </div>
          )}

          {/* ── STEP 1: Personal Details ──────────────────────────────── */}
          {step === 1 && (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                    First Name <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={firstName}
                      onChange={e => setFirstName(e.target.value)}
                      placeholder="Jane"
                      className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                    Last Name
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={lastName}
                      onChange={e => setLastName(e.target.value)}
                      placeholder="Doe"
                      className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                  City <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={city}
                    onChange={e => setCity(e.target.value)}
                    placeholder="San Francisco"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                  Country <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={country}
                    onChange={e => setCountry(e.target.value)}
                    placeholder="United States"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  type="button"
                  disabled={!canStep1}
                  onClick={() => setStep(2)}
                  className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next: Company Info <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 2: Company Info ──────────────────────────────────── */}
          {step === 2 && (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                  Company / Organization Name
                </label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={companyName}
                    onChange={e => setCompanyName(e.target.value)}
                    placeholder="Acme Corp (or leave blank if solo)"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-3">
                  Team / Company Size <span className="text-red-500">*</span>
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {COMPANY_SIZES.map(s => (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() => setCompanySize(s.value)}
                      className={`p-3 rounded-xl border-2 text-left transition-all ${
                        companySize === s.value
                          ? 'border-gray-900 bg-gray-900 text-white'
                          : 'border-gray-200 hover:border-gray-400 text-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <Users className="w-3.5 h-3.5 opacity-70" />
                        <span className="text-sm font-bold">{s.label}</span>
                      </div>
                      <p className={`text-xs ${companySize === s.value ? 'text-gray-300' : 'text-gray-500'}`}>
                        {s.desc}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Industry / Sector <span className="text-red-500">*</span>
                </label>
                <p className="text-xs text-gray-400 mb-3">Select all sectors that apply to your company</p>
                <div className="flex flex-wrap gap-2">
                  {INDUSTRIES.map(ind => {
                    const isSelected = industries.includes(ind)
                    return (
                      <button
                        key={ind}
                        type="button"
                        onClick={() => toggleIndustry(ind)}
                        className={`px-4 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                          isSelected
                            ? 'bg-gray-900 text-white border-gray-900 shadow-sm'
                            : 'border-gray-200 text-gray-600 hover:border-gray-400'
                        }`}
                      >
                        {isSelected && '✓ '}{ind}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                  Website (optional)
                </label>
                <div className="relative">
                  <Globe className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  <input
                    type="url"
                    value={website}
                    onChange={e => setWebsite(e.target.value)}
                    placeholder="https://yourcompany.com"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900"
                  />
                </div>
              </div>

              <div className="pt-4 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="text-gray-500 hover:text-gray-900 text-sm font-semibold flex items-center gap-1.5"
                >
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
                <button
                  type="button"
                  disabled={!canStep2}
                  onClick={() => setStep(3)}
                  className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next: Background <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 3: Background & Intent (Optional) ───────────────── */}
          {step === 3 && (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-3">
                  What are you mainly hiring for?
                </label>
                <div className="flex flex-wrap gap-2">
                  {HIRING_FOR.map(item => {
                    const selected = hiringFor.includes(item)
                    return (
                      <button
                        key={item}
                        type="button"
                        onClick={() => toggleHiringFor(item)}
                        className={`px-4 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                          selected
                            ? 'bg-gray-900 text-white border-gray-900'
                            : 'border-gray-200 text-gray-600 hover:border-gray-400'
                        }`}
                      >
                        {selected && '✓ '}{item}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                  Brief Background / What you do
                </label>
                <textarea
                  rows={4}
                  value={bio}
                  onChange={e => setBio(e.target.value)}
                  placeholder="Tell freelancers a bit about your company and the types of projects you typically work on..."
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium resize-none"
                />
              </div>

              <div className="pt-4 flex items-center justify-between">
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
                    disabled={loading}
                    onClick={() => handleSubmit(true)}
                    className="text-gray-400 hover:text-gray-700 font-semibold text-sm flex items-center gap-1"
                  >
                    Skip & Finish <SkipForward className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => handleSubmit(false)}
                    className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2 disabled:opacity-60"
                  >
                    {loading ? 'Saving...' : 'Finish Setup & Go Home'} <CheckCircle className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="max-w-3xl mx-auto w-full text-center text-xs text-gray-400 py-6">
        © {new Date().getFullYear()} FreelanceFlow Inc. All rights reserved.
      </footer>
    </div>
  )
}

export default ClientOnboardingPage
