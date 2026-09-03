import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, Star, MapPin, Briefcase, ChevronRight, Filter,
  X, Sparkles, Clock, CheckCircle, TrendingUp, Shield, Users
} from 'lucide-react'
import { searchAPI } from '../../api/search'
import { formatCurrency } from '../../utils/formatCurrency'

/* ── Announcement Banner (same feel as Freelancer home) ─────────────────── */
const CLIENT_SLIDES = [
  {
    src: '/images/client dashboard 1.png',
    alt: 'Client Dashboard 1',
  },
  {
    src: '/images/client dashboard 2.png',
    alt: 'Client Dashboard 2',
  },
  {
    src: '/images/client dashboard 3.png',
    alt: 'Client Dashboard 3',
  },
]

const BannerCarousel = () => {
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => setCurrent(prev => (prev + 1) % CLIENT_SLIDES.length), 4000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="relative w-full rounded-2xl overflow-hidden shadow-sm border border-gray-200/80 mb-6 bg-white aspect-[3.2/1]">
      {CLIENT_SLIDES.map((slide, i) => (
        <img
          key={i}
          src={slide.src}
          alt={slide.alt}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ease-in-out ${i === current ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
        />
      ))}

      {/* Sliding Dot indicators inside the image */}
      <div className="absolute bottom-3 right-5 flex items-center gap-1.5 z-10 bg-black/25 backdrop-blur-md px-2.5 py-1 rounded-full border border-white/20">
        {CLIENT_SLIDES.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            className={`rounded-full transition-all duration-300 ${i === current ? 'w-5 h-1.5 bg-white shadow' : 'w-1.5 h-1.5 bg-white/50 hover:bg-white/75'
              }`}
            title={`Slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}

/* ── Freelancer Card ─────────────────────────────────────────────────────── */
const FreelancerCard = ({ freelancer }) => {
  const navigate = useNavigate()
  const profile = freelancer.freelancer_profile || {}
  const skills = profile.skills || freelancer.skills || []
  const name = freelancer.full_name || (freelancer.first_name ? `${freelancer.first_name} ${freelancer.last_name || ''}`.trim() : '') || freelancer.email?.split('@')[0] || 'Freelancer'
  const initials = name.split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'FL'
  const bannerImage = profile.banner_image || freelancer.banner_image
  const avatarImage = profile.avatar || freelancer.avatar

  const avgRating = typeof profile.average_rating === 'number'
    ? profile.average_rating.toFixed(1)
    : profile.average_rating || null

  return (
    <div
      onClick={() => navigate(`/client/freelancers/${freelancer.id}`)}
      className="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-lg hover:border-gray-200 transition-all duration-200 cursor-pointer group flex flex-col h-full"
    >
      {/* Banner */}
      <div className="relative h-24 w-full bg-slate-100 shrink-0">
        {bannerImage ? (
          <img
            src={bannerImage}
            alt="Banner"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-r from-slate-200 to-gray-300" />
        )}
        {/* Avatar overlapping banner */}
        <div className="absolute -bottom-6 left-4">
          <div className="w-14 h-14 rounded-full border-4 border-white shadow-md overflow-hidden bg-slate-200 text-slate-700 flex items-center justify-center">
            {avatarImage ? (
              <img src={avatarImage} alt={name} className="w-full h-full object-cover" />
            ) : (
              <span className="font-bold text-base text-slate-600">{initials}</span>
            )}
          </div>
        </div>
        {/* Verified badge */}
        {(profile.is_onboarded || freelancer.is_onboarded) && (
          <div className="absolute top-2 right-2">
            <span className="flex items-center gap-1 text-[10px] text-emerald-600 bg-white/90 px-2 py-0.5 rounded-full font-bold shadow-sm">
              <CheckCircle className="w-3 h-3" /> Verified
            </span>
          </div>
        )}
      </div>

      {/* Body — flex flex-col flex-1 justify-between */}
      <div className="px-4 pt-8 pb-4 flex flex-col flex-1 justify-between">
        {/* Main Content Area */}
        <div className="flex flex-col flex-1">
          {/* Name + meta */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="min-w-0">
              <h3 className="font-bold text-gray-900 group-hover:text-gray-700 transition-colors truncate leading-tight">
                {name}
              </h3>
              <div className="flex items-center gap-2 flex-wrap mt-0.5">
                {profile.city && (
                  <span className="flex items-center gap-1 text-[11px] text-gray-400">
                    <MapPin className="w-3 h-3" /> {profile.city}{profile.country ? `, ${profile.country}` : ''}
                  </span>
                )}
                {profile.experience_level && (
                  <span className="text-[11px] text-gray-400 capitalize">
                    · {profile.experience_level.toLowerCase().replace('_', ' ')}
                  </span>
                )}
              </div>
            </div>
            {profile.hourly_rate && (
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-extrabold text-gray-900">{formatCurrency(profile.hourly_rate)}</p>
                <p className="text-[10px] text-gray-400 font-medium">/hr</p>
              </div>
            )}
          </div>

          {/* Rating + reviews */}
          <div className="flex items-center gap-2 mb-2.5 min-h-[1.5rem]">
            <span className="flex items-center gap-1 text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200/80 px-2 py-0.5 rounded-md">
              <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" /> {avgRating || '5.0'}
            </span>
            <span className="text-[11px] text-gray-400 font-medium">
              ({profile.total_reviews || freelancer.total_reviews || 0} {((profile.total_reviews || freelancer.total_reviews) === 1) ? 'review' : 'reviews'})
            </span>
          </div>

          {/* Bio snippet — fixed 2-line height so all cards align identically */}
          <div className="h-9 mb-3 overflow-hidden">
            <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
              {profile.bio || 'Professional freelancer ready to collaborate on your projects.'}
            </p>
          </div>

          {/* Skills — fixed 2-row height container */}
          <div className="h-14 mb-2 overflow-hidden flex flex-wrap gap-1.5 content-start">
            {skills.length > 0 ? (
              <>
                {skills.slice(0, 4).map((skill, i) => (
                  <span key={i} className="text-[11px] bg-gray-100 text-gray-800 border border-gray-200/60 px-2.5 py-0.5 rounded-full font-medium whitespace-nowrap">
                    {skill}
                  </span>
                ))}
                {skills.length > 4 && (
                  <span className="text-[11px] bg-gray-100 text-gray-500 border border-gray-200/40 px-2.5 py-0.5 rounded-full font-medium whitespace-nowrap">
                    +{skills.length - 4}
                  </span>
                )}
              </>
            ) : (
              <span className="text-[11px] text-gray-400 italic py-0.5">No skills listed</span>
            )}
          </div>
        </div>

        {/* View Profile Button — permanently fixed to the bottom baseline */}
        <div className="pt-2 mt-auto">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              navigate(`/client/freelancers/${freelancer.id}`)
            }}
            className="w-full flex items-center justify-center gap-2 py-2 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 hover:border-gray-300 hover:text-gray-900 hover:bg-gray-50 transition-all cursor-pointer"
          >
            View Profile <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── Skeleton Card ───────────────────────────────────────────────────────── */
const SkeletonCard = () => (
  <div className="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
    <div className="flex items-start gap-4 mb-4">
      <div className="w-12 h-12 bg-gray-200 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-3 bg-gray-100 rounded w-1/2" />
        <div className="h-3 bg-gray-100 rounded w-1/3" />
      </div>
    </div>
    <div className="flex gap-1.5 mb-4">
      {[...Array(3)].map((_, i) => <div key={i} className="h-5 w-16 bg-gray-100 rounded-full" />)}
    </div>
    <div className="h-8 bg-gray-100 rounded-xl" />
  </div>
)

/* ── Main ClientHomePage ─────────────────────────────────────────────────── */
const ClientHomePage = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [freelancers, setFreelancers] = useState([])
  const [loading, setLoading] = useState(true)
  const debounceRef = useRef(null)

  // Debounce search query
  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setDebouncedQuery(query), 400)
    return () => clearTimeout(debounceRef.current)
  }, [query])

  useEffect(() => {
    const fetchFreelancers = async () => {
      setLoading(true)
      try {
        const res = await searchAPI.searchFreelancers(debouncedQuery)
        let results = res.data?.results || res.data || []
        // Sort by average rating descending (highest-rated first)
        results = [...results].sort((a, b) => {
          const aRating = parseFloat(a.freelancer_profile?.average_rating || 0)
          const bRating = parseFloat(b.freelancer_profile?.average_rating || 0)
          return bRating - aRating
        })
        setFreelancers(results)
      } catch (err) {
        console.error(err)
        setFreelancers([])
      } finally {
        setLoading(false)
      }
    }
    fetchFreelancers()
  }, [debouncedQuery])

  return (
    <div className="max-w-6xl mx-auto">
      {/* Banner */}
      <BannerCarousel />

      {/* Search Bar */}
      <div className="relative mb-6">
        <Search className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search freelancers by name, skill, or bio…"
          className="w-full pl-11 pr-10 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-transparent transition-all shadow-sm"
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Results header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">
            {loading ? 'Searching…' : `${freelancers.length} Freelancer${freelancers.length !== 1 ? 's' : ''} Found`}
          </h2>
          {debouncedQuery && !loading && (
            <p className="text-xs text-gray-500 mt-0.5">
              Showing results for "{debouncedQuery}"
            </p>
          )}
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : freelancers.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
          <Users className="w-14 h-14 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-gray-800 mb-1">No freelancers found</h3>
          <p className="text-sm text-gray-500 mb-6">Try adjusting your search terms.</p>
          {query && (
            <button
              onClick={() => setQuery('')}
              className="px-6 py-2.5 bg-slate-800 text-white text-sm font-semibold rounded-xl hover:bg-slate-900 transition-colors shadow-sm"
            >
              Clear Search
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {freelancers.map(f => (
            <FreelancerCard key={f.id} freelancer={f} />
          ))}
        </div>
      )}
    </div>
  )
}

export default ClientHomePage
