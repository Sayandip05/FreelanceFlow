import api from './axiosConfig'

export const searchAPI = {
  // Unified search (projects and freelancers)
  search: (query, filters = {}) => {
    const params = new URLSearchParams()
    if (query) params.append('q', query)
    if (filters.type) params.append('type', filters.type)
    if (filters.skills) params.append('skills', filters.skills)
    if (filters.budget_min) params.append('budget_min', filters.budget_min)
    if (filters.budget_max) params.append('budget_max', filters.budget_max)
    
    return api.get('/search/', { params })
  },

  // Search projects only
  searchProjects: (query, skills = '') => {
    const params = new URLSearchParams()
    if (query) params.append('q', query)
    if (skills) params.append('skills', skills)
    
    return api.get('/search/projects/', { params })
  },

  // Search freelancers only
  searchFreelancers: (query, skills = '') => {
    const params = new URLSearchParams()
    if (query) params.append('q', query)
    if (skills) params.append('skills', skills)
    
    return api.get('/search/freelancers/', { params })
  },
}

export default searchAPI
