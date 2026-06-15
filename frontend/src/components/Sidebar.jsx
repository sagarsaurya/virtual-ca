import { useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getCompanies, addCompany, deleteCompany } from '../api'

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const [companies, setCompanies] = useState([])
  const [currentCompany, setCurrentCompany] = useState(null)
  const [showMenu, setShowMenu] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [newName, setNewName] = useState('')

  useEffect(() => {
    getCompanies().then(r => {
      setCompanies(r.data)
      const saved = localStorage.getItem('company_id')
      const found = r.data.find(c => c.id == saved) || r.data[0]
      if (found) { setCurrentCompany(found); localStorage.setItem('company_id', found.id) }
    }).catch(() => {})
  }, [])

  const switchCompany = (c) => {
    setCurrentCompany(c)
    localStorage.setItem('company_id', c.id)
    setShowMenu(false)
    window.location.reload()
  }

  const doAddCompany = () => {
    if (!newName.trim()) return
    addCompany(newName.trim()).then(r => {
      setCompanies(prev => [...prev, r.data])
      switchCompany(r.data)
      setShowAddModal(false)
      setNewName('')
    })
  }

  const nav = (path) => navigate(path)
  const active = (path) => location.pathname === path ? 'nav-item active' : 'nav-item'

  return (
    <div className="sidebar fixed top-0 left-0 h-full flex flex-col z-50 overflow-y-auto">
      {/* Logo */}
      <div className="px-6 py-5" style={{borderBottom:'1px solid rgba(255,255,255,0.06)'}}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{background:'rgba(201,168,76,0.15)',border:'1px solid rgba(201,168,76,0.25)'}}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" stroke="#C9A84C" strokeWidth="1.8" strokeLinejoin="round"/>
              <path d="M12 22V12M2 7l10 5 10-5" stroke="#C9A84C" strokeWidth="1.8"/>
            </svg>
          </div>
          <div>
            <div className="font-display font-bold text-base tracking-tight" style={{color:'#F0EAD8'}}>VirtualCA</div>
            <div className="text-xs" style={{color:'#2E4A62'}}>AI Accountant</div>
          </div>
        </div>
      </div>

      {/* User chip */}
      <div className="mx-4 mt-4 px-3 py-2.5 rounded-xl flex items-center gap-3" style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.06)'}}>
        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0" style={{background:'rgba(201,168,76,0.2)',color:'var(--gold-400)',border:'1px solid rgba(201,168,76,0.3)'}}>S</div>
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate" style={{color:'#D0C8B8'}}>Sagar Pathak</div>
          <div className="text-xs flex items-center gap-1" style={{color:'#2E7D32'}}>
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block"></span>Active
          </div>
        </div>
      </div>

      {/* Company Switcher */}
      <div className="mx-4 mt-3 relative">
        <div className="text-xs mb-1.5 font-semibold uppercase tracking-wide" style={{color:'#2E4A62'}}>Company</div>
        <button onClick={() => setShowMenu(!showMenu)} className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left transition" style={{background:'rgba(201,168,76,0.08)',border:'1px solid rgba(201,168,76,0.2)',color:'var(--gold-300)'}}>
          <i className="fas fa-building text-xs" style={{color:'var(--gold-500)'}}></i>
          <span className="flex-1 text-xs font-semibold truncate">{currentCompany?.name || 'Loading…'}</span>
          <i className="fas fa-chevron-down text-xs" style={{color:'#2E4A62'}}></i>
        </button>
        {showMenu && (
          <div className="absolute left-0 right-0 mt-1 rounded-xl overflow-hidden z-50" style={{background:'var(--navy-700)',border:'1px solid var(--navy-500)',boxShadow:'0 8px 32px rgba(0,0,0,0.5)'}}>
            <div className="max-h-48 overflow-y-auto py-1">
              {companies.map(c => (
                <button key={c.id} onClick={() => switchCompany(c)} className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-white/5 transition" style={{color: c.id === currentCompany?.id ? 'var(--gold-400)' : '#94a3b8'}}>
                  <i className="fas fa-building text-xs"></i>{c.name}
                  {c.id === currentCompany?.id && <i className="fas fa-check ml-auto text-xs" style={{color:'var(--gold-400)'}}></i>}
                </button>
              ))}
            </div>
            <div style={{borderTop:'1px solid var(--navy-600)'}}>
              <button onClick={() => { setShowAddModal(true); setShowMenu(false) }} className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium transition hover:bg-white/5" style={{color:'#34d399'}}>
                <i className="fas fa-plus text-xs"></i> Add Company
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 pb-4 mt-2">
        <div className="nav-section-label">Workspace</div>
        <div className={active('/dashboard')} onClick={() => nav('/dashboard')}><i className="fas fa-th-large nav-icon"></i><span className="nav-label">Dashboard</span></div>
        <div className={active('/history')} onClick={() => nav('/history')}><i className="fas fa-clock-rotate-left nav-icon"></i><span className="nav-label">History</span></div>

        <div className="nav-section-label">Audit</div>
        <div className={active('/quickaudit')} onClick={() => nav('/quickaudit')}><i className="fas fa-magnifying-glass-dollar nav-icon"></i><span className="nav-label">Quick Audit</span></div>
        <div className={active('/fullaudit')} onClick={() => nav('/fullaudit')}>
          <i className="fas fa-clipboard-check nav-icon"></i><span className="nav-label">Full Audit</span>
          <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded-full" style={{background:'rgba(201,168,76,0.15)',color:'var(--gold-400)'}}>New</span>
        </div>
        <div className={active('/doc-checker')} onClick={() => nav('/doc-checker')}><i className="fas fa-file-circle-exclamation nav-icon"></i><span className="nav-label">Missing Docs</span></div>

        <div className="nav-section-label">Financial Reports</div>
        <div className={active('/balance-sheet')} onClick={() => nav('/balance-sheet')}><i className="fas fa-scale-balanced nav-icon"></i><span className="nav-label">Balance Sheet</span></div>
        <div className={active('/cash-flow')} onClick={() => nav('/cash-flow')}><i className="fas fa-water nav-icon"></i><span className="nav-label">Cash Flow (AS-3)</span></div>

        <div className="nav-section-label">Tax & Compliance</div>
        <div className={active('/tds-detect')} onClick={() => nav('/tds-detect')}><i className="fas fa-triangle-exclamation nav-icon"></i><span className="nav-label">TDS Detector</span></div>
        <div className={active('/gst-return')} onClick={() => nav('/gst-return')}><i className="fas fa-file-invoice nav-icon"></i><span className="nav-label">GST Returns</span></div>
        <div className={active('/tds')} onClick={() => nav('/tds')}><i className="fas fa-percent nav-icon"></i><span className="nav-label">TDS Analysis</span></div>
        <div className={active('/compliance')} onClick={() => nav('/compliance')}><i className="fas fa-calendar-check nav-icon"></i><span className="nav-label">Compliance Calendar</span></div>

        <div className="nav-section-label">Investments</div>
        <div className={active('/shares-pnl')} onClick={() => nav('/shares-pnl')}><i className="fas fa-chart-line nav-icon"></i><span className="nav-label">Shares P&L</span></div>
        <div className={active('/broker-rec')} onClick={() => nav('/broker-rec')}><i className="fas fa-handshake nav-icon"></i><span className="nav-label">Broker Rec</span></div>

        <div className="nav-section-label">Reconciliation</div>
        <div className={active('/party-rec')} onClick={() => nav('/party-rec')}><i className="fas fa-right-left nav-icon"></i><span className="nav-label">Party Ledger Rec</span></div>
        <div className={active('/bankrec')} onClick={() => nav('/bankrec')}><i className="fas fa-building-columns nav-icon"></i><span className="nav-label">Bank Reconciliation</span></div>

        <div className="nav-section-label">AI &amp; Guides</div>
        <div className={active('/askca')} onClick={() => nav('/askca')}>
          <i className="fas fa-comments nav-icon"></i><span className="nav-label">Ask Your CA</span>
          <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded-full" style={{background:'rgba(201,168,76,0.15)',color:'var(--gold-400)'}}>AI</span>
        </div>
        <div className={active('/journal')} onClick={() => nav('/journal')}><i className="fas fa-book-open nav-icon"></i><span className="nav-label">Journal Entry Guide</span></div>

        <div className="nav-section-label">Admin</div>
        <div className={active('/admin')} onClick={() => nav('/admin')}><i className="fas fa-sliders nav-icon"></i><span className="nav-label">Admin Panel</span></div>
      </nav>

      {/* Logout */}
      <div className="px-4 py-3" style={{borderTop:'1px solid rgba(255,255,255,0.05)'}}>
        <button onClick={() => { localStorage.clear(); navigate('/') }} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 transition">
          <i className="fas fa-arrow-right-from-bracket w-4 text-sm" style={{color:'#2E4A62'}}></i>
          <span className="text-xs" style={{color:'#2E4A62'}}>Sign out</span>
        </button>
      </div>

      {/* Add Company Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-box p-6 max-w-sm" onClick={e => e.stopPropagation()}>
            <div className="font-semibold text-base mb-4" style={{color:'#f1f5f9'}}>Add Company</div>
            <input value={newName} onChange={e => setNewName(e.target.value)} onKeyDown={e => e.key==='Enter' && doAddCompany()}
              type="text" placeholder="Company name (e.g. ABC Pvt Ltd)"
              className="w-full text-sm rounded-xl px-4 py-3 mb-4 focus:outline-none"
              style={{background:'var(--navy-700)',border:'1px solid var(--navy-500)',color:'#e2e8f0'}} autoFocus />
            <div className="flex gap-3">
              <button onClick={doAddCompany} className="btn-gold px-5 py-2.5 rounded-xl text-sm font-semibold flex-1">Add</button>
              <button onClick={() => setShowAddModal(false)} className="btn-primary px-5 py-2.5 rounded-xl text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
