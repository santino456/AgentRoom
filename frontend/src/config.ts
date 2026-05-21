// Agent Coop Frontend Configuration
// Use VITE_ prefixed env vars for Vite builds, fallback to current host

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export const WS_BASE =
  import.meta.env.VITE_WS_BASE_URL ||
  (window.location.protocol === 'https:' ? 'wss:' : 'ws:') +
    '//' +
    window.location.host
