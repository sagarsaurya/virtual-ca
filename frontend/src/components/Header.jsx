import { useNavigate } from 'react-router-dom'

function logout(navigate) {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_email')
  localStorage.removeItem('logged_in')
  navigate('/')
}

const titles = {
  '/dashboard': ['Dashboard', 'Welcome back, Sagar'],
  '/history': ['History', 'All your past audits'],
  '/bankrec': ['Bank Reconciliation', 'Match bank statement vs Tally'],
  '/quickaudit': ['Quick Audit', 'Ledgers, TDS, GST, loans, cash violations'],
  '/fullaudit': ['Full Audit', 'All 6 files — TB, Daybook, BS, P&L, Bank Statement, Bank Ledger'],
  '/tds': ['TDS Analysis', 'Section-wise TDS payable, deposited, pending & return mismatches'],
  '/compliance': ['Compliance Calendar', 'TDS, PT, GST, Advance Tax — real due dates'],
  '/askca': ['Ask Your CA', 'AI reads your uploaded data to answer specific questions'],
  '/journal': ['Journal Entry Guide', 'Get correct journal entries instantly'],
  '/admin': ['Admin Panel', 'Audit history and stats'],
}

export default function Header({ filesStatus }) {
  const navigate = useNavigate()
  const path = window.location.pathname
  const [title, sub] = titles[path] || ['VirtualCA', '']

  return (
    <div className="app-header px-8 py-3.5 flex items-center justify-between sticky top-0 z-40">
      <div>
        <h2 className="text-base font-semibold" style={{color:'#e2e8f0'}}>{title}</h2>
        <p className="text-xs mt-0.5" style={{color:'var(--ink-muted)'}}>{sub}</p>
      </div>
      <div className="flex items-center gap-3">
        {filesStatus?.tb_exists && (
          <div onClick={() => navigate('/quickaudit')} className="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer transition" style={{background:'rgba(201,168,76,0.08)',border:'1px solid rgba(201,168,76,0.2)'}}>
            <span className="w-1.5 h-1.5 rounded-full" style={{background:'var(--gold-500)'}}></span>
            <span className="text-xs font-semibold" style={{color:'var(--gold-500)'}}>Files loaded</span>
          </div>
        )}
        <button className="relative p-2 rounded-xl transition">
          <i className="fas fa-bell text-sm" style={{color:'var(--ink-muted)'}}></i>
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        <div className="text-xs font-medium px-3 py-1.5 rounded-lg" style={{background:'var(--navy-700)',color:'#94a3b8',border:'1px solid var(--navy-600)'}}>FY 2025–26</div>
        <button onClick={() => navigate('/quickaudit')} className="btn-gold px-4 py-2 rounded-xl text-sm">
          <i className="fas fa-arrow-up-from-bracket mr-2"></i>Upload Files
        </button>
        <button
          onClick={() => logout(navigate)}
          title={localStorage.getItem('auth_email') || 'Log out'}
          style={{background:'rgba(248,113,113,0.08)',border:'1px solid rgba(248,113,113,0.2)',color:'#f87171',borderRadius:'10px',padding:'7px 12px',fontSize:'12px',fontWeight:600,cursor:'pointer',display:'flex',alignItems:'center',gap:'6px'}}>
          <i className="fas fa-sign-out-alt"></i>
          <span style={{maxWidth:'120px',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
            {localStorage.getItem('auth_email') || 'Log out'}
          </span>
        </button>
      </div>
    </div>
  )
}
