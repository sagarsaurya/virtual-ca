import { useEffect, useState } from 'react'
import { getCompliance } from '../api'

export default function Compliance() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCompliance().then(r => { setItems(r.data.items || r.data || []); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const overdue = items.filter(i => i.status === 'overdue').length
  const upcoming = items.filter(i => i.status === 'upcoming').length
  const done = items.filter(i => i.status === 'done').length

  const statusClass = { overdue: 'overdue', upcoming: 'upcoming', done: 'done' }
  const statusColor = { overdue: { bg:'#DC2626', text:'#f87171', badge:'OVERDUE', badgeBg:'rgba(239,68,68,0.15)' }, upcoming: { bg:'#D97706', text:'#fbbf24', badge:'UPCOMING', badgeBg:'rgba(245,158,11,0.15)' }, done: { bg:'#15803D', text:'#34d399', badge:'✓ DONE', badgeBg:'rgba(52,211,153,0.12)' } }

  return (
    <div className="p-8">
      <div className="grid grid-cols-3 gap-5 mb-6">
        <div className="stat-card" style={{borderTop:'2px solid #DC2626'}}>
          <div className="text-xs font-semibold uppercase tracking-wider mb-3" style={{color:'#94a3b8'}}>Overdue</div>
          <div className="text-3xl font-bold" style={{color:'#f87171'}}>{overdue}</div>
        </div>
        <div className="stat-card" style={{borderTop:'2px solid #D97706'}}>
          <div className="text-xs font-semibold uppercase tracking-wider mb-3" style={{color:'#94a3b8'}}>Due This Week</div>
          <div className="text-3xl font-bold" style={{color:'#fbbf24'}}>{upcoming}</div>
        </div>
        <div className="stat-card" style={{borderTop:'2px solid #15803D'}}>
          <div className="text-xs font-semibold uppercase tracking-wider mb-3" style={{color:'#94a3b8'}}>On Track</div>
          <div className="text-3xl font-bold" style={{color:'#34d399'}}>{done}</div>
        </div>
      </div>

      <div className="rounded-2xl p-6" style={{background:'var(--navy-800)',border:'1px solid var(--navy-600)'}}>
        <h3 className="text-sm font-semibold mb-5" style={{color:'#f1f5f9'}}>Upcoming Due Dates — Real Time</h3>
        {loading
          ? <div className="text-center py-8 text-sm" style={{color:'#64748b'}}>Loading...</div>
          : items.length === 0
          ? <div className="text-center py-8 text-sm" style={{color:'#64748b'}}>No compliance items found</div>
          : items.map((item, i) => {
            const s = statusColor[item.status] || statusColor.upcoming
            return (
              <div key={i} className={`compliance-card ${statusClass[item.status]||'upcoming'} rounded-xl p-4 flex items-center gap-4 mb-3`}>
                <div className="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0" style={{background:s.badgeBg}}>
                  <div className="text-center">
                    <div className="font-bold text-lg leading-none" style={{color:s.text}}>{item.day}</div>
                    <div className="text-xs" style={{color:s.text}}>{item.month}</div>
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm" style={{color:'#f1f5f9'}}>{item.title}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{background:s.badgeBg,color:s.text}}>{s.badge}</span>
                  </div>
                  <div className="text-sm" style={{color:'#94a3b8'}}>{item.description}</div>
                  {item.note && <div className="text-xs mt-1" style={{color:'#64748b'}}>{item.note}</div>}
                </div>
                {item.status !== 'done' && (
                  <button className="px-4 py-2 rounded-xl text-xs font-medium" style={{background:s.badgeBg,color:s.text,border:`1px solid ${s.text}33`}}>Mark Done</button>
                )}
                {item.status === 'done' && <i className="fas fa-check-circle text-xl" style={{color:'#34d399'}}></i>}
              </div>
            )
          })
        }
      </div>
    </div>
  )
}
