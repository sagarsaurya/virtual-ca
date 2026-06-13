import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getHistory } from '../api'

export default function History() {
  const [history, setHistory] = useState([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const navigate = useNavigate()

  useEffect(() => {
    getHistory().then(r => setHistory(r.data.history || r.data || [])).catch(() => {})
  }, [])

  const filtered = history.filter(h => {
    const matchSearch = !search || (h.filename||'').toLowerCase().includes(search.toLowerCase())
    const matchFilter = filter === 'all' || (filter === 'critical' && h.critical > 0) || (filter === 'ok' && h.critical === 0)
    return matchSearch && matchFilter
  })

  return (
    <div className="p-8">
      <div className="rounded-2xl p-6" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold" style={{color:'#f1f5f9'}}>Upload History</h3>
          <div className="flex gap-2">
            <input value={search} onChange={e => setSearch(e.target.value)} type="text" placeholder="Search..."
              className="rounded-xl px-3 py-2 text-sm focus:outline-none"
              style={{background:'var(--navy-700)',border:'1px solid var(--navy-500)',color:'#e2e8f0'}}/>
            <select value={filter} onChange={e => setFilter(e.target.value)}
              className="rounded-xl px-3 py-2 text-sm focus:outline-none"
              style={{background:'var(--navy-700)',border:'1px solid var(--navy-500)',color:'#94a3b8'}}>
              <option value="all">All Status</option>
              <option value="critical">Critical</option>
              <option value="ok">All OK</option>
            </select>
          </div>
        </div>

        {filtered.length === 0
          ? <div className="flex flex-col items-center py-12 text-center">
              <i className="fas fa-folder-open text-4xl mb-3" style={{color:'#1e3a5f'}}></i>
              <div className="text-sm" style={{color:'#475569'}}>No audit history yet</div>
              <button onClick={() => navigate('/quickaudit')} className="mt-4 text-xs px-4 py-2 rounded-xl font-semibold btn-gold">Run First Audit</button>
            </div>
          : <div className="space-y-3">
              {filtered.map((h, i) => {
                const dt = h.audited_at ? new Date(h.audited_at).toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}) : ''
                return (
                  <div key={i} onClick={() => navigate('/quickaudit')} className="flex items-center gap-4 p-4 rounded-xl cursor-pointer transition" style={{background:'var(--navy-700)',border:'1px solid var(--navy-600)'}}>
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{background:'rgba(201,168,76,0.15)'}}>
                      <i className="fas fa-file-excel" style={{color:'var(--gold-400)'}}></i>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate" style={{color:'#f1f5f9'}}>{h.filename || 'Trial Balance'}</div>
                      <div className="text-xs mt-0.5" style={{color:'#475569'}}>{dt} {h.period ? '· ' + h.period : ''}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold" style={{color: h.score>=75?'#34d399':h.score>=50?'#f59e0b':'#f87171'}}>{h.score}%</div>
                      <div className="text-xs" style={{color:'#64748b'}}>Score</div>
                    </div>
                    {h.critical > 0 ? <span className="tag-critical">{h.critical} Critical</span> : <span className="tag-ok">Clear</span>}
                    <i className="fas fa-chevron-right text-xs" style={{color:'#334155'}}></i>
                  </div>
                )
              })}
            </div>
        }
      </div>
    </div>
  )
}
