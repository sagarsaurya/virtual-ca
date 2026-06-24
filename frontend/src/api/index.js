import axios from 'axios'

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com',
})

// attach auth token (and legacy company id) to every request
API.interceptors.request.use(cfg => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    cfg.headers['Authorization'] = `Bearer ${token}`
  }
  // legacy fallback for admin/unauthenticated calls
  const cid = localStorage.getItem('company_id') || 1
  cfg.headers['X-Company-ID'] = cid
  return cfg
})

export const getCompanies    = ()      => API.get('/api/companies')
export const addCompany      = (name)  => API.post('/api/companies', { name })
export const deleteCompany   = (cid)   => API.delete(`/api/companies/${cid}`)
export const renameCompany   = (cid, name) => API.post(`/api/companies/${cid}/rename`, { name })

export const getDashboard    = ()      => API.get('/api/dashboard')
export const getFilesStatus  = ()      => API.get('/api/files/status')
export const getHistory      = ()      => API.get('/api/audit/history')
export const getCompliance   = ()      => API.get('/api/compliance')
export const getAdminStats   = ()      => API.get('/api/admin/stats')

export const uploadFiles     = (form)  => API.post('/api/upload/files', form)
export const runAudit        = (form)  => API.post('/api/audit', form)
export const runBankRec      = (form)  => API.post('/api/bankrec', form)
export const runCompleteAudit= (form)  => API.post('/api/complete-audit', form)

export const askCA           = (q, ctx) => API.post('/api/ca-chat', { question: q, context: ctx })
export const rerunCAQueries  = ()      => API.post('/api/rerun-ca-queries')
export const getJournalEntry = (q)    => API.post('/api/journal-entry', { query: q })

export default API
