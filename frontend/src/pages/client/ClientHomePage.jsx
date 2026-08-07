import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, Star, MapPin, Briefcase, ChevronRight, Filter,
  X, Sparkles, Clock, CheckCircle, TrendingUp, Shield, Users
} from 'lucide-react'
import { searchAPI } from '../../api/search'

/* ── Announcement Banner (same feel as Freelancer home) ─────────────────── */
const SLIDES = [
  {
    tag: 'Find Expert Talent',
    title: 'Search Verified Freelancers',
    description: 'Browse thousands of skilled professionals ready to work on your next project.',
    badge: 'TOP TALENT',
    color: 'from-gray-900 via-indigo-950 to-gray-900',
    badgeBg: 'bg-indigo-600 text-white',
  },
  {
    tag: 'Hire With Confidence',
    title: '100% Escrow-Protected Payments',
    description: 'Your funds are held securely until milestones are approved — zero risk, full control.',
    badge: 'RAZORPAY ESCROW',
    color: 'from-slate-900 via-emerald-950 to-slate-900',
    badgeBg: 'bg-emerald-600 text-white',
  },
  {
    tag: 'AI-Assisted Hiring',
    title: 'Smart Skill Matching & Recommendations',
    description: 'Our AI matches your project brief to the best available freelancers automatically.',
    badge: 'AI POWERED',
    color: 'from-zinc-900 via-purple-950 to-zinc-900',
    badgeBg: 'bg-purple-600 text-white',
  },
  {
    tag: 'Direct Messaging',
    title: 'Chat Before You Hire',
    description: 'Message any freelancer for free before making any commitment or payment.',
    badge: 'FREE CHAT',
    color: 'from-gray-900 via-blue-950 to-gray-900',
    badgeBg: 'bg-blue-600 text-white',
  },
]

const BannerCarousel = () => {
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => setCurrent(prev => (prev + 1) % SLIDES.length), 3500)
    return () => clearInterval(timer)
  }, [])

  const slide = SLIDES[current]

  return (
    <div className={`h-[190px] bg-gradient-to-r ${slide.color} text-white rounded-2xl p-6 shadow-xl relative overflow-hidden transition-all duration-500 border border-white/10 flex flex-col justify-between mb-6`}>
      <div className="absolute right-8 top-1/2 -translate-y-1/2 hidden md:flex flex-col gap-2.5 opacity-80 pointer-events-none">
        <div className="w-52 bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 shadow-xl transform -rotate-2">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-xs font-bold">JD</div>
            <div>
              <p className="text-xs font-semibold text-white">Jane Doe</p>
              <p className="text-[10px] text-white/60">Full-stack Developer</p>
            </div>
            <div className="ml-auto flex items-center gap-0.5">
              <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
              <span className="text-[10px] text-white/80">4.9</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1">
            {['React', 'Node.js', 'Python'].map(s => (
              <span key={s} className="text-[9px] bg-white/10 text-white/80 px-2 py-0.5 rounded-full">{s}</span>
            ))}
          </div>
        </div>
        <div className="w-52 bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 shadow-xl transform rotate-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-xs font-bold">AS</div>
            <div>
              <p className="text-xs font-semibold text-white">Alex S.</p>
              <p className="text-[10px] text-white/60">UI/UX Designer</p>
            </div>
            <div className="ml-auto flex items-center gap-0.5">
              <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
              <span className="text-[10px] text-white/80">5.0</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1">
            {['Figma', 'Adobe XD'].map(s => (
              <span key={s} className="text-[9px] bg-white/10 text-white/80 px-2 py-0.5 rounded-full">{s}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="relative z-10">
        <span className={`text-[10px] font-bold px-3 py-1 rounded-full ${slide.badgeBg} mb-3 inline-block tracking-wider`}>
          {slide.badge}
        </span>
        <p className="text-[11px] text-white/60 font-medium uppercase tracking-widest mb-1">{slide.tag}</p>
        <h2 className="text-xl font-extrabold leading-tight text-white mb-1">{slide.title}</h2>
      </div>

      <p className="text-xs text-white/70 max-w-xs relative z-10">{slide.description}</p>

      {/* Dot indicators */}
      <div className="absolute bottom-4 right-6 flex gap-1.5 z-10">
        {SLIDES.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            className={`rounded-full transition-all duration-300 ${i === current ? 'w-5 h-1.5 bg-white' : 'w-1.5 h-1.5 bg-white/40'}`}
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
  const skills = profile.skills || []
  const name = freelancer.first_name
    ? `${freelancer.first_name} ${freelancer.last_name || ''}`.trim()
    : freelancer.email?.split('@')[0] || 'Freelancer'
  const initials = name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  const avgRating = typeof profile.average_rating === 'number'
    ? profile.average_rating.toFixed(1)
    : profile.average_rating || null

  const BANNER_COLORS = [
    'from-indigo-600 to-purple-700',
    'from-blue-600 to-indigo-700',
    'from-emerald-600 to-teal-700',
    'from-pink-600 to-rose-700',
    'from-amber-500 to-orange-600',
    'from-violet-600 to-purple-700',
  ]
  const colorIdx = freelancer.id % BANNER_COLORS.length

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-lg hover:border-indigo-100 transition-all duration-200 cursor-pointer group">
      {/* Banner */}
      <div className="relative h-24 w-full">
        {profile.banner_image ? (
          <img
            src={profile.banner_image}
            alt="Banner"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className={`w-full h-full bg-gradient-to-r ${BANNER_COLORS[colorIdx]}`} />
        )}
        {/* Avatar overlapping banner */}
        <div className="absolute -bottom-6 left-4">
          <div className="w-14 h-14 rounded-full border-4 border-white shadow-md overflow-hidden bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            {profile.avatar ? (
              <img src={profile.avatar} alt={name} className="w-full h-full object-cover" />
            ) : (
              <span className="text-white font-bold text-base">{initials}</span>
            )}
          </div>
        </div>
        {/* Verified badge */}
        {profile.is_onboarded && (
          <div className="absolute top-2 right-2">
            <span className="flex items-center gap-1 text-[10px] text-emerald-600 bg-white/90 px-2 py-0.5 rounded-full font-bold shadow-sm">
              <CheckCircle className="w-3 h-3" /> Verified
            </span>
          </div>
        )}
      </div>

      {/* Body — 24px top padding to clear the avatar overlap */}
      <div className="px-4 pt-8 pb-4">
        {/* Name + meta */}
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="min-w-0">
            <h3 className="font-bold text-gray-900 group-hover:text-indigo-700 transition-colors truncate leading-tight">
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
              <p className="text-sm font-extrabold text-gray-900">${profile.hourly_rate}</p>
              <p className="text-[10px] text-gray-400 font-medium">/hr</p>
            </div>
          )}
        </div>

        {/* Rating + reviews */}
        {(avgRating || profile.total_reviews > 0) && (
          <div className="flex items-center gap-1.5 mb-2">
            {avgRating && (
              <span className="flex items-center gap-0.5 text-xs font-bold text-yellow-600">
                <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" /> {avgRating}
              </span>
            )}
            {profile.total_reviews > 0 && (
              <span className="text-[11px] text-gray-400">({profile.total_reviews} review{profile.total_reviews !== 1 ? 's' : ''})</span>
            )}
          </div>
        )}

        {/* Bio snippet */}
        {profile.bio && (
          <p className="text-xs text-gray-500 line-clamp-2 mb-3 leading-relaxed">{profile.bio}</p>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {skills.slice(0, 4).map((skill, i) => (
              <span key={i} className="text-[11px] bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-full font-medium">
                {skill}
              </span>
            ))}
            {skills.length > 4 && (
              <span className="text-[11px] bg-gray-100 text-gray-500 px-2.5 py-0.5 rounded-full font-medium">
                +{skills.length - 4}
              </span>
            )}
          </div>
        )}

        <button
          onClick={() => navigate(`/client/freelancers/${freelancer.id}`)}
          className="w-full flex items-center justify-center gap-2 py-2 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 hover:border-indigo-300 hover:text-indigo-700 hover:bg-indigo-50 transition-all"
        >
          View Profile <ChevronRight className="w-3.5 h-3.5" />
        </button>
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
const SKILL_FILTERS = ['All', 'React', 'Python', 'Node.js', 'Django', 'Design', 'Flutter', 'Go', 'DevOps', 'AI/ML']
const EXPERIENCE_FILTERS = ['All', 'Entry Level', 'Mid Level', 'Senior', 'Expert']

const ClientHomePage = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [selectedSkill, setSelectedSkill] = useState('All')
  const [selectedExp, setSelectedExp] = useState('All')
  const [freelancers, setFreelancers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showFilters, setShowFilters] = useState(false)
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
        const skillFilter = selectedSkill !== 'All' ? selectedSkill : ''
        const res = await searchAPI.searchFreelancers(debouncedQuery, skillFilter)
        let results = res.data?.results || res.data || []
        // Client-side experience filter (since API may not support it)
        if (selectedExp !== 'All') {
          const expMap = {
            'Entry Level': 'ENTRY',
            'Mid Level': 'MID',
            'Senior': 'SENIOR',
            'Expert': 'EXPERT',
          }
          results = results.filter(f =>
            (f.freelancer_profile?.experience_level || '').toUpperCase() === expMap[selectedExp]
          )
        }
        setFreelancers(results)
      } catch (err) {
        console.error(err)
        setFreelancers([])
      } finally {
        setLoading(false)
      }
    }
    fetchFreelancers()
  }, [debouncedQuery, selectedSkill, selectedExp])

  const clearFilters = () => {
    setQuery('')
    setSelectedSkill('All')
    setSelectedExp('All')
  }

  const hasFilters = query || selectedSkill !== 'All' || selectedExp !== 'All'

  return (
    <div className="max-w-6xl mx-auto">
      {/* Banner */}
      <BannerCarousel />

      {/* Search Bar */}
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search freelancers by name, skill, or bio…"
            className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all shadow-sm"
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
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium transition-all shadow-sm ${
            showFilters || hasFilters
              ? 'border-indigo-400 bg-indigo-50 text-indigo-700'
              : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
          }`}
        >
          <Filter className="w-4 h-4" />
          Filters
          {hasFilters && <span className="w-2 h-2 bg-indigo-500 rounded-full" />}
        </button>
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1 px-3 py-3 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <X className="w-3.5 h-3.5" /> Clear
          </button>
        )}
      </div>

      {/* Filter Drawer */}
      {showFilters && (
        <div className="bg-white border border-gray-100 rounded-2xl p-5 mb-5 shadow-sm">
          <div className="space-y-4">
            {/* Skill filter */}
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2.5">Skill</p>
              <div className="flex flex-wrap gap-2">
                {SKILL_FILTERS.map(s => (
                  <button
                    key={s}
                    onClick={() => setSelectedSkill(s)}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                      selectedSkill === s
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Experience filter */}
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2.5">Experience Level</p>
              <div className="flex flex-wrap gap-2">
                {EXPERIENCE_FILTERS.map(e => (
                  <button
                    key={e}
                    onClick={() => setSelectedExp(e)}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                      selectedExp === e
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Skill pill quick-filters (always visible) */}
      <div className="flex gap-2 overflow-x-auto pb-1 mb-5 scrollbar-hide">
        {SKILL_FILTERS.map(s => (
          <button
            key={s}
            onClick={() => setSelectedSkill(s)}
            className={`flex-shrink-0 px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
              selectedSkill === s
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-white border border-gray-200 text-gray-600 hover:border-indigo-300 hover:text-indigo-700'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Results header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">
            {loading ? 'Searching…' : `${freelancers.length} Freelancer${freelancers.length !== 1 ? 's' : ''} Found`}
          </h2>
          {hasFilters && !loading && (
            <p className="text-xs text-gray-500 mt-0.5">
              {debouncedQuery && `"${debouncedQuery}"`}
              {selectedSkill !== 'All' && ` · ${selectedSkill}`}
              {selectedExp !== 'All' && ` · ${selectedExp}`}
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
        <div className="text-center py-20">
          <Users className="w-14 h-14 text-gray-200 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-gray-700 mb-1">No freelancers found</h3>
          <p className="text-sm text-gray-400 mb-6">Try adjusting your search or filters.</p>
          <button
            onClick={clearFilters}
            className="px-6 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
          >
            Clear Filters
          </button>
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
