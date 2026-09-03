/**
 * Resolves the WebSocket base URL dynamically.
 * - In local development: ws://localhost:8000
 * - In production (e.g. Vercel connecting to EC2 backend): wss://freelanceflow.backend.debabrata.site
 */
export function getWebSocketBaseUrl() {
  const apiUrl = import.meta.env.VITE_API_URL
  if (apiUrl) {
    try {
      const parsed = new URL(apiUrl)
      const protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${parsed.host}`
    } catch (e) {
      console.warn('Failed to parse VITE_API_URL for WebSocket:', e)
    }
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
  return `${protocol}//${host}`
}

/**
 * Builds a full WebSocket URL for a given path and token/query params.
 * Example: getWebSocketUrl('/ws/notifications/', { token: myToken })
 */
export function getWebSocketUrl(path, queryParams = {}) {
  const base = getWebSocketBaseUrl()
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const searchParams = new URLSearchParams(queryParams)
  const queryString = searchParams.toString() ? `?${searchParams.toString()}` : ''
  return `${base}${cleanPath}${queryString}`
}
