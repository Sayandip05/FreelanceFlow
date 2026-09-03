import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, MapPin, Briefcase, Star, IndianRupee, Mail, Globe, CheckCircle, ExternalLink
} from 'lucide-react'
import { usersAPI } from '../../api/auth'
import { formatCurrency } from '../../utils/formatCurrency'

const ClientFreelancerProfilePage = () => {
  const { freelancerId } = useParams()
  const navigate = useNavigate()
  const [freelancer, setFreelancer] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true)
      try {
        const res = await usersAPI.getUser(freelancerId)
        setFreelancer(res.data)
      } catch (err) {
        console.error(err)
        setError('Failed to load freelancer profile.')
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [freelancerId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !freelancer) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="text-center bg-white p-8 rounded-2xl border border-gray-100 shadow-sm max-w-md w-full">
          <p className="text-gray-600 mb-4">{error || 'Freelancer not found.'}</p>
          <button onClick={() => navigate('/client/home')} className="w-full py-2.5 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-colors">
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  const profile = freelancer.freelancer_profile || {}
  const skills = profile.skills || freelancer.skills || []
  const name = freelancer.full_name || (freelancer.first_name ? `${freelancer.first_name} ${freelancer.last_name || ''}`.trim() : '') || freelancer.email?.split('@')[0] || 'Freelancer'
  const initials = name.split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'FL'
  const bannerImage = profile.banner_image || freelancer.banner_image
  const avatarImage = profile.avatar || freelancer.avatar

  const avgRating = typeof profile.average_rating === 'number'
    ? profile.average_rating.toFixed(1)
    : profile.average_rating || 'N/A'

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <div className="bg-white rounded-3xl border border-gray-150 overflow-hidden shadow-sm">
        {/* Banner */}
        <div className="h-44 sm:h-52 w-full relative bg-slate-100">
          {bannerImage ? (
            <img src={bannerImage} alt="Banner" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-gradient-to-r from-slate-200 to-gray-300" />
          )}
        </div>

        {/* Profile Info Section */}
        <div className="px-6 sm:px-8 pb-8 relative pt-14">
          {/* Avatar overlay */}
          <div className="absolute -top-12 left-6 sm:left-8">
            <div className="w-24 h-24 rounded-full border-4 border-white shadow-md overflow-hidden bg-slate-200 text-slate-700 flex items-center justify-center">
              {avatarImage ? (
                <img src={avatarImage} alt={name} className="w-full h-full object-cover" />
              ) : (
                <span className="font-bold text-3xl text-slate-600">{initials}</span>
              )}
            </div>
          </div>

          {/* Main Info */}
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-black text-gray-900 flex items-center gap-2">
                  {name}
                  {profile.is_onboarded && (
                    <span className="flex items-center gap-0.5 text-[10px] text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-bold">
                      <CheckCircle className="w-3 h-3" /> Verified
                    </span>
                  )}
                </h1>
                
                {/* Meta details */}
                <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Briefcase className="w-4 h-4" /> {profile.experience_level || 'Intermediate'} Level
                  </span>
                  {profile.city && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" /> {profile.city}, {profile.country}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Mail className="w-4 h-4" /> {freelancer.email}
                  </span>
                </div>
              </div>

              {/* Price / Rating */}
              <div className="flex items-center gap-6 sm:text-right">
                {profile.hourly_rate && (
                  <div>
                    <p className="text-2xl font-black text-gray-900">{formatCurrency(profile.hourly_rate)}</p>
                    <p className="text-xs text-gray-400 font-medium">Hourly Rate</p>
                  </div>
                )}
                <div>
                  <p className="text-2xl font-black text-gray-900 flex items-center gap-1">
                    <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" /> {avgRating}
                  </p>
                  <p className="text-xs text-gray-400 font-medium">
                    {profile.total_reviews || 0} reviews
                  </p>
                </div>
              </div>
            </div>

            {/* Divider */}
            <hr className="my-6 border-gray-100" />

            {/* About / Bio */}
            {profile.bio && (
              <div className="mb-6">
                <h2 className="text-base font-bold text-gray-900 mb-2">About</h2>
                <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{profile.bio}</p>
              </div>
            )}

            {/* Skills */}
            {skills.length > 0 && (
              <div className="mb-6">
                <h2 className="text-base font-bold text-gray-900 mb-2.5">Skills & Expertise</h2>
                <div className="flex flex-wrap gap-2">
                  {skills.map((skill, idx) => (
                    <span key={idx} className="text-xs bg-gray-100 text-gray-800 border border-gray-200/70 px-3.5 py-1 rounded-full font-semibold">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Portfolio Link */}
            {profile.portfolio_website && (
              <div>
                <h2 className="text-base font-bold text-gray-900 mb-2">Portfolio / Links</h2>
                <a
                  href={profile.portfolio_website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-gray-800 hover:text-gray-900 font-medium underline underline-offset-2"
                >
                  <Globe className="w-4 h-4 text-gray-600" /> {profile.portfolio_website} <ExternalLink className="w-3.5 h-3.5 text-gray-500" />
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ClientFreelancerProfilePage
