import { useState } from 'react'
import axios from 'axios'

const API_URL = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'

export default function TDSAnalysis() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const cid = localStorage.getItem('company_id') || 1

  const run = async () => {
    setLoading(true)
    try {
      const r = await axios.post(`${API_URL}/api/audit`, {}, { headers: { 'X-Company-ID': cid } })
      setData(r.data)
    } catch { alert('Run a Quick Audit first to see TDS analysis') }
    setLoading(false)
  }

  const tds = data?.tds_analysis || []
  const salary = data?.salary_compliance || []

  return (
    <div className="p-8">
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="stat-card" style={{borderTop:'2px solid #f87171'}}>
          <div className="text-xs uppercase tracking-wider mb-2" style={{color:'#94a3b8'}}>TDS Sections Flagged</div>
          <div className="text-3xl font-bold" style={{color:'#f87171'}}>{tds.length || '—'}</div>
        </div>
        <div className="stat-card" style={{borderTop:'2px solid #fbbf24'}}>
          <div className="text-xs uppercase tracking-wider mb-2" style={{color:'#94a3b8'}}>Salary Issues</div>
          <div className="text-3xl font-bold" style={{color:'#fbbf24'}}>{salary.filter(s=>s.severity==='Critical').length || '—'}</div>
        </div>
        <div className="stat-card" style={{borderTop:'2px solid #34d399'}}>
          <div className="text-xs uppercase tracking-wider mb-2" style={{color:'#94a3b8'}}>Sections OK</div>
          <div className="text-3xl font-bold" style={{color:'#34d399'}}>{tds.filter(t=>t.severity==='OK').length || '—'}</div>
        </div>
      </div>

      {!data && !loading && (
        <div className="rounded-2xl p-12 text-center" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <i className="fas fa-percent text-4xl mb-4 block" style={{color:'#334155'}}></i>
          <div className="font-semibold mb-2" style={{color:'#f1f5f9'}}>No TDS data yet</div>
          <div className="text-sm mb-4" style={{color:'#64748b'}}>Run an audit to see TDS analysis</div>
          <button onClick={run} className="btn-gold px-6 py-3 rounded-xl text-sm font-bold">Run Audit</button>
        </div>
      )}

      {loading && (
        <div className="rounded-2xl p-8 text-center" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <i className="fas fa-cog text-3xl mb-3 block" style={{color:'var(--gold-400)',animation:'spin 1.5s linear infinite'}}></i>
          <div style={{color:'#f1f5f9'}}>Analyzing TDS...</div>
        </div>
      )}

      {tds.length > 0 && (
        <div className="rounded-2xl p-5 mb-4" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-sm font-bold mb-3" style={{color:'#f1f5f9'}}>TDS Section Analysis</div>
          {tds.map((t, i) => (
            <div key={i} className="entry-card p-3 mb-2 flex items-center gap-3">
              <span className={t.severity==='Critical' ? 'tag-critical' : t.severity==='Review' ? 'tag-review' : 'tag-ok'}>{t.severity}</span>
              <div className="flex-1 text-xs" style={{color:'#e2e8f0'}}>{t.section} — {t.description}</div>
              <div className="text-xs font-bold" style={{color:'#f87171'}}>₹{Number(t.amount||0).toLocaleString('en-IN')}</div>
            </div>
          ))}
        </div>
      )}

      {salary.length > 0 && (
        <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="text-sm font-bold mb-3" style={{color:'#f1f5f9'}}>Salary Compliance</div>
          {salary.map((s, i) => (
            <div key={i} className="entry-card p-3 mb-2 flex items-center gap-3">
              <span className={s.severity==='Critical' ? 'tag-critical' : 'tag-review'}>{s.severity}</span>
              <div className="flex-1 text-xs" style={{color:'#e2e8f0'}}>{s.employee} — {s.issue}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
