import { useState, useEffect, useRef } from 'react'
import { askCA } from '../api'

export default function AskCA() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Hello! I'm your AI CA. Upload a Trial Balance or Daybook to get started. I can answer questions about your books, find errors, and guide you on compliance." }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (q) => {
    const question = q || input.trim()
    if (!question) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: question }])
    setLoading(true)
    try {
      const r = await askCA(question, '')
      setMessages(prev => [...prev, { role: 'ai', text: r.data.answer || r.data.response || 'No answer received.' }])
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error connecting to AI. Please try again.' }])
    }
    setLoading(false)
  }

  const quickQuestions = [
    'What are my top 3 errors to fix first?',
    'How much TDS is pending?',
    'Am I ready to file ITR?',
    'Give me all journal entries needed to fix the errors',
  ]

  return (
    <div style={{height:'calc(100vh - 64px)',display:'flex',flexDirection:'column',overflow:'hidden'}}>
      {/* Header */}
      <div className="px-6 py-3 flex items-center justify-between flex-shrink-0" style={{background:'var(--navy-800)',borderBottom:'1px solid var(--navy-600)'}}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{background:'linear-gradient(135deg,#3b82f6,#7c3aed)'}}>
            <i className="fas fa-robot text-white text-sm"></i>
          </div>
          <div>
            <div className="font-bold" style={{color:'#f1f5f9'}}>Ask Your CA <span className="ml-1 text-xs px-2 py-0.5 rounded-full font-semibold" style={{background:'rgba(96,165,250,0.2)',color:'#60a5fa'}}>AI</span></div>
            <div className="text-xs" style={{color:'#64748b'}}>Powered by Groq AI</div>
          </div>
        </div>
        <button onClick={() => setMessages([{ role: 'ai', text: "Hello! I'm your AI CA. How can I help you?" }])} className="text-xs" style={{color:'#475569'}}><i className="fas fa-trash-alt"></i></button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xl px-4 py-3 text-sm ${m.role === 'ai' ? 'chat-bubble-ai' : 'chat-bubble-user'}`} style={{whiteSpace:'pre-wrap'}}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="chat-bubble-ai px-4 py-3">
              <div className="typing"><span></span><span></span><span></span></div>
            </div>
          </div>
        )}
        <div ref={bottomRef}/>
      </div>

      {/* Quick chips + input */}
      <div className="px-6 pb-6 flex-shrink-0" style={{background:'var(--navy-900)'}}>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {quickQuestions.map((q, i) => (
            <button key={i} onClick={() => send(q)} className="text-xs px-3 py-1.5 rounded-full transition" style={{background:'var(--navy-700)',border:'1px solid var(--navy-500)',color:'#94a3b8'}}>
              {q}
            </button>
          ))}
        </div>
        <div className="rounded-2xl p-3 flex items-end gap-3" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
          <textarea value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if(e.key==='Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
            rows={2} placeholder="Ask anything about your books..."
            className="flex-1 resize-none text-sm focus:outline-none" style={{background:'transparent',color:'#e2e8f0'}}/>
          <button onClick={() => send()} className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition" style={{background:'#3b82f6',color:'white'}}>
            <i className="fas fa-paper-plane text-sm"></i>
          </button>
        </div>
      </div>
    </div>
  )
}
