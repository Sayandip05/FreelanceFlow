import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MapPin, Wrench, DollarSign, Globe, Briefcase,
  CheckCircle, ArrowRight, ArrowLeft, SkipForward, Plus, X
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { usersAPI } from '../../api/auth'

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

  // Save profile state to backend
  const handleSubmitProfile = async (completedOnboarding = true) => {
    setLoading(true)
    setError('')
    try {
      let formattedPortfolio = portfolioWebsite.trim()
      if (formattedPortfolio && !formattedPortfolio.startsWith('http://') && !formattedPortfolio.startsWith('https://')) {
        formattedPortfolio = `https://${formattedPortfolio}`
      }

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

  // Step 1 Validation (Mandatory: City & Country)
  const canProceedStep1 = city.trim() !== '' && country.trim() !== ''

  // Step 2 Validation (Mandatory: At least 1 Skill)
  const canProceedStep2 = skills.length > 0

  return (
    <div className="min-h-screen bg-white flex flex-col justify-between p-6 sm:p-12">
      {/* ── Top Navigation & Brand Bar ───────────────────────────────────── */}
      <header className="max-w-3xl mx-auto w-full flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gray-900 rounded-xl flex items-center justify-center text-white font-black text-sm">
            <Briefcase className="w-4 h-4" />
          </div>
          <span className="text-lg font-extrabold text-gray-900 tracking-tight">FreelanceFlow</span>
        </div>
        <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
          Step {step} of 4
        </span>
      </header>

      {/* ── Main Content Area ───────────────────────────────────────────── */}
      <main className="max-w-3xl mx-auto w-full py-10 space-y-8 flex-1 flex flex-col justify-center">
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-gray-900 h-full transition-all duration-300 rounded-full"
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>

        {/* Step Headings */}
        <div className="space-y-2">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight">
            {step === 1 && 'Where are you located?'}
            {step === 2 && 'What are your top skills?'}
            {step === 3 && 'Set your hourly rate & bio'}
            {step === 4 && 'Add portfolio & experience level'}
          </h1>
          <p className="text-base text-gray-500 font-normal">
            {step === 1 && 'Address details are required for client contract compliance.'}
            {step === 2 && 'Select at least 1 primary skill to match with relevant project opportunities.'}
            {step === 3 && 'Optional: You can set your hourly rate & bio now or skip and edit anytime later.'}
            {step === 4 && 'Optional: Share your portfolio link or skip to finish setup.'}
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
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                Select your primary skills ({skills.length} selected)
              </span>
            </div>

            {/* Clean Skill Pills */}
            <div className="flex flex-wrap gap-2.5">
              {POPULAR_SKILLS.map(skill => {
                const isSelected = skills.includes(skill)
                return (
                  <button
                    key={skill}
                    type="button"
                    onClick={() => toggleSkill(skill)}
                    className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all border ${
                      isSelected
                        ? 'bg-gray-900 border-gray-900 text-white shadow-sm'
                        : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {isSelected ? '✓ ' : '+ '}{skill}
                  </button>
                )
              })}
            </div>

            {/* Custom Skill Input */}
            <form onSubmit={addCustomSkill} className="flex gap-3 pt-2">
              <input
                type="text"
                value={customSkill}
                onChange={e => setCustomSkill(e.target.value)}
                placeholder="Add custom skill (e.g. AWS, Vue.js)..."
                className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900"
              />
              <button
                type="submit"
                className="bg-gray-100 hover:bg-gray-200 text-gray-900 font-bold text-xs px-5 rounded-xl border border-gray-200 transition-colors"
              >
                Add Skill Tag
              </button>
            </form>

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
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                Hourly Rate ($ / hour)
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold text-base">$</span>
                <input
                  type="number"
                  step="0.01"
                  min="1"
                  value={hourlyRate}
                  onChange={e => setHourlyRate(e.target.value)}
                  placeholder="e.g. 45.00"
                  className="w-full pl-9 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium"
                />
              </div>
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
                  onClick={() => setStep(4)}
                  className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2"
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
                type="url"
                value={portfolioWebsite}
                onChange={e => setPortfolioWebsite(e.target.value)}
                placeholder="https://github.com/yourusername or portfolio URL"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm bg-gray-50/40 focus:bg-white text-gray-900 font-medium"
              />
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
                  onClick={() => handleSubmitProfile(true)}
                  className="text-gray-400 hover:text-gray-700 font-semibold text-sm flex items-center gap-1"
                >
                  Skip & Finish <SkipForward className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleSubmitProfile(true)}
                  className="bg-gray-900 hover:bg-black text-white px-8 py-3.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2"
                >
                  {loading ? 'Saving...' : 'Finish Setup & Go Home'} <CheckCircle className="w-4 h-4" />
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
