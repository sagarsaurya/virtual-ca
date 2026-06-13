import { useState, useEffect } from 'react'
import { runBankRec } from '../api'
import axios from 'axios'

const API_URL = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'

export default function BankRec() {
  const [bankFile, setBankFile] = useState(null)
  const [tallyFile, setTallyFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [activeTab, setActiveTab] = useState('wrongdate')
  const cid = localStorage.getItem('company_id') || 1

  useEffect(() => {
    // Check if files already uploaded
    axios.get(`${API_URL}/api/bankrec/status`, { headers: { 'X-Company-ID': cid } })
      .then(r => { if (r.data.bstmt_exists) setBankFile({ name: r.data.bstmt_filename }) })
      .catch(() => {})
  }, [])

  const handleBankUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setBankFile(file)
    const form = new FormData()
    form.append('bank_statement', file)
    await axios.post(`${API_URL}/api/upload/files`, form, { headers: { 'X-Company-ID': cid } })
  }

  const handleTallyUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setTallyFile(file)
    const form = new FormData()
    form.append('bank_tally', file)
    await axios.post(`${API_URL}/api/upload/files`, form, { headers: { 'X-Company-ID': cid } })
  }

  const doRunBankRec = async () => {
    setLoading(true)
    try {
      const r = await axios.post(`${API_URL}/api/bankrec`, {}, { headers: { 'X-Company-ID': cid } })
      setResults(r.data)
      setActiveTab('wrongdate')
    } catch (e) { alert('Error running reconciliation') }
    setLoading(false)
  }

  const tabs = [
    { id: 'wrongdate', label: '📅 Wrong Date', data: results?.wrong_date || [] },
    { id: 'unmatched', label: '🔴 Missing in Tally', data: results?.bank_only || [] },
    { id: 'tally', label: '🟡 Extra in Tally', data: results?.tally_only || [] },
    { id: 'duplicate', label: '🟠 Duplicates', data: results?.duplicates || [] },
    { id: 'matched', label: '✅ Matched', data: results?.matched || [] },
  ]

  return (
    <div className="p-8">
      {/* Upload strip */}
      {!results && (
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{background:'rgba(96,165,250,0.15)'}}><i className="fas fa-university" style={{color:'#60a5fa'}}></i></div>
              <div><div className="text-sm font-semibold" style={{color:'#f1f5f9'}}>Bank Statement</div><div className="text-xs" style={{color:'#64748b'}}>Upload PDF, CSV or Excel from your bank</div></div>
            </div>
            <label className="upload-zone rounded-xl p-5 text-center cursor-pointer block" htmlFor="bankInput">
              <i className="fas fa-cloud-upload-alt text-2xl mb-2 block" style={{color:'#60a5fa'}}></i>
              <p className="text-xs mb-1" style={{color:'#94a3b8'}}>{bankFile ? bankFile.name : 'Drop bank statement here'}</p>
              <input type="file" id="bankInput" accept=".pdf,.xlsx,.xls,.csv" className="hidden" onChange={handleBankUpload}/>
              <span className="px-4 py-1.5 rounded-lg text-xs font-medium" style={{background:'#3b82f6',color:'white'}}>Choose File</span>
              <p className="text-xs mt-2" style={{color:'#64748b'}}>Supports: PDF, .xlsx, .csv · HDFC, ICICI, SBI, Axis, Kotak</p>
            </label>
            {bankFile && <div className="mt-3 flex items-center gap-2 p-2 rounded-lg" style={{background:'rgba(52,211,153,0.08)'}}>
              <i className="fas fa-check-circle" style={{color:'#34d399'}}></i>
              <span className="text-xs" style={{color:'#34d399'}}>{bankFile.name}</span>
            </div>}
          </div>
          <div className="rounded-2xl p-5" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{background:'rgba(167,139,250,0.15)'}}><i className="fas fa-book" style={{color:'#a78bfa'}}></i></div>
              <div><div className="text-sm font-semibold" style={{color:'#f1f5f9'}}>Tally Bank Ledger</div><div className="text-xs" style={{color:'#64748b'}}>Export bank ledger from Tally as Excel</div></div>
            </div>
            <label className="upload-zone rounded-xl p-5 text-center cursor-pointer block" htmlFor="tallyInput">
              <i className="fas fa-cloud-upload-alt text-2xl mb-2 block" style={{color:'#a78bfa'}}></i>
              <p className="text-xs mb-1" style={{color:'#94a3b8'}}>{tallyFile ? tallyFile.name : 'Drop Tally bank ledger here'}</p>
              <input type="file" id="tallyInput" accept=".xlsx,.xls,.csv" className="hidden" onChange={handleTallyUpload}/>
              <span className="px-4 py-1.5 rounded-lg text-xs font-medium" style={{background:'#7c3aed',color:'white'}}>Choose File</span>
              <p className="text-xs mt-2" style={{color:'#64748b'}}>Tally → Account Books → Bank Ledger → Export Excel</p>
            </label>
            {tallyFile && <div className="mt-3 flex items-center gap-2 p-2 rounded-lg" style={{background:'rgba(52,211,153,0.08)'}}>
              <i className="fas fa-check-circle" style={{color:'#34d399'}}></i>
              <span className="text-xs" style={{color:'#34d399'}}>{tallyFile.name}</span>
            </div>}
          </div>
        </div>
      )}

      {bankFile && tallyFile && !results && !loading && (
        <button onClick={doRunBankRec} className="w-full py-4 rounded-2xl text-base font-bold transition flex items-center justify-center gap-3 mb-6" style={{background:'#3b82f6',color:'white'}}>
          <i className="fas fa-balance-scale"></i> Run Reconciliation
        </button>
      )}

      {loading && (
        <div className="rounded-2xl p-8 text-center mb-6" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <i className="fas fa-cog text-3xl mb-3 block" style={{color:'#60a5fa',animation:'spin 1.5s linear infinite'}}></i>
          <div className="font-semibold mb-1" style={{color:'#f1f5f9'}}>Reconciling transactions...</div>
          <div className="text-sm" style={{color:'#64748b'}}>Matching bank statement vs Tally entries</div>
        </div>
      )}

      {results && (
        <>
          <div className="flex justify-between items-center mb-4">
            <button onClick={() => { setResults(null); setBankFile(null); setTallyFile(null) }} className="text-xs px-4 py-2 rounded-xl font-semibold flex items-center gap-2" style={{background:'var(--navy-700)',color:'#94a3b8',border:'1px solid var(--navy-500)'}}>
              <i className="fas fa-arrow-left"></i> Change Files
            </button>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-6">
            {[
              {label:'Matched',color:'#34d399',border:'border-green-400',val:results.summary?.matched||0},
              {label:'Wrong Date',color:'#a78bfa',border:'border-purple-500',val:results.summary?.wrong_date||0},
              {label:'Missing in Tally',color:'#f87171',border:'border-red-400',val:results.summary?.bank_only||0},
              {label:'Extra in Tally',color:'#fbbf24',border:'border-yellow-400',val:results.summary?.tally_only||0},
              {label:'Duplicates',color:'#fb923c',border:'border-orange-400',val:results.summary?.duplicates||0},
            ].map((s, i) => (
              <div key={i} className="stat-card card-shadow text-center" style={{borderTop:`4px solid ${s.color}`}}>
                <div className="text-3xl font-bold" style={{color:s.color}}>{s.val}</div>
                <div className="text-sm mt-1" style={{color:'#94a3b8'}}>{s.label}</div>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-2 mb-5">
            {tabs.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} className="px-4 py-2 rounded-xl text-sm font-medium transition" style={{background: activeTab===t.id ? '#3b82f6' : 'var(--navy-700)', color: activeTab===t.id ? 'white' : '#94a3b8', border:`1px solid ${activeTab===t.id ? '#3b82f6' : 'var(--navy-500)'}` }}>
                {t.label} ({t.data.length})
              </button>
            ))}
          </div>

          <div className="space-y-3">
            {(tabs.find(t => t.id === activeTab)?.data || []).length === 0
              ? <div className="text-sm text-center py-8" style={{color:'#64748b'}}>No items in this category</div>
              : tabs.find(t => t.id === activeTab)?.data.map((row, i) => (
                <div key={i} className="entry-card p-4 flex items-center gap-4">
                  <div className="text-xs" style={{color:'#94a3b8',minWidth:'80px'}}>{row.date}</div>
                  <div className="flex-1 text-xs" style={{color:'#e2e8f0'}}>{row.narration || row.description || '—'}</div>
                  <div className="text-xs font-bold" style={{color:'#34d399'}}>₹{Number(row.amount||0).toLocaleString('en-IN')}</div>
                  {row.dr_cr && <span className="text-xs px-2 py-0.5 rounded-full" style={{background:'var(--navy-600)',color:'#94a3b8'}}>{row.dr_cr}</span>}
                </div>
              ))
            }
          </div>
        </>
      )}

      {!bankFile && !results && (
        <div className="rounded-2xl p-12 text-center" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{background:'rgba(96,165,250,0.15)'}}>
            <i className="fas fa-exchange-alt text-3xl" style={{color:'#60a5fa'}}></i>
          </div>
          <div className="font-semibold mb-1" style={{color:'#f1f5f9'}}>Upload both files to start reconciliation</div>
          <div className="text-sm" style={{color:'#64748b'}}>Upload your bank statement and Tally bank ledger above</div>
        </div>
      )}
    </div>
  )
}
