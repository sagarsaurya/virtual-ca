import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App'

// Auto-inject auth token on every /api/* call — no page changes needed
const _fetch = window.fetch
window.fetch = function(url, options = {}) {
  if (typeof url === 'string' && url.startsWith('/api/')) {
    const token = localStorage.getItem('auth_token')
    if (token) {
      options = {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`,
        },
      }
    }
  }
  return _fetch(url, options)
}

const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<React.StrictMode><App /></React.StrictMode>)
