import { useState } from 'react'
import axios from 'axios'

const API_URL = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'

export default function FullAudit() {
  const [files, setFiles] = useState({})
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const cid = localStorage.getItem('company_id') || 1
  const headers = { 'X-Company-ID': cid }

  const uploadFile = async (key, file) => {
    if (!file) return
    const form = new FormData()
    form.append(key, file)
    await axios.post(`${API_URL}/api/upload/files`, form, { headers })
    setFiles(prev => ({ ...prev, [key]: file.name }))
  }

  const runAudit = async () => {
    setLoading(true)
    try {
      const r = await axios.post(`${API_URL}/api/complete-audit`, {}, { headers })
      setResults(r.data)
    } catch { alert('Error running audit') }
    setLoading(false)
  }

  const fileFields = [
    { key: 'trial_balance', label: 'Trial Balance', required: true, color: '#818cf8' },
    { key: 'daybook', label: 'Daybook', required: true, color: '#34d399' },
    { key: 'balance_sheet', label: 'Balance Sheet', required: false, color: '#60a5fa' },
    { key: 'profit_loss', label: 'Profit & Loss', required: false, color: '#f59e0b' },
    { key: 'bank_statement', label: 'Bank Statement', required: false, color: '#f87171' },
    { key: 'bank_tally', label: 'Bank Ledger (Tally)', required: false, color: '#a78bfa' },
  ]

  const score = results?.score
  const scoreColor = score >= 75 ? '#34d399' : score >= 50 ? '#f59e0b' : '#f87171'

  return (
    <div className="p-6">
      <div className="grid grid-cols-3 gap-4 mb-6">
        {fileFields.map(f => (
          <div key={f.key} className="rounded-2xl p-4" style={{background:'var(--navy-800)',border:`1px solid ${files[f.key] ? f.color+'55' : 'var(--navy-600)'}`}}>
            <div className="flex items-center gap-2 mb-2">
              <div className="text-xs font-semibold" style={{color:'#f1f5f9'}}>{f.label}</div>
              {f.required && <span className="text-xs" style={{color:'#f87171'}}>*</span>}
              {files[f.key] && <span className="ml-auto tag-ok">✓</span>}
            </div>
            <label className="upload-zone rounded-xl p-3 text-center cursor-pointer block" htmlFor={f.key}>
              <i className="fas fa-cloud-upload-alt mb-1 block" style={{color:f.color}}></i>
              <p className="text-xs mb-1" style={{color:'#94a3b8'}}>{files[f.key] || 'Drop Excel here'}</p>
              <input type="file" id={f.key} accept=".xlsx,.xls,.csv" className="hidden" onChange={e => uploadFile(f.key, e.target.files[0])}/>
              <span className="px-3 py-1 rounded-lg text-xs font-medium" style={{background:f.color,color:'#070E1A'}}>Choose</span>
            </label>
          </div>
        ))}
      </div>

      {files.trial_balance && !loading && (
        <button onClick={runAudit} className="w-full py-4 rounded-2xl text-base font-bold flex items-center justify-center gap-3 mb-6 btn-gold">
          <i className="fas fa-clipboard-check"></i> Run Full Audit
        </button>
      )}

      {loading && (
        <div className="rounded-2xl p-8 text-center" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <i className="fas fa-cog text-3xl mb-3 block" style={{color:'var(--gold-400)',animation:'spin 1.5s linear infinite'}}></i>
          <div className="font-semibold mb-1" style={{color:'#f1f5f9'}}>Running full audit...</div>
          <div className="text-sm" style={{color:'#64748b'}}>Analyzing all 6 files. This may take 1–2 minutes.</div>
        </div>
      )}

      {results && (
        <div className="rounded-2xl p-6" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="flex items-center gap-6 mb-6">
            <div className="text-center">
              <div className="text-5xl font-black" style={{color:scoreColor}}>{score}%</div>
              <div className="text-xs mt-1" style={{color:'#64748b'}}>Health Score</div>
            </div>
            <div className="flex-1">
              <div className="text-lg font-bold mb-1" style={{color:'#f1f5f9'}}>Full Audit Complete</div>
              <div className="text-sm" style={{color:'#94a3b8'}}>{results.summary?.critical||0} Critical · {results.summary?.warnings||0} Warnings</div>
              <div className="progress-bar mt-3"><div className="progress-fill" style={{width:score+'%'}}></div></div>
            </div>
          </div>
          <pre className="text-xs overflow-auto" style={{color:'#94a3b8',maxHeight:'400px'}}>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
