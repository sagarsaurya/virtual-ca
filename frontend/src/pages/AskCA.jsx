import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { askCA } from '../api'

const API_URL = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'
const getHeaders = () => { const t=localStorage.getItem('auth_token'); return {'X-Company-ID':localStorage.getItem('company_id')||1,...(t?{Authorization:`Bearer ${t}`}:{})} }

const SEVERITY_COLOR = { critical: '#ef4444', warning: '#f97316', info: '#60a5fa' }
const SEVERITY_BG    = { critical: 'rgba(239,68,68,0.08)', warning: 'rgba(249,115,22,0.08)', info: 'rgba(96,165,250,0.08)' }
const SEVERITY_BORDER= { critical: 'rgba(239,68,68,0.2)', warning: 'rgba(249,115,22,0.2)', info: 'rgba(96,165,250,0.2)' }

function buildIssues(data) {
  if (!data) return []
  const issues = []

  // Ledger classification errors
  ;(data.ledger_issues || []).forEach(i => issues.push({
    id: `led-${issues.length}`,
    category: 'Ledger',
    severity: i.severity === 'critical' ? 'critical' : 'warning',
    title: i.ledger || i.name || 'Ledger Issue',
    detail: i.issue || i.rule || '',
    amount: i.balance,
    context: `Ledger: ${i.ledger || i.name}\nGroup: ${i.current_group || ''} → should be ${i.correct_group || ''}\nBalance: ₹${Number(i.balance||0).toLocaleString('en-IN')}\nIssue: ${i.issue || i.rule || ''}`,
  }))

  // Cash violations
  ;(data.cash_violations || []).forEach(i => issues.push({
    id: `cash-${issues.length}`,
    category: 'Cash Violation',
    severity: 'critical',
    title: i.party || 'Cash Payment',
    detail: `₹${Number(i.amount||0).toLocaleString('en-IN')} on ${i.date || ''}`,
    amount: i.amount,
    context: `Cash Violation (Sec 40A(3))\nParty: ${i.party}\nAmount: ₹${Number(i.amount||0).toLocaleString('en-IN')}\nDate: ${i.date || ''}\nVoucher: ${i.voucher_type || 'Payment'}\nIssue: Cash payment above ₹10,000 limit`,
  }))

  // Outstanding balances
  ;(data.outstanding_balances || []).forEach(i => issues.push({
    id: `out-${issues.length}`,
    category: 'Outstanding',
    severity: i.severity === 'critical' ? 'critical' : 'warning',
    title: i.ledger || 'Outstanding Balance',
    detail: i.question || i.issue || '',
    amount: i.amount,
    context: `Outstanding Balance Issue\nLedger: ${i.ledger}\nAmount: ₹${Number(i.amount||0).toLocaleString('en-IN')}\nIssue: ${i.question || i.issue || ''}`,
  }))

  // Large expenses (TDS)
  ;(data.large_expenses || []).forEach(i => issues.push({
    id: `tds-${issues.length}`,
    category: 'TDS',
    severity: 'warning',
    title: i.party || 'Large Expense',
    detail: `₹${Number(i.amount||0).toLocaleString('en-IN')} — ${i.question || 'TDS may apply'}`,
    amount: i.amount,
    context: `Possible TDS Applicable\nParty: ${i.party}\nAmount: ₹${Number(i.amount||0).toLocaleString('en-IN')}\nDate: ${i.date || ''}\nVoucher: ${i.voucher_type || ''}\nQuestion: ${i.question || 'Is TDS deducted on this payment?'}`,
  }))

  // Loans
  ;(data.loans || []).forEach(i => issues.push({
    id: `loan-${issues.length}`,
    category: 'Loan',
    severity: 'info',
    title: i.ledger || 'Loan',
    detail: i.question || `Balance: ₹${Number(i.balance||0).toLocaleString('en-IN')}`,
    amount: i.balance,
    context: `Loan Entry\nLedger: ${i.ledger}\nBalance: ₹${Number(i.balance||0).toLocaleString('en-IN')}\nQuestion: ${i.question || ''}`,
  }))

  return issues
}

export default function AskCA() {
  const [auditData, setAuditData]     = useState(null)
  const [issues, setIssues]           = useState([])
  const [selected, setSelected]       = useState(null)
  const [messages, setMessages]       = useState([])
  const [input, setInput]             = useState('')
  const [loading, setLoading]         = useState(false)
  const [filter, setFilter]           = useState('all')
  const bottomRef = useRef(null)

  useEffect(() => {
    axios.get(`${API_URL}/api/audit/result`, { headers: getHeaders() })
      .then(r => {
        setAuditData(r.data)
        const built = buildIssues(r.data)
        setIssues(built)
        if (built.length > 0) selectIssue(built[0])
      })
      .catch(() => {
        setMessages([{ role: 'ai', text: "No audit data found. Please run a Quick Audit first, then come back here." }])
      })
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const selectIssue = (issue) => {
    setSelected(issue)
    const greeting = `I've selected the **${issue.category}** issue for **${issue.title}**.\n\n${issue.context}\n\nWhat would you like to know about this? You can ask about the impact, how to fix it in Tally, applicable law/section, or anything else.`
    setMessages([{ role: 'ai', text: greeting }])
    setInput('')
  }

  const send = async (q) => {
    const question = q || input.trim()
    if (!question) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: question }])
    setLoading(true)
    try {
      const context = selected ? selected.context : ''
      const r = await askCA(question, context)
      setMessages(prev => [...prev, { role: 'ai', text: r.data.answer || r.data.response || 'No answer received.' }])
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error connecting to AI. Please try again.' }])
    }
    setLoading(false)
  }

  const filtered = filter === 'all' ? issues : issues.filter(i => i.severity === filter)
  const summary  = auditData?.summary || {}

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>

      {/* LEFT PANEL — Issues */}
      <div style={{ width: 320, flexShrink: 0, borderRight: '1px solid var(--navy-600)', display: 'flex', flexDirection: 'column', background: 'var(--navy-900)' }}>

        {/* Left header */}
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--navy-600)', flexShrink: 0 }}>
          <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 13, marginBottom: 2 }}>Issues Found</div>
          {summary.score !== undefined && (
            <div style={{ color: '#64748b', fontSize: 11 }}>
              Score {summary.score}/100 · {summary.critical || 0} critical · {summary.warnings || 0} warnings
            </div>
          )}
          {/* Filter tabs */}
          <div style={{ display: 'flex', gap: 4, marginTop: 10 }}>
            {[['all','All'], ['critical','Critical'], ['warning','Warning'], ['info','Info']].map(([v, label]) => (
              <button key={v} onClick={() => setFilter(v)}
                style={{ fontSize: 10, padding: '3px 8px', borderRadius: 6, border: 'none', cursor: 'pointer',
                  background: filter === v ? 'var(--gold-500)' : 'var(--navy-700)',
                  color: filter === v ? 'var(--navy-900)' : '#64748b', fontWeight: filter === v ? 700 : 400 }}>
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Issue list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {filtered.length === 0 && (
            <div style={{ padding: 20, color: '#64748b', fontSize: 12, textAlign: 'center' }}>
              {issues.length === 0 ? 'Run a Quick Audit first to see issues here.' : 'No issues in this category.'}
            </div>
          )}
          {filtered.map(issue => (
            <div key={issue.id} onClick={() => selectIssue(issue)}
              style={{
                padding: '12px 14px', cursor: 'pointer', borderBottom: '1px solid var(--navy-700)',
                background: selected?.id === issue.id ? SEVERITY_BG[issue.severity] : 'transparent',
                borderLeft: selected?.id === issue.id ? `3px solid ${SEVERITY_COLOR[issue.severity]}` : '3px solid transparent',
                transition: 'all 0.15s'
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                  background: SEVERITY_BG[issue.severity], color: SEVERITY_COLOR[issue.severity],
                  border: `1px solid ${SEVERITY_BORDER[issue.severity]}` }}>
                  {issue.category.toUpperCase()}
                </span>
                {issue.severity === 'critical' && <i className="fas fa-circle-exclamation" style={{ color: '#ef4444', fontSize: 10 }}></i>}
              </div>
              <div style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{issue.title}</div>
              <div style={{ color: '#64748b', fontSize: 11, lineHeight: 1.4 }}>{issue.detail}</div>
              {issue.amount && (
                <div style={{ color: SEVERITY_COLOR[issue.severity], fontSize: 11, fontWeight: 600, marginTop: 4 }}>
                  ₹{Number(issue.amount).toLocaleString('en-IN')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* RIGHT PANEL — Chat */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Chat header */}
        <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--navy-600)', background: 'var(--navy-800)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: 'linear-gradient(135deg,#3b82f6,#7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <i className="fas fa-robot text-white text-sm"></i>
            </div>
            <div>
              <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 13 }}>
                Ask Your CA
                <span style={{ marginLeft: 8, fontSize: 10, padding: '2px 8px', borderRadius: 99, background: 'rgba(96,165,250,0.2)', color: '#60a5fa', fontWeight: 700 }}>AI</span>
              </div>
              <div style={{ color: '#64748b', fontSize: 11 }}>
                {selected ? `Discussing: ${selected.title}` : 'Select an issue from the left to begin'}
              </div>
            </div>
          </div>
          <button onClick={() => selected && selectIssue(selected)} title="Reset chat for this issue"
            style={{ color: '#475569', fontSize: 11, background: 'none', border: 'none', cursor: 'pointer' }}>
            <i className="fas fa-rotate-left"></i>
          </button>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: 60, color: '#475569' }}>
              <i className="fas fa-arrow-left" style={{ fontSize: 24, marginBottom: 12, display: 'block' }}></i>
              <div style={{ fontSize: 13 }}>Select an issue from the left panel</div>
              <div style={{ fontSize: 11, marginTop: 4 }}>Then ask anything about it</div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 12 }}>
              <div className={m.role === 'ai' ? 'chat-bubble-ai' : 'chat-bubble-user'}
                style={{ maxWidth: '80%', padding: '10px 14px', fontSize: 13, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 12 }}>
              <div className="chat-bubble-ai" style={{ padding: '10px 14px' }}>
                <div className="typing"><span></span><span></span><span></span></div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Quick chips */}
        {selected && (
          <div style={{ padding: '8px 20px 0', flexShrink: 0 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {[
                'What is the exact penalty for this?',
                'How do I fix this in Tally?',
                'Which section of law applies?',
                'What journal entry is needed?',
                'What happens if I ignore this?',
              ].map((q, i) => (
                <button key={i} onClick={() => send(q)}
                  style={{ fontSize: 11, padding: '4px 10px', borderRadius: 99, cursor: 'pointer',
                    background: 'var(--navy-700)', border: '1px solid var(--navy-500)', color: '#94a3b8' }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div style={{ padding: '10px 20px 16px', flexShrink: 0, background: 'var(--navy-900)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, background: 'var(--navy-800)', border: '1px solid var(--navy-600)', borderRadius: 14, padding: '10px 12px' }}>
            <textarea value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              rows={2} placeholder={selected ? `Ask anything about "${selected.title}"...` : 'Select an issue first...'}
              disabled={!selected}
              style={{ flex: 1, resize: 'none', fontSize: 13, background: 'transparent', color: '#e2e8f0', border: 'none', outline: 'none' }} />
            <button onClick={() => send()} disabled={!selected || loading}
              style={{ width: 36, height: 36, borderRadius: 10, background: '#3b82f6', color: 'white', border: 'none', cursor: selected ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, opacity: selected ? 1 : 0.4 }}>
              <i className="fas fa-paper-plane" style={{ fontSize: 13 }}></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
