import api from './axiosConfig'

export const projectsAPI = {
  // Get all projects (with optional filters)
  getProjects: (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.budget_min) params.append('budget_min', filters.budget_min)
    if (filters.budget_max) params.append('budget_max', filters.budget_max)
    if (filters.skills) params.append('skills', filters.skills)
    if (filters.search) params.append('search', filters.search)
    if (filters.page) params.append('page', filters.page)
    
    return api.get('/projects/', { params })
  },

  // Get single project
  getProject: (id) => api.get(`/projects/${id}/`),

  // Create project (client only)
  createProject: (data) => api.post('/projects/', data),

  // Update project (owner only)
  updateProject: (id, data) => api.patch(`/projects/${id}/`, data),

  // Close/delete project (owner only)
  closeProject: (id) => api.delete(`/projects/${id}/`),

  // Get client's projects
  getMyProjects: () => api.get('/projects/my_projects/'),

  // Get project bids (for project detail page)
  getProjectBids: (projectId) => api.get(`/projects/${projectId}/bids/`),
}

export default projectsAPI
