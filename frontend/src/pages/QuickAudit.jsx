import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'

export default function QuickAudit() {
  const [filesStatus, setFilesStatus] = useState({})
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const cid = localStorage.getItem('company_id') || 1
  const headers = { 'X-Company-ID': cid }

  useEffect(() => { loadFilesStatus() }, [])

  const loadFilesStatus = () => {
    axios.get(`${API_URL}/api/files/status`, { headers }).then(r => setFilesStatus(r.data)).catch(() => {})
  }

  const uploadFile = async (key, file) => {
    if (!file) return
    const form = new FormData()
    form.append(key, file)
    await axios.post(`${API_URL}/api/upload/files`, form, { headers })
    loadFilesStatus()
  }

  const runAudit = async () => {
    setLoading(true)
    try {
      const r = await axios.post(`${API_URL}/api/audit`, {}, { headers })
      setResults(r.data)
    } catch { alert('Error running audit') }
    setLoading(false)
  }

  const fileFields = [
    { key: 'trial_balance', label: 'Trial Balance', icon: 'fa-table', color: '#818cf8', statusKey: 'tb' },
    { key: 'daybook', label: 'Daybook', icon: 'fa-book', color: '#34d399', statusKey: 'db' },
  ]

  const score = results?.score
  const scoreColor = score >= 75 ? '#34d399' : score >= 50 ? '#f59e0b' : '#f87171'

  return (
    <div className="p-6">
      {/* Upload section */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {fileFields.map(f => (
          <div key={f.key} className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{background:`${f.color}22`}}>
                <i className={`fas ${f.icon}`} style={{color:f.color}}></i>
              </div>
              <div>
                <div className="text-sm font-semibold" style={{color:'#f1f5f9'}}>{f.label}</div>
                <div className="text-xs" style={{color:'#64748b'}}>Upload Excel from Tally</div>
              </div>
              {filesStatus[f.statusKey+'_exists'] && <span className="ml-auto tag-ok">Loaded</span>}
            </div>
            <label className="upload-zone rounded-xl p-4 text-center cursor-pointer block" htmlFor={f.key}>
              <i className={`fas fa-cloud-upload-alt text-2xl mb-2 block`} style={{color:f.color}}></i>
              <p className="text-xs mb-2" style={{color:'#94a3b8'}}>{filesStatus[f.statusKey] ? filesStatus[f.statusKey].filename : 'Drop file here'}</p>
              <input type="file" id={f.key} accept=".xlsx,.xls,.csv" className="hidden" onChange={e => uploadFile(f.key, e.target.files[0])}/>
              <span className="px-4 py-1.5 rounded-lg text-xs font-medium" style={{background:f.color,color:'#070E1A'}}>Choose File</span>
            </label>
          </div>
        ))}
      </div>

      {filesStatus.tb_exists && !loading && (
        <button onClick={runAudit} className="w-full py-4 rounded-2xl text-base font-bold flex items-center justify-center gap-3 mb-6 btn-gold">
          <i className="fas fa-magnifying-glass-dollar"></i> Run Quick Audit
        </button>
      )}

      {loading && (
        <div className="rounded-2xl p-8 text-center mb-6" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <i className="fas fa-cog text-3xl mb-3 block" style={{color:'var(--gold-400)',animation:'spin 1.5s linear infinite'}}></i>
          <div className="font-semibold mb-1" style={{color:'#f1f5f9'}}>Analyzing your books...</div>
          <div className="text-sm" style={{color:'#64748b'}}>This takes 30–60 seconds</div>
        </div>
      )}

      {results && (
        <div>
          {/* Score banner */}
          <div className="rounded-2xl p-6 mb-6 flex items-center gap-6" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
            <div className="text-center">
              <div className="text-5xl font-black" style={{color:scoreColor}}>{score}%</div>
              <div className="text-xs mt-1" style={{color:'#64748b'}}>Health Score</div>
            </div>
            <div className="flex-1">
              <div className="text-lg font-bold mb-1" style={{color:'#f1f5f9'}}>{score>=75?'Books look clean!':score>=50?'Some issues found':'Needs attention'}</div>
              <div className="text-sm" style={{color:'#94a3b8'}}>{results.summary?.critical||0} Critical · {results.summary?.warnings||0} Warnings · {results.summary?.questions||0} Questions</div>
              <div className="progress-bar mt-3"><div className="progress-fill" style={{width:score+'%'}}></div></div>
            </div>
          </div>

          {/* Issues */}
          {(results.cash_violations||[]).length > 0 && (
            <div className="rounded-2xl p-5 mb-4" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
              <div className="text-sm font-bold mb-3" style={{color:'#f87171'}}>⚠️ Cash Violations ({results.cash_violations.length})</div>
              {results.cash_violations.slice(0,10).map((v, i) => (
                <div key={i} className="entry-card p-3 mb-2 flex items-center gap-3">
                  <span className="tag-critical">Critical</span>
                  <div className="flex-1 text-xs" style={{color:'#e2e8f0'}}>{v.ledger} — ₹{Number(v.amount||0).toLocaleString('en-IN')}</div>
                  <div className="text-xs" style={{color:'#64748b'}}>{v.date}</div>
                </div>
              ))}
            </div>
          )}

          {(results.ledger_classification||[]).filter(f=>f.severity==='Critical').length > 0 && (
            <div className="rounded-2xl p-5 mb-4" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
              <div className="text-sm font-bold mb-3" style={{color:'#f87171'}}>Ledger Issues</div>
              {results.ledger_classification.filter(f=>f.severity==='Critical').slice(0,10).map((f, i) => (
                <div key={i} className="entry-card p-3 mb-2 flex items-center gap-3">
                  <span className="tag-critical">Critical</span>
                  <div className="flex-1 text-xs" style={{color:'#e2e8f0'}}>{f.ledger}</div>
                  <div className="text-xs" style={{color:'#94a3b8'}}>{f.issue}</div>
                </div>
              ))}
            </div>
          )}

          {(results.ledger_classification||[]).filter(f=>f.severity==='Review').length > 0 && (
            <div className="rounded-2xl p-5 mb-4" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
              <div className="text-sm font-bold mb-3" style={{color:'#fbbf24'}}>Ledger Warnings</div>
              {results.ledger_classification.filter(f=>f.severity==='Review').slice(0,10).map((f, i) => (
                <div key={i} className="entry-card p-3 mb-2 flex items-center gap-3">
                  <span className="tag-review">Review</span>
                  <div className="flex-1 text-xs" style={{color:'#e2e8f0'}}>{f.ledger}</div>
                  <div className="text-xs" style={{color:'#94a3b8'}}>{f.issue}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
