import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, DollarSign, Clock, Tag, ArrowRight, ShieldCheck, CheckCircle, Sparkles } from 'lucide-react'
import { projectsAPI } from '../../api/projects'
import { bidsAPI } from '../../api/bids'

/* ── FreelanceFlow Auto-Scrolling Banner Carousel ───────────────────────── */
const ANNOUNCEMENT_SLIDES = [
  {
    tag: 'Get hired 2X faster',
    title: 'Boosted Proposals & Escrow Protection',
    description: 'Submit competitive proposals backed by 100% Razorpay Escrow payment guarantees.',
    badge: 'BOOSTED',
    color: 'from-gray-900 via-primary-950 to-gray-900',
    badgeBg: 'bg-primary-600 text-white',
  },
  {
    tag: 'AI-Powered Productivity',
    title: 'Automated Daily & Weekly Worklogs',
    description: 'Log progress in real-time chat updates to automatically generate structured client reports.',
    badge: 'AI POWERED',
    color: 'from-slate-900 via-indigo-950 to-slate-900',
    badgeBg: 'bg-indigo-600 text-white',
  },
  {
    tag: '100% Escrow Security',
    title: 'Instant Milestone Escrow Releases',
    description: 'Project funds are deposited into Escrow upfront and released upon deliverable approval.',
    badge: 'RAZORPAY ESCROW',
    color: 'from-gray-900 via-emerald-950 to-gray-900',
    badgeBg: 'bg-emerald-600 text-white',
  },
  {
    tag: 'Verified Freelancer Badge',
    title: 'Build Reputation & Get Direct Hires',
    description: 'Complete contracts with 5-star ratings to unlock top-rated status and direct project invites.',
    badge: 'VERIFIED',
    color: 'from-zinc-900 via-purple-950 to-zinc-900',
    badgeBg: 'bg-purple-600 text-white',
  },
]

const BannerCarousel = () => {
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent(prev => (prev + 1) % ANNOUNCEMENT_SLIDES.length)
    }, 3500)
    return () => clearInterval(timer)
  }, [])

  const slide = ANNOUNCEMENT_SLIDES[current]

  return (
    <div className={`h-[210px] bg-gradient-to-r ${slide.color} text-white rounded-2xl p-6 sm:p-7 shadow-xl relative overflow-hidden transition-all duration-500 border border-white/10 flex flex-col justify-between`}>
      {/* Background Graphic Illustration Cards */}
      <div className="absolute right-8 top-1/2 -translate-y-1/2 hidden md:flex flex-col gap-2.5 opacity-90 pointer-events-none">
        <div className="w-60 bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 shadow-xl transform -rotate-2 transition-transform duration-500 hover:rotate-0">
          <div className="flex items-center justify-between mb-2">
            <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${slide.badgeBg}`}>
              {slide.badge}
            </span>
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          </div>
          <div className="h-2 w-3/4 bg-white/40 rounded mb-2" />
          <div className="h-2 w-1/2 bg-white/20 rounded" />
        </div>
        <div className="w-60 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-3.5 shadow-md transform rotate-2">
          <div className="h-2 w-4/5 bg-white/30 rounded mb-1.5" />
          <div className="h-2 w-2/3 bg-white/15 rounded" />
        </div>
      </div>

      {/* Slide Content */}
      <div className="max-w-xl z-10 space-y-2">
        <div>
          <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-primary-300 bg-white/10 px-3 py-1 rounded-full border border-white/10">
            <Sparkles className="w-3.5 h-3.5 text-yellow-400" /> {slide.tag}
          </span>
        </div>
        <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white leading-snug truncate">
          {slide.title}
        </h2>
        <p className="text-sm text-gray-300 leading-relaxed font-normal line-clamp-2">
          {slide.description}
        </p>
      </div>

      {/* Carousel Indicators / Progress Bars */}
      <div className="flex items-center gap-2 pt-2 z-10">
        {ANNOUNCEMENT_SLIDES.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrent(idx)}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              idx === current ? 'w-10 bg-white' : 'w-3 bg-white/30 hover:bg-white/50'
            }`}
            title={`Slide ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  )
}

/* ── Main Page Component ─────────────────────────────────────────────────── */
export default function FreelancerBrowsePage() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [budgetFilter, setBudgetFilter] = useState('')
  const [biddedProjectIds, setBiddedProjectIds] = useState(new Set())

  useEffect(() => {
    fetchProjects()
    fetchMyBids()
  }, [search, budgetFilter])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const filters = {}
      if (search) filters.search = search
      if (budgetFilter === 'low') { filters.budget_min = 0; filters.budget_max = 500 }
      else if (budgetFilter === 'mid') { filters.budget_min = 500; filters.budget_max = 2000 }
      else if (budgetFilter === 'high') { filters.budget_min = 2000 }
      const res = await projectsAPI.getProjects(filters)
      setProjects(res.data?.results || res.data || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const fetchMyBids = async () => {
    try {
      const res = await bidsAPI.getMyBids()
      const myBids = res.data?.results || res.data || []
      const ids = new Set(myBids.map(b => typeof b.project === 'object' ? b.project.id : b.project))
      setBiddedProjectIds(ids)
    } catch (e) {
      console.error(e)
    }
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchProjects()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Home</h1>
        <p className="text-gray-600 mt-1">Search and explore project opportunities</p>
      </div>

      {/* Auto-scrolling Announcement Banner Carousel right above Search Section */}
      <BannerCarousel />

      {/* Search & Filters */}
      <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3 pt-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search projects by title or skill..."
            className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white"
          />
        </div>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={budgetFilter}
            onChange={e => setBudgetFilter(e.target.value)}
            className="pl-9 pr-8 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white appearance-none"
          >
            <option value="">Any Budget</option>
            <option value="low">Under $500</option>
            <option value="mid">$500 – $2,000</option>
            <option value="high">$2,000+</option>
          </select>
        </div>
        <button type="submit" className="btn-primary px-5">Search</button>
      </form>

      {/* Results */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-36 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-gray-100">
          <Search className="w-14 h-14 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No projects found</h3>
          <p className="text-gray-500">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">{projects.length} project{projects.length !== 1 ? 's' : ''} found</p>
          {projects.map(project => (
            <div
              key={project.id}
              onClick={() => navigate(`/freelancer/projects/${project.id}`)}
              className="bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-md hover:border-primary-100 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="px-2.5 py-0.5 bg-green-50 text-green-700 text-[11px] font-semibold rounded-full flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" /> Escrow Protected
                    </span>
                  </div>
                  
                  {/* Title */}
                  <h3 className="font-bold text-gray-900 text-lg mb-1 group-hover:text-primary-600 transition-colors flex items-center gap-2">
                    {project.title}
                  </h3>
                  
                  {/* Short Description Summary Preview */}
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2 leading-relaxed">
                    {project.short_description || project.description}
                  </p>
                  
                  {/* Skills tags */}
                  {project.required_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {project.required_skills.map((skill, i) => (
                        <span key={i} className="px-2.5 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-lg font-medium flex items-center gap-1">
                          <Tag className="w-3 h-3 text-gray-400" /> {skill}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" /> Posted {new Date(project.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Right Column: Budget & Action */}
                <div className="text-right flex-shrink-0 flex flex-col justify-between h-full pt-1">
                  <div>
                    <p className="text-2xl font-extrabold text-gray-900 mb-0.5">${parseFloat(project.budget)?.toLocaleString()}</p>
                    <p className="text-xs text-gray-400 mb-4 font-medium">Fixed Budget</p>
                  </div>

                  {biddedProjectIds.has(project.id) ? (
                    <span className="text-xs text-green-700 bg-green-50 font-semibold px-3 py-1.5 rounded-xl inline-flex items-center justify-end gap-1">
                      <CheckCircle className="w-3.5 h-3.5" /> Bid Submitted
                    </span>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/freelancer/projects/${project.id}`)
                      }}
                      className="btn-primary text-sm px-4 py-2 flex items-center gap-1.5 ml-auto"
                    >
                      View Details & Apply <ArrowRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
