import { useEffect, useState } from 'react'
import { getAdminStats } from '../api'

export default function Admin() {
  const [stats, setStats] = useState({})

  useEffect(() => {
    getAdminStats().then(r => setStats(r.data)).catch(() => {})
  }, [])

  return (
    <div className="p-8">
      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="stat-card card-shadow">
          <div className="text-sm mb-1" style={{color:'#94a3b8'}}>Total Audits Run</div>
          <div className="text-3xl font-bold" style={{color:'#f1f5f9'}}>{stats.total_audits || '—'}</div>
        </div>
        <div className="stat-card card-shadow">
          <div className="text-sm mb-1" style={{color:'#94a3b8'}}>Last Score</div>
          <div className="text-3xl font-bold" style={{color:'#f59e0b'}}>{stats.last_score != null ? stats.last_score+'%' : '—'}</div>
        </div>
        <div className="stat-card card-shadow">
          <div className="text-sm mb-1" style={{color:'#94a3b8'}}>Critical Issues (last)</div>
          <div className="text-3xl font-bold" style={{color:'#f87171'}}>{stats.last_critical != null ? stats.last_critical : '—'}</div>
        </div>
      </div>

      <div className="rounded-2xl p-6" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
        <h3 className="font-semibold mb-4" style={{color:'#f1f5f9'}}>Audit History</h3>
        {!stats.history || stats.history.length === 0
          ? <div className="text-sm py-6 text-center" style={{color:'#475569'}}>No audits run yet</div>
          : stats.history.map((h, i) => (
            <div key={i} className="flex items-center gap-4 p-3 rounded-xl mb-2" style={{background:'var(--navy-700)',border:'1px solid var(--navy-600)'}}>
              <div className="flex-1 text-xs" style={{color:'#f1f5f9'}}>{h.filename||'Trial Balance'}</div>
              <div className="text-xs" style={{color:'#64748b'}}>{h.audited_at ? new Date(h.audited_at).toLocaleDateString('en-IN') : ''}</div>
              <div className="text-xs font-bold" style={{color:'#f59e0b'}}>{h.score}%</div>
              {h.critical > 0 ? <span className="tag-critical">{h.critical} Critical</span> : <span className="tag-ok">Clear</span>}
            </div>
          ))
        }
      </div>
    </div>
  )
}
