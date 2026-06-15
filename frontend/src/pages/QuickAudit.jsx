import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const API_URL = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'
const fmt = n => '₹' + Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })
const secTag = (text, color = '#93c5fd', bg = 'rgba(96,165,250,0.15)') =>
  <span style={{ fontSize: 10, background: bg, color, padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>{text}</span>

function EmptyOk({ msg, detail, law }) {
  return (
    <div style={{ margin: 12, padding: '12px 16px', background: 'rgba(52,211,153,0.07)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 10 }}>
      <div style={{ color: '#34d399', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
        <i className="fas fa-check-circle"></i> {msg}
      </div>
      {detail && <div style={{ color: '#64748b', fontSize: 11, marginTop: 4 }}>{detail}</div>}
      {law && <div style={{ color: '#34d399', opacity: 0.7, fontSize: 11, marginTop: 4 }}>📋 {law}</div>}
    </div>
  )
}

function AuditTable({ headers, rows }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            {headers.map(h => <th key={h} style={{ textAlign: 'left', padding: '8px 16px', color: '#64748b', fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>)}
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  )
}

function Section({ icon, title, subtitle, badgeText, badgeColor = '#f87171', badgeBg = 'rgba(239,68,68,0.2)', extra, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div style={{ background: 'var(--navy-800)', border: '1px solid var(--navy-600)', borderRadius: 12, marginBottom: 10, overflow: 'hidden' }}>
      <div onClick={() => setOpen(o => !o)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px', cursor: 'pointer' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, background: 'rgba(255,255,255,0.05)' }}>{icon}</div>
          <div>
            <div style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 600 }}>{title}</div>
            <div style={{ color: '#64748b', fontSize: 11 }}>{subtitle}</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {extra && <span style={{ color: '#64748b', fontSize: 11 }}>{extra}</span>}
          {badgeText && <span style={{ background: badgeBg, color: badgeColor, fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 99 }}>{badgeText}</span>}
          <i className="fas fa-chevron-down" style={{ color: '#64748b', fontSize: 11, transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}></i>
        </div>
      </div>
      {open && <div style={{ borderTop: '1px solid var(--navy-600)' }}>{children}</div>}
    </div>
  )
}

export default function QuickAudit() {
  const [filesStatus, setFilesStatus] = useState({})
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState(null)
  const [confirmedBank, setConfirmedBank] = useState(new Set())
  const [uploading, setUploading] = useState({})
  const getHeaders = () => ({ 'X-Company-ID': localStorage.getItem('company_id') || 1 })

  const loadFilesStatus = useCallback(() => {
    const cid = localStorage.getItem('company_id') || 1
    axios.get(`${API_URL}/api/files/status`, { headers: { 'X-Company-ID': cid } }).then(r => setFilesStatus(r.data)).catch(() => {})
  }, [])

  useEffect(() => { loadFilesStatus() }, [loadFilesStatus])

  const uploadFile = async (key, file) => {
    if (!file) return
    setUploading(u => ({ ...u, [key]: true }))
    try {
      const form = new FormData()
      form.append(key, file)
      const r = await axios.post(`${API_URL}/api/upload/files`, form, { headers: getHeaders() })
      // Update UI directly from upload response — don't wait for Supabase refetch
      const uploadedMeta = r.data.status || {}
      setFilesStatus(prev => ({
        ...prev,
        ...uploadedMeta,
        tb_exists: !!uploadedMeta.tb,
        db_exists: !!uploadedMeta.db,
      }))
    } catch (e) {
      alert('Upload failed: ' + (e.response?.data?.error || e.message))
    } finally {
      setUploading(u => ({ ...u, [key]: false }))
    }
  }

  const runAudit = async () => {
    setLoading(true)
    setProgress(0)
    setResults(null)
    const iv = setInterval(() => setProgress(p => p < 60 ? p + 1 : p), 40)
    try {
      const r = await axios.post(`${API_URL}/api/audit`, {}, { headers: getHeaders() })
      clearInterval(iv)
      let p = 60
      const iv2 = setInterval(() => {
        p += 3
        setProgress(p)
        if (p >= 100) { clearInterval(iv2); setResults(r.data); setLoading(false) }
      }, 25)
    } catch (e) {
      clearInterval(iv)
      alert('Audit failed: ' + (e.response?.data?.error || e.message))
      setLoading(false)
    }
  }

  const confirmPartyBank = async (key, items) => {
    setConfirmedBank(prev => new Set([...prev, key]))
    for (const v of items) {
      try {
        await axios.post(`${API_URL}/api/audit/mark-personal`, { date: v.date, party: v.party, amount: v.amount, reason: 'Bank payment — confirmed' }, { headers: getHeaders() })
      } catch (e) {}
    }
  }

  const confirmAllBank = async () => {
    const groups = groupByParty(results?.cash_violations || [])
    for (const [key, g] of Object.entries(groups)) {
      await confirmPartyBank(key, g.items)
    }
  }

  const markPersonal = async (v, i) => {
    const reason = window.prompt(`Mark "${v.party}" as personal?\nEnter reason:`, 'Personal expense')
    if (reason === null) return
    try {
      await axios.post(`${API_URL}/api/audit/mark-personal`, { date: v.date, party: v.party, amount: v.amount, reason }, { headers: getHeaders() })
      alert('Marked as personal.')
    } catch (e) {}
  }

  const exportExcel = () => window.open(`${API_URL}/api/audit/export-excel`, '_blank')

  const fileFields = [
    { key: 'trial_balance', label: 'Trial Balance', icon: 'fa-table', color: '#818cf8', statusKey: 'tb' },
    { key: 'daybook', label: 'Daybook', icon: 'fa-book', color: '#34d399', statusKey: 'db' },
  ]

  const s = results?.summary || {}
  const score = s.score || 0
  const scoreColor = score >= 70 ? '#34d399' : score >= 40 ? '#f97316' : '#ef4444'
  const gaugeCirc = 276.5
  const gaugeOffset = gaugeCirc - (score / 100 * gaugeCirc)

  return (
    <div style={{ padding: 20 }}>

      {/* Upload */}
      {!results && !loading && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            {fileFields.map(f => (
              <div key={f.key} style={{ background: 'var(--navy-800)', border: '1px solid var(--navy-600)', borderRadius: 12, padding: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <div style={{ width: 34, height: 34, borderRadius: 10, background: f.color + '22', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <i className={`fas ${f.icon}`} style={{ color: f.color }}></i>
                  </div>
                  <div>
                    <div style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 600 }}>{f.label}</div>
                    <div style={{ color: '#64748b', fontSize: 11 }}>Upload Excel from Tally</div>
                  </div>
                  {filesStatus[f.statusKey + '_exists'] && <span style={{ marginLeft: 'auto', background: 'rgba(52,211,153,0.12)', color: '#34d399', border: '1px solid rgba(52,211,153,0.3)', fontSize: 11, padding: '2px 8px', borderRadius: 99 }}>Loaded</span>}
                </div>
                <label htmlFor={f.key} style={{ display: 'block', border: '2px dashed var(--navy-500)', background: 'var(--navy-800)', borderRadius: 10, padding: 14, textAlign: 'center', cursor: 'pointer' }}>
                  <i className="fas fa-cloud-upload-alt" style={{ color: f.color, fontSize: 22, display: 'block', marginBottom: 6 }}></i>
                  <p style={{ color: '#94a3b8', fontSize: 11, marginBottom: 8 }}>{filesStatus[f.statusKey]?.filename || 'Drop file here'}</p>
                  <input type="file" id={f.key} accept=".xlsx,.xls,.csv" style={{ display: 'none' }} onChange={e => uploadFile(f.key, e.target.files[0])} disabled={uploading[f.key]} />
                  <span style={{ background: uploading[f.key] ? '#64748b' : f.color, color: '#070E1A', fontSize: 12, fontWeight: 700, padding: '5px 14px', borderRadius: 8 }}>{uploading[f.key] ? 'Uploading…' : 'Choose File'}</span>
                </label>
              </div>
            ))}
          </div>
          {filesStatus.tb_exists && (
            <button onClick={runAudit} style={{ width: '100%', padding: '14px 0', background: 'var(--gold-500)', color: 'var(--navy-900)', borderRadius: 12, fontSize: 15, fontWeight: 700, border: 'none', cursor: 'pointer', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <i className="fas fa-magnifying-glass-dollar"></i> Run Quick Audit
            </button>
          )}
        </>
      )}

      {/* Progress */}
      {loading && (
        <div style={{ background: 'var(--navy-800)', border: '1px solid var(--navy-600)', borderRadius: 12, padding: 28, textAlign: 'center', marginBottom: 16 }}>
          <i className="fas fa-cog" style={{ color: 'var(--gold-400)', fontSize: 28, marginBottom: 12, display: 'block', animation: 'spin 1.5s linear infinite' }}></i>
          <div style={{ color: '#f1f5f9', fontWeight: 600, marginBottom: 4 }}>Analyzing your books... {progress}%</div>
          <div style={{ color: '#64748b', fontSize: 12, marginBottom: 14 }}>This takes 30–60 seconds</div>
          <div style={{ height: 6, background: 'var(--navy-700)', borderRadius: 99, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: progress + '%', background: 'var(--gold-500)', borderRadius: 99, transition: 'width 0.3s' }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 14 }}>
            {[['fa-table', 'Ledger Classification', 20], ['fa-ban', 'Cash Violations', 35], ['fa-receipt', 'TDS & Compliance', 50]].map(([icon, label, threshold]) => (
              <div key={label} style={{ fontSize: 11, color: progress >= threshold ? '#C9A84C' : '#4A6A8A', display: 'flex', alignItems: 'center', gap: 4 }}>
                <i className={`fas ${progress >= threshold ? 'fa-circle-notch fa-spin' : icon}`} style={{ fontSize: 11 }}></i> {label}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <>
          {/* Score Banner */}
          <div style={{ background: 'var(--navy-800)', border: '1px solid var(--navy-600)', borderRadius: 12, padding: 18, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flexShrink: 0 }}>
              <svg width="100" height="100" viewBox="0 0 108 108">
                <circle cx="54" cy="54" r="44" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="9" />
                <circle cx="54" cy="54" r="44" fill="none" stroke={scoreColor} strokeWidth="9"
                  strokeLinecap="round" strokeDasharray="276.5" strokeDashoffset={gaugeOffset}
                  transform="rotate(-90 54 54)" style={{ transition: 'stroke-dashoffset 1.2s ease' }} />
              </svg>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: '#f1f5f9', fontSize: 28, fontWeight: 900, lineHeight: 1 }}>{score}</div>
                <div style={{ color: '#64748b', fontSize: 11 }}>/100</div>
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ color: '#64748b', fontSize: 11, marginBottom: 2 }}>Compliance Score · {s.period || 'FY 2025–26'}</div>
              <div style={{ color: '#f1f5f9', fontWeight: 600, marginBottom: 2 }}>{s.company || ''}</div>
              <div style={{ color: '#64748b', fontSize: 12, marginBottom: 10 }}>{(s.critical || 0) + (s.warnings || 0)} issues found across all modules</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10, padding: '6px 12px', textAlign: 'center', minWidth: 52 }}>
                  <div style={{ color: '#f87171', fontWeight: 700, fontSize: 18 }}>{s.critical || 0}</div>
                  <div style={{ color: '#64748b', fontSize: 10 }}>Critical</div>
                </div>
                <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 10, padding: '6px 12px', textAlign: 'center', minWidth: 52 }}>
                  <div style={{ color: '#fbbf24', fontWeight: 700, fontSize: 18 }}>{s.warnings || 0}</div>
                  <div style={{ color: '#64748b', fontSize: 10 }}>Warnings</div>
                </div>
                <div style={{ background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.2)', borderRadius: 10, padding: '6px 12px', textAlign: 'center', minWidth: 52 }}>
                  <div style={{ color: '#93c5fd', fontWeight: 700, fontSize: 18 }}>{s.questions || 0}</div>
                  <div style={{ color: '#64748b', fontSize: 10 }}>Questions</div>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flexShrink: 0 }}>
              <button onClick={() => { setResults(null); setProgress(0) }} style={{ fontSize: 12, padding: '7px 14px', background: 'var(--navy-700)', color: '#94a3b8', border: '1px solid var(--navy-600)', borderRadius: 10, cursor: 'pointer' }}>
                <i className="fas fa-sync-alt" style={{ marginRight: 6 }}></i>Change Files
              </button>
              <button onClick={exportExcel} style={{ fontSize: 12, padding: '7px 14px', background: 'rgba(16,185,129,0.15)', color: '#34d399', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 10, cursor: 'pointer' }}>
                <i className="fas fa-file-excel" style={{ marginRight: 6 }}></i>Download Report
              </button>
            </div>
          </div>

          {/* 1. Cash Violations */}
          <CashSection violations={results.cash_violations || []} bankCleared={results.cash_violations_bank_cleared || []} bankStatus={results.bank_crosscheck_status} confirmedBank={confirmedBank} onConfirmParty={confirmPartyBank} onConfirmAll={confirmAllBank} headers={getHeaders()} />

          {/* 2. Ledger Classification */}
          <Section icon="📋" title="Ledger Classification" subtitle="Wrong groups · misclassified accounts"
            badgeText={(results.ledger_classification || []).length ? results.ledger_classification.length + ' Issues' : undefined}
            badgeColor="#fbbf24" badgeBg="rgba(245,158,11,0.2)">
            <LedgerSection findings={results.ledger_classification || []} />
          </Section>

          {/* 3. TDS Compliance */}
          <Section icon="🧾" title="TDS Compliance" subtitle="Sec 194C · 194J · 194I · 194H"
            badgeText={(results.tds_compliance || []).filter(t => t.type === 'payment_check').length ? (results.tds_compliance.filter(t => t.type === 'payment_check').length + ' parties') : undefined}
            badgeColor="#93c5fd" badgeBg="rgba(96,165,250,0.2)"
            extra={results.tds_compliance?.filter(t => t.type === 'payment_check').reduce((s, t) => s + (t.tds_expected || 0), 0) > 0 ? fmt(results.tds_compliance.filter(t => t.type === 'payment_check').reduce((s, t) => s + (t.tds_expected || 0), 0)) + ' exposure' : undefined}>
            <TDSSection items={(results.tds_compliance || []).filter(t => t.type === 'payment_check')} />
          </Section>

          {/* 4. Outstanding Balances */}
          <Section icon="⚖️" title="Outstanding Balances" subtitle="Abnormal balances · suspense accounts"
            badgeText={(results.outstanding || []).length ? results.outstanding.length + ' Items' : undefined}
            badgeColor="#34d399" badgeBg="rgba(16,185,129,0.2)">
            <OutstandingSection items={results.outstanding || []} />
          </Section>

          {/* 5. Large Expenses */}
          <Section icon="💰" title="Large Expenses" subtitle="Payments above ₹1L · bill & TDS verification"
            badgeText={(results.large_expenses || []).length ? results.large_expenses.length + ' Entries' : undefined}
            badgeColor="#fbbf24" badgeBg="rgba(245,158,11,0.2)">
            <LargeExpensesSection expenses={results.large_expenses || []} itr={results.itr || []} onMarkPersonal={markPersonal} />
          </Section>

          {/* 6. Loans */}
          <Section icon="🏦" title="Loans & Director Advances" subtitle="Sec 269SS/269T · director loans · long-pending advances"
            badgeText={(results.loans || []).length ? results.loans.length + ' Loans' : undefined}
            badgeColor="#f87171" badgeBg="rgba(239,68,68,0.2)">
            <LoansSection loans={results.loans || []} />
          </Section>

          {/* 7. Bank Accounts */}
          <Section icon="🏧" title="Bank Accounts in Books" subtitle="All bank ledgers detected · reconcile each with statement"
            badgeText={(results.bank_accounts || []).length ? results.bank_accounts.length + ' accounts' : undefined}
            badgeColor="#34d399" badgeBg="rgba(16,185,129,0.2)"
            extra={results.bank_accounts?.length ? fmt(results.bank_accounts.reduce((s, b) => s + Math.abs(b.balance || 0), 0)) + ' total' : undefined}>
            <BankSection accounts={results.bank_accounts || []} />
          </Section>

          {/* 8. Salary / PF / PT */}
          <Section icon="👥" title="Salary / PF / PT Compliance" subtitle="EPF Act · Professional Tax (WB) · salary deductions"
            badgeText={(results.salary_compliance || []).length ? results.salary_compliance.length + ' issues' : undefined}
            badgeColor="#93c5fd" badgeBg="rgba(96,165,250,0.2)">
            <SalarySection items={results.salary_compliance || []} />
          </Section>

          {/* Footer */}
          <div style={{ background: '#0D1B2E', border: '1px solid var(--navy-600)', borderRadius: 12, padding: 20, textAlign: 'center', marginTop: 4 }}>
            <div style={{ color: '#f1f5f9', fontWeight: 600, marginBottom: 4 }}>Audit Complete</div>
            <div style={{ color: '#64748b', fontSize: 12, marginBottom: 16 }}>Download the full report with all findings, corrections and journal entries</div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 10 }}>
              <button onClick={exportExcel} style={{ background: '#16a34a', color: 'white', border: 'none', borderRadius: 10, padding: '10px 20px', fontWeight: 700, fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <i className="fas fa-file-excel"></i> Download Excel Report
              </button>
              <button onClick={() => window.print()} style={{ background: '#374151', color: 'white', border: 'none', borderRadius: 10, padding: '10px 20px', fontWeight: 700, fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <i className="fas fa-file-pdf"></i> Download PDF
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function groupByParty(violations) {
  const byParty = {}
  violations.forEach(v => {
    const k = v.party + '__' + (v.type || '')
    if (!byParty[k]) byParty[k] = { party: v.party, section: v.section, type: v.type, total: 0, items: [] }
    byParty[k].total += v.amount
    byParty[k].items.push(v)
  })
  return byParty
}

function CashSection({ violations, bankCleared, bankStatus, confirmedBank, onConfirmParty, onConfirmAll, headers }) {
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState({})
  const total = violations.reduce((s, v) => s + v.amount, 0)
  const groups = groupByParty(violations)
  const filtered = Object.entries(groups).filter(([k, g]) => g.party.toLowerCase().includes(search.toLowerCase()))
  const initials = name => name.split(' ').map(w => w[0] || '').join('').slice(0, 2).toUpperCase()
  const avatarColors = ['#1d4ed8', '#dc2626', '#059669', '#b45309', '#0f766e']

  const badgeText = violations.length ? violations.length + ' items' : (bankCleared.length ? '0 items' : undefined)
  const badgeColor = violations.length ? '#f87171' : '#34d399'
  const badgeBg = violations.length ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)'

  return (
    <Section icon="💸" title="Cash Violations" subtitle="Sec 40A(3) >₹10k · Sec 269ST >₹2L · grouped by party"
      badgeText={badgeText} badgeColor={badgeColor} badgeBg={badgeBg} defaultOpen={true}
      extra={violations.length ? fmt(total) + ' total' + (bankCleared.length ? ` · ${bankCleared.length} auto-cleared by bank ✓` : '') : undefined}>

      {!violations.length && !bankCleared.length && (
        <EmptyOk msg="No cash violations found" detail="All payments scanned — none exceed ₹10,000 in cash (Sec 40A(3)) or ₹2,00,000 cash receipt (Sec 269ST)." law="Sec 40A(3) & Sec 269ST — Income Tax Act 1961" />
      )}

      {!violations.length && bankCleared.length > 0 && (
        <div style={{ margin: 12, padding: 14, background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.25)', borderRadius: 10 }}>
          <div style={{ color: '#34d399', fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
            <i className="fas fa-check-circle" style={{ marginRight: 6 }}></i>All {bankCleared.length} entries verified via bank statement — no cash violations
          </div>
          {bankCleared.map((v, i) => (
            <div key={i} style={{ fontSize: 11, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '5px 0', display: 'flex', justifyContent: 'space-between' }}>
              <span>{v.party} · {v.date}</span><span style={{ color: '#34d399' }}>{fmt(v.amount)} ✓ Bank</span>
            </div>
          ))}
        </div>
      )}

      {violations.length > 0 && (
        <>
          {bankStatus === 'no_bank_statement' && (
            <div style={{ margin: '10px 12px 0', padding: '10px 14px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#fbbf24' }}>
              <i className="fas fa-triangle-exclamation"></i>
              <span style={{ flex: 1 }}>Bank statement not uploaded — cross-check skipped. Upload bank statement to auto-clear verified payments.</span>
            </div>
          )}
          <div style={{ margin: '10px 12px', padding: '10px 14px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 10, fontSize: 12, color: '#fbbf24' }}>
            💡 If all payments were via Bank/NEFT/UPI — click <strong>"Confirm All as Bank"</strong> to clear all {violations.length} in one go.
          </div>
          <div style={{ display: 'flex', gap: 8, padding: '0 12px 10px', flexWrap: 'wrap' }}>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="🔍 Search party..."
              style={{ flex: 1, minWidth: 140, fontSize: 12, padding: '6px 12px', background: 'var(--navy-700)', border: '1px solid var(--navy-600)', color: '#e2e8f0', borderRadius: 8, outline: 'none' }} />
            <button onClick={onConfirmAll} style={{ fontSize: 12, padding: '6px 12px', background: 'rgba(16,185,129,0.2)', color: '#34d399', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}>
              ✓ Confirm All as Bank
            </button>
          </div>
          {filtered.map(([key, g], ci) => {
            const confirmed = confirmedBank.has(key)
            const isExp = expanded[key]
            return (
              <div key={key} style={{ opacity: confirmed ? 0.4 : 1, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <div onClick={() => setExpanded(e => ({ ...e, [key]: !e[key] }))}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: avatarColors[ci % avatarColors.length], display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: 'white', flexShrink: 0 }}>
                      {initials(g.party)}
                    </div>
                    <div>
                      <div style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13, textDecoration: confirmed ? 'line-through' : 'none' }}>{g.party}</div>
                      <div style={{ color: '#94a3b8', fontSize: 11 }}>{g.items.length} transaction{g.items.length > 1 ? 's' : ''} · click to expand</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    {secTag('Sec ' + g.section, '#f87171', 'rgba(239,68,68,0.15)')}
                    <span style={{ color: '#f87171', fontWeight: 700, fontSize: 13 }}>{fmt(g.total)}</span>
                    {confirmed
                      ? <span style={{ color: '#34d399', fontSize: 12, fontWeight: 700 }}>✓ Confirmed Bank</span>
                      : <>
                        <button onClick={e => { e.stopPropagation(); onConfirmParty(key, g.items) }}
                          style={{ fontSize: 11, padding: '4px 10px', background: 'rgba(16,185,129,0.2)', color: '#34d399', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>✓ All Bank</button>
                        <button onClick={e => e.stopPropagation()}
                          style={{ fontSize: 11, padding: '4px 10px', background: 'rgba(239,68,68,0.15)', color: '#f87171', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>✗ Cash</button>
                      </>}
                    <i className="fas fa-chevron-right" style={{ color: '#64748b', fontSize: 11, transform: isExp ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}></i>
                  </div>
                </div>
                {isExp && (
                  <table style={{ width: '100%', fontSize: 12 }}>
                    <tbody>
                      {g.items.map((v, i) => (
                        <tr key={i} style={{ background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                          <td style={{ padding: '8px 16px 8px 52px', color: '#94a3b8' }}>{v.date || '—'}</td>
                          <td style={{ padding: '8px 16px', color: '#94a3b8' }}>Voucher {i + 1}</td>
                          <td style={{ padding: '8px 16px', color: '#fca5a5', fontWeight: 600 }}>{fmt(v.amount)}</td>
                          <td style={{ padding: '8px 16px' }}>
                            <button style={{ fontSize: 11, padding: '3px 8px', background: 'rgba(16,185,129,0.2)', color: '#34d399', border: 'none', borderRadius: 6, cursor: 'pointer', marginRight: 4 }}>Bank</button>
                            <button style={{ fontSize: 11, padding: '3px 8px', background: 'rgba(239,68,68,0.2)', color: '#f87171', border: 'none', borderRadius: 6, cursor: 'pointer' }}>Cash</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )
          })}
          <div style={{ padding: '10px 16px', color: '#64748b', fontSize: 11, borderTop: '1px solid rgba(255,255,255,0.04)' }}>
            {Object.keys(groups).length} parties · {violations.length} total transactions
          </div>
        </>
      )}
    </Section>
  )
}

function LedgerSection({ findings }) {
  if (!findings.length) return <EmptyOk msg="All ledger groups are correct" detail="Every ledger checked against ICAI Chart of Accounts standards." law="ICAI Accounting Standards + Tally CoA conventions" />
  return (
    <AuditTable
      headers={['Ledger', 'Current Group', 'Should Be', 'Balance', 'Severity', 'Fix']}
      rows={findings.map((f, i) => (
        <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <td style={{ padding: '10px 16px', color: '#e2e8f0', fontWeight: 600 }}>{f.ledger}<div style={{ color: '#64748b', fontSize: 10 }}>{f.rule || ''}</div></td>
          <td style={{ padding: '10px 16px', color: '#f87171' }}>{f.current_group || f.group || ''}</td>
          <td style={{ padding: '10px 16px', color: '#34d399' }}>{f.correct_group || ''}</td>
          <td style={{ padding: '10px 16px', color: '#94a3b8' }}>{fmt(f.balance || f.amount || 0)}</td>
          <td style={{ padding: '10px 16px' }}>{f.severity === 'Critical' ? secTag('Critical', '#f87171', 'rgba(239,68,68,0.15)') : secTag('Review', '#fbbf24', 'rgba(245,158,11,0.15)')}</td>
          <td style={{ padding: '10px 16px' }}><span style={{ fontSize: 11, padding: '3px 8px', background: 'rgba(245,158,11,0.15)', color: '#fbbf24', borderRadius: 6 }}>{(f.fix || '').split('→')[0] || 'Alter Ledger'}</span></td>
        </tr>
      ))}
    />
  )
}

function TDSSection({ items }) {
  if (!items.length) return <EmptyOk msg="No TDS compliance issues detected" detail="Payments within TDS threshold limits — or TDS has been correctly deducted." law="Sec 194C / 194J / 194I / 194H — Income Tax Act 1961" />
  return (
    <AuditTable
      headers={['Party / Ledger', 'Section', 'Total Paid', 'TDS Due', 'Interest Est.']}
      rows={items.map((t, i) => (
        <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <td style={{ padding: '10px 16px', color: '#e2e8f0', fontWeight: 600 }}>{t.party}</td>
          <td style={{ padding: '10px 16px' }}>{secTag('Sec ' + t.section, '#93c5fd', 'rgba(96,165,250,0.15)')}</td>
          <td style={{ padding: '10px 16px', color: '#e2e8f0' }}>{fmt(t.total_paid || 0)}</td>
          <td style={{ padding: '10px 16px' }}><span style={{ color: '#f87171', fontWeight: 700 }}>{fmt(t.tds_expected || 0)}</span> <span style={{ color: '#64748b', fontSize: 11 }}>@ {t.rate}%</span></td>
          <td style={{ padding: '10px 16px', color: t.interest_est > 0 ? '#fbbf24' : '#64748b' }}>{t.interest_est > 0 ? fmt(t.interest_est) : '—'}</td>
        </tr>
      ))}
    />
  )
}

function OutstandingSection({ items }) {
  if (!items.length) return <EmptyOk msg="No abnormal balances found" detail="Suspense accounts are nil. No credit balance debtors or debit balance creditors detected." law="SA 500 + SA 505 — ICAI" />
  return (
    <AuditTable
      headers={['Ledger', 'Issue', 'Balance', 'Severity']}
      rows={items.map((f, i) => (
        <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <td style={{ padding: '10px 16px', color: '#e2e8f0', fontWeight: 600 }}>{f.ledger}</td>
          <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 11 }}>{f.question || f.issue || ''}</td>
          <td style={{ padding: '10px 16px', color: '#f87171', fontWeight: 600 }}>{fmt(f.amount || f.balance || 0)}</td>
          <td style={{ padding: '10px 16px' }}>{f.severity === 'Critical' ? secTag('Critical', '#f87171', 'rgba(239,68,68,0.15)') : secTag('Warning', '#fbbf24', 'rgba(245,158,11,0.15)')}</td>
        </tr>
      ))}
    />
  )
}

function LargeExpensesSection({ expenses, itr, onMarkPersonal }) {
  const all = [...expenses, ...itr.filter(f => f.ledger && f.ledger !== 'Cash Payments (Sec 40A(3))').map(f => ({
    date: '—', party: f.ledger, amount: f.amount || 0, question: f.issue + ' — ' + (f.action || '')
  }))]
  if (!all.length) return <EmptyOk msg="No large unverified expenses" detail="No single payment above ₹1,00,000 found — or all large payments have been verified." law="Sec 37(1) Income Tax Act — CGST Act Sec 16(2) for ITC" />
  return (
    <AuditTable
      headers={['Date', 'Party', 'Amount', 'Note', 'Action']}
      rows={all.map((e, i) => (
        <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <td style={{ padding: '10px 16px', color: '#94a3b8' }}>{e.date || '—'}</td>
          <td style={{ padding: '10px 16px', color: '#e2e8f0', fontWeight: 600 }}>{e.party}</td>
          <td style={{ padding: '10px 16px', color: '#fbbf24', fontWeight: 700 }}>{fmt(e.amount)}</td>
          <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 11 }}>{e.question || e.voucher_type || ''}</td>
          <td style={{ padding: '10px 16px' }}>
            {e.date !== '—' && <button onClick={() => onMarkPersonal(e, i)} style={{ fontSize: 11, padding: '3px 8px', background: 'rgba(100,116,139,0.2)', color: '#94a3b8', border: 'none', borderRadius: 6, cursor: 'pointer' }}>👤 Personal</button>}
          </td>
        </tr>
      ))}
    />
  )
}

function LoansSection({ loans }) {
  if (!loans.length) return <EmptyOk msg="No loan accounts requiring documentation" detail="No loans or director advances found above ₹10,000 — or all loans are already documented." law="Sec 269SS / 269T — Income Tax Act | Companies Act 2013 Sec 185" />
  return (
    <AuditTable
      headers={['Ledger', 'Balance', 'Issue', 'Action']}
      rows={loans.map((f, i) => (
        <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <td style={{ padding: '10px 16px', color: '#e2e8f0', fontWeight: 600 }}>{f.ledger}</td>
          <td style={{ padding: '10px 16px', color: '#f87171', fontWeight: 700 }}>{fmt(f.balance || 0)}</td>
          <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 11 }}>{f.question || f.note || ''}</td>
          <td style={{ padding: '10px 16px' }}>{secTag('Document Required', '#fbbf24', 'rgba(245,158,11,0.15)')}</td>
        </tr>
      ))}
    />
  )
}

function BankSection({ accounts }) {
  if (!accounts.length) return <EmptyOk msg="No bank accounts detected" />
  return (
    <AuditTable
      headers={['Bank Ledger', 'Book Balance', 'Dr / Cr', 'Note']}
      rows={accounts.map((b, i) => {
        const bal = b.balance || 0
        const isNeg = bal < 0
        return (
          <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <td style={{ padding: '10px 16px', color: '#e2e8f0', fontWeight: 600 }}>{b.ledger}</td>
            <td style={{ padding: '10px 16px', color: isNeg ? '#f87171' : '#34d399', fontWeight: 700 }}>{fmt(Math.abs(bal))}</td>
            <td style={{ padding: '10px 16px' }}>{secTag(b.dr_cr || (bal >= 0 ? 'Dr (Asset)' : 'Cr (Liability)'), bal >= 0 ? '#34d399' : '#f87171', bal >= 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)')}</td>
            <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 11 }}>{isNeg ? '⚠️ Credit balance — possible overdraft or error' : 'Reconcile with bank statement'}</td>
          </tr>
        )
      })}
    />
  )
}

function SalarySection({ items }) {
  if (!items.length) return <EmptyOk msg="No salary or payroll compliance issues" detail="No salary entries found, or PF/ESI/PT deductions are correctly recorded." law="EPF Act 1952 | ESI Act 1948 | WB PT Act 1979" />
  return (
    <AuditTable
      headers={['Issue', 'Amount', 'Detail', 'Severity']}
      rows={items.map((s, i) => {
        const isCrit = s.severity === 'Critical'
        const isImp = s.severity === 'Important'
        const color = isCrit ? '#f87171' : isImp ? '#fbbf24' : '#34d399'
        const bg = isCrit ? 'rgba(239,68,68,0.15)' : isImp ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)'
        return (
          <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <td style={{ padding: '10px 16px', color: '#e2e8f0', fontSize: 12 }}>{s.issue || ''}</td>
            <td style={{ padding: '10px 16px', color, fontWeight: 600 }}>{s.amount ? fmt(s.amount) : '—'}</td>
            <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 11 }}>{s.impact || s.note || ''}</td>
            <td style={{ padding: '10px 16px' }}>{secTag(s.severity || 'Info', color, bg)}</td>
          </tr>
        )
      })}
    />
  )
}
