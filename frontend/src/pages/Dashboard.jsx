import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboard, getFilesStatus } from '../api'

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState({})
  const [meta, setMeta] = useState({})

  useEffect(() => {
    Promise.all([getDashboard(), getFilesStatus()])
      .then(([d, m]) => { setData(d.data); setMeta(m.data) })
      .catch(() => {})
  }, [])

  const score = data.last_score
  const critical = data.last_critical
  const warnings = data.last_warnings
  const total = data.total_audits || 0
  const files = ['tb','db','bs','pnl','bstmt','btally']
  const present = files.filter(f => meta[f+'_exists'] || meta[f]).length
  const pct = Math.round((present / files.length) * 100)

  const scoreColor = score >= 75 ? '#34d399' : score >= 50 ? '#f59e0b' : '#f87171'
  const scoreLabel = score >= 75 ? 'Good' : score >= 50 ? 'Needs Attention' : score != null ? 'High Risk' : 'No audit yet'

  return (
    <div style={{padding:'24px 28px',overflowY:'auto',height:'calc(100vh - 64px)'}}>

      {/* ROW 1: 3 cards */}
      <div className="grid gap-5 mb-5" style={{gridTemplateColumns:'1fr 1fr 1fr'}}>
        <div className="rounded-2xl p-5 cursor-pointer" style={{background:'linear-gradient(135deg,var(--navy-700) 0%,var(--navy-800) 100%)',border:'1px solid var(--navy-500)',opacity:0.75}}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-base font-bold" style={{color:'#f1f5f9'}}>AI Audit Manager</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{background:'rgba(201,168,76,0.2)',color:'var(--gold-400)',border:'1px solid rgba(201,168,76,0.3)'}}>Beta</span>
            <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded-full" style={{background:'#1e293b',color:'#475569',border:'1px solid #334155'}}>Soon</span>
          </div>
          <p className="text-xs mb-4" style={{color:'#64748b'}}>Your personal AI auditor that analyzes, explains and guides you to 100% compliance</p>
          <div className="flex gap-2">
            <button className="btn-gold px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 opacity-50"><i className="fas fa-play text-xs"></i> Start AI Audit</button>
          </div>
        </div>
        <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs font-semibold" style={{color:'#64748b'}}>AI Auditor Status</div>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{background:'#1e293b',color:'#475569',border:'1px solid #334155'}}>Soon</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0" style={{background:'rgba(201,168,76,0.1)',border:'1px solid rgba(201,168,76,0.2)'}}>
              <i className="fas fa-robot text-2xl" style={{color:'var(--gold-400)',opacity:0.5}}></i>
            </div>
            <div><div className="text-sm font-semibold mb-0.5" style={{color:'#475569'}}>AI analysis not available</div><div className="text-xs" style={{color:'#334155'}}>Coming soon</div></div>
          </div>
        </div>
        <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-xs font-semibold mb-3" style={{color:'#64748b'}}>Next Action Required</div>
          {!meta.tb_exists
            ? <><div className="text-sm font-bold mb-1" style={{color:'#f1f5f9'}}>Upload Trial Balance</div><div className="text-xs mb-3" style={{color:'#64748b'}}>Required to start audit</div><button onClick={() => navigate('/quickaudit')} className="w-full py-2 rounded-xl text-xs font-bold" style={{background:'rgba(201,168,76,0.15)',color:'var(--gold-300)',border:'1px solid rgba(201,168,76,0.3)'}}><i className="fas fa-upload mr-1"></i>Upload Now</button></>
            : critical > 0
            ? <><div className="text-sm font-bold mb-1" style={{color:'#f87171'}}>{critical} Critical Issues Found</div><div className="text-xs mb-3" style={{color:'#64748b'}}>Review and resolve before filing</div><button onClick={() => navigate('/quickaudit')} className="w-full py-2 rounded-xl text-xs font-bold" style={{background:'rgba(248,113,113,0.15)',color:'#f87171',border:'1px solid rgba(248,113,113,0.3)'}}><i className="fas fa-eye mr-1"></i>View Issues</button></>
            : <><div className="text-sm font-bold mb-1" style={{color:'#34d399'}}>All Clear!</div><div className="text-xs mb-3" style={{color:'#64748b'}}>No critical issues found</div><button onClick={() => navigate('/askca')} className="w-full py-2 rounded-xl text-xs font-bold" style={{background:'rgba(52,211,153,0.15)',color:'#34d399',border:'1px solid rgba(52,211,153,0.3)'}}><i className="fas fa-comments mr-1"></i>Ask Your CA</button></>
          }
        </div>
      </div>

      {/* ROW 2: 5 score cards */}
      <div className="grid grid-cols-5 gap-4 mb-5">
        <div className="rounded-2xl p-4" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-xs font-semibold mb-1" style={{color:'#64748b'}}>Health Score</div>
          <div className="text-3xl font-black mb-1" style={{color: scoreColor}}>{score != null ? score+'%' : '—'}</div>
          <div className="progress-bar mb-1"><div className="progress-fill" style={{width:(score||0)+'%'}}></div></div>
          <div className="text-xs" style={{color:'#64748b'}}>{scoreLabel}</div>
        </div>
        <div className="rounded-2xl p-4" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-xs font-semibold mb-1" style={{color:'#64748b'}}>Audit Status</div>
          <div className="text-xl font-black mb-1" style={{color: critical === 0 ? '#34d399' : '#f87171'}}>{critical != null ? (critical===0 ? 'PASSED' : 'ISSUES') : '—'}</div>
          <div className="text-xs" style={{color:'#64748b'}}>{critical != null ? `${critical} Critical · ${warnings||0} Warnings` : 'Not run yet'}</div>
        </div>
        <div className="rounded-2xl p-4 relative" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-xs font-semibold mb-1" style={{color:'#64748b'}}>GST Readiness</div>
          <div className="text-3xl font-black mb-1" style={{color:'#64748b'}}>—</div>
          <div className="text-xs" style={{color:'#475569'}}>Coming Soon</div>
          <span className="absolute top-3 right-3 text-xs font-bold px-2 py-0.5 rounded-full" style={{background:'#1e293b',color:'#475569',border:'1px solid #334155'}}>Soon</span>
        </div>
        <div className="rounded-2xl p-4 relative" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-xs font-semibold mb-1" style={{color:'#64748b'}}>ITR Readiness</div>
          <div className="text-3xl font-black mb-1" style={{color:'#64748b'}}>—</div>
          <div className="text-xs" style={{color:'#475569'}}>Coming Soon</div>
          <span className="absolute top-3 right-3 text-xs font-bold px-2 py-0.5 rounded-full" style={{background:'#1e293b',color:'#475569',border:'1px solid #334155'}}>Soon</span>
        </div>
        <div className="rounded-2xl p-4" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-xs font-semibold mb-1" style={{color:'#64748b'}}>Data Completeness</div>
          <div className="text-3xl font-black mb-1" style={{color: pct>=80?'#34d399':pct>=50?'#f59e0b':'#f87171'}}>{pct}%</div>
          <div className="text-xs" style={{color:'#64748b'}}>{present} of 6 files uploaded</div>
        </div>
      </div>

      {/* ROW 3: Recent + Journey */}
      <div className="grid gap-5 mb-5" style={{gridTemplateColumns:'1.5fr 1fr'}}>
        <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-bold" style={{color:'#f1f5f9'}}>Recent Analyses</span>
            <button onClick={() => navigate('/history')} className="text-xs font-medium" style={{color:'var(--gold-400)'}}>View all →</button>
          </div>
          {!data.recent || data.recent.length === 0
            ? <div className="flex flex-col items-center justify-center py-8 text-center">
                <i className="fas fa-folder-open text-xl mb-2" style={{color:'#334155'}}></i>
                <div className="text-xs" style={{color:'#475569'}}>No audits yet</div>
                <button onClick={() => navigate('/quickaudit')} className="btn-gold mt-3 text-xs px-4 py-2 rounded-xl font-semibold">Run First Audit</button>
              </div>
            : data.recent.map((a, i) => {
                const dt = a.audited_at ? new Date(a.audited_at).toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}) : ''
                return (
                  <div key={i} onClick={() => navigate('/quickaudit')} className="flex items-center gap-3 p-3 rounded-xl cursor-pointer mb-2 transition" style={{border:'1px solid var(--navy-600)',background:'var(--navy-700)'}}>
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{background:'rgba(201,168,76,0.15)'}}><i className="fas fa-file-excel text-xs" style={{color:'var(--gold-400)'}}></i></div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-xs truncate" style={{color:'#f1f5f9'}}>{a.filename||'Trial Balance'}</div>
                      <div className="text-xs mt-0.5" style={{color:'#475569'}}>{dt}</div>
                    </div>
                    {a.critical > 0 ? <span className="tag-critical">{a.critical} Critical</span> : <span className="tag-ok">Clear</span>}
                  </div>
                )
              })
          }
        </div>
        <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-bold" style={{color:'#f1f5f9'}}>Audit Journey</span>
            <button onClick={() => navigate('/fullaudit')} className="text-xs font-medium" style={{color:'var(--gold-400)'}}>View full →</button>
          </div>
          {[
            {label:'Trial Balance Uploaded', done: !!meta.tb},
            {label:'P&L Uploaded', done: !!meta.pnl},
            {label:'Balance Sheet Uploaded', done: !!meta.bs},
            {label:'Bank Statement Uploaded', done: !!meta.bstmt},
            {label:'Initial Audit Completed', done: total > 0},
            {label:'GST Analysis', done: false, soon: true},
            {label:'ITR Readiness', done: false, soon: true},
          ].map((s, i) => (
            <div key={i} className="flex items-center gap-2.5 py-1.5" style={{borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
              <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{background: s.done?'rgba(52,211,153,0.2)':'var(--navy-700)',border:`1px solid ${s.done?'rgba(52,211,153,0.4)':'var(--navy-500)'}`}}>
                <i className={`fas ${s.done?'fa-check':'fa-circle'}`} style={{color:s.done?'#34d399':'#334155',fontSize:'8px'}}></i>
              </div>
              <span className="text-xs flex-1" style={{color:s.done?'#e2e8f0':'#475569'}}>{s.label}</span>
              {s.soon && <span className="text-xs font-bold px-1.5 py-0.5 rounded-full" style={{background:'#1e293b',color:'#334155',border:'1px solid #334155',fontSize:'9px'}}>Soon</span>}
            </div>
          ))}
        </div>
      </div>

      {/* ROW 4: Quick Actions */}
      <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
        <div className="text-sm font-bold mb-4" style={{color:'#f1f5f9'}}>Quick Actions</div>
        <div className="grid grid-cols-5 gap-3">
          {[
            {icon:'fa-clipboard-check',color:'#818cf8',bg:'rgba(129,140,248,0.15)',label:'Run Full Audit',desc:'Deep analysis of all transactions',path:'/fullaudit'},
            {icon:'fa-right-left',color:'#60a5fa',bg:'rgba(96,165,250,0.15)',label:'Bank Reconciliation',desc:'Reconcile bank statements',path:'/bankrec'},
            {icon:'fa-percent',color:'#34d399',bg:'rgba(52,211,153,0.15)',label:'GST Analysis',desc:'Check GST compliance & mismatches',path:null},
            {icon:'fa-file-invoice-dollar',color:'#fbbf24',bg:'rgba(251,191,36,0.15)',label:'Generate Reports',desc:'Generate financial & compliance reports',path:null},
            {icon:'fa-calendar-check',color:'#f87171',bg:'rgba(248,113,113,0.15)',label:'Compliance Calendar',desc:'View upcoming deadlines',path:'/compliance'},
          ].map((a, i) => (
            <button key={i} onClick={() => a.path && navigate(a.path)} className="rounded-xl p-4 text-left transition hover:brightness-110" style={{background:'var(--navy-700)',border:'1px solid var(--navy-600)',opacity: a.path ? 1 : 0.6}}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-2" style={{background:a.bg}}><i className={`fas ${a.icon} text-sm`} style={{color:a.color}}></i></div>
              <div className="text-xs font-semibold mb-0.5" style={{color:'#e2e8f0'}}>{a.label}</div>
              <div className="text-xs" style={{color:'#475569'}}>{a.desc}</div>
              {!a.path && <span className="text-xs font-bold px-1.5 py-0.5 rounded-full mt-1 inline-block" style={{background:'#1e293b',color:'#475569',border:'1px solid #334155',fontSize:'9px'}}>Soon</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
