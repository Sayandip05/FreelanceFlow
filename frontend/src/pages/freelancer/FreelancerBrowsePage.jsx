import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, IndianRupee, Clock, Tag, ArrowRight, ShieldCheck, CheckCircle, Sparkles } from 'lucide-react'
import { projectsAPI } from '../../api/projects'
import { bidsAPI } from '../../api/bids'
import { Skeleton } from '../../components/common/Skeleton'
import { formatCurrency } from '../../utils/formatCurrency'

/* ── FreelanceFlow Auto-Scrolling Banner Carousel ───────────────────────── */
const FREELANCER_SLIDES = [
  {
    src: '/images/freelancer dashboard 1.png',
    alt: 'Freelancer Dashboard 1',
  },
  {
    src: '/images/freelancer dashboard 2.png',
    alt: 'Freelancer Dashboard 2',
  },
  {
    src: '/images/freelancer dashboard 3.png',
    alt: 'Freelancer Dashboard 3',
  },
]

const BannerCarousel = () => {
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent(prev => (prev + 1) % FREELANCER_SLIDES.length)
    }, 4000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="relative w-full rounded-2xl overflow-hidden shadow-sm border border-gray-200/80 mb-6 bg-white aspect-[3.2/1]">
      {FREELANCER_SLIDES.map((slide, i) => (
        <img
          key={i}
          src={slide.src}
          alt={slide.alt}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ease-in-out ${
            i === current ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        />
      ))}

      {/* Sliding Dot indicators inside the image */}
      <div className="absolute bottom-3 right-5 flex items-center gap-1.5 z-10 bg-black/25 backdrop-blur-md px-2.5 py-1 rounded-full border border-white/20">
        {FREELANCER_SLIDES.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrent(idx)}
            className={`rounded-full transition-all duration-300 ${
              idx === current ? 'w-5 h-1.5 bg-white shadow' : 'w-1.5 h-1.5 bg-white/50 hover:bg-white/75'
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
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Auto-scrolling Announcement Banner Carousel at top of Home */}
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
          <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={budgetFilter}
            onChange={e => setBudgetFilter(e.target.value)}
            className="pl-9 pr-8 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white appearance-none"
          >
            <option value="">Any Budget</option>
            <option value="low">Under ₹500</option>
            <option value="mid">₹500 – ₹2,000</option>
            <option value="high">₹2,000+</option>
          </select>
        </div>
        <button type="submit" className="btn-primary px-5">Search</button>
      </form>

      {/* Results */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-3xl border border-gray-100 p-6 space-y-4 shadow-xs">
              <div className="flex justify-between items-start">
                <div className="space-y-2 flex-1 max-w-lg">
                  <Skeleton className="h-6 w-3/4 rounded-xl" />
                  <Skeleton className="h-4 w-1/2 rounded-lg" />
                </div>
                <Skeleton className="h-8 w-28 rounded-xl" />
              </div>
              <Skeleton className="h-12 w-full rounded-xl" />
              <div className="flex gap-2">
                <Skeleton className="h-6 w-16 rounded-lg" />
                <Skeleton className="h-6 w-20 rounded-lg" />
                <Skeleton className="h-6 w-24 rounded-lg" />
              </div>
            </div>
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
              className="bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-md hover:border-gray-200 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="px-2.5 py-0.5 bg-green-50 text-green-700 text-[11px] font-semibold rounded-full flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" /> Escrow Protected
                    </span>
                  </div>
                  
                  {/* Title (Constant Black) */}
                  <h3 className="font-bold text-gray-900 text-lg mb-1 flex items-center gap-2">
                    {project.title}
                  </h3>
                  
                  {/* Description preview */}
                  <p className="text-gray-600 text-sm leading-relaxed line-clamp-2 mb-3">
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
                    <p className="text-2xl font-extrabold text-gray-900 mb-0.5">{formatCurrency(project.budget)}</p>
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
