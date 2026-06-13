import { useState } from 'react'
import axios from 'axios'
const API = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'
const fmt = n => '₹' + Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:0})
const card = {background:'var(--navy-800)',border:'1px solid var(--navy-600)',borderRadius:12,padding:16,marginBottom:10}

const RISK_COLOR = {high:'#f87171',medium:'#fbbf24',low:'#34d399'}
const RISK_BG = {high:'rgba(239,68,68,0.1)',medium:'rgba(245,158,11,0.1)',low:'rgba(52,211,153,0.1)'}

export default function DocChecker() {
  const [loading,setLoading]=useState(false)
  const [data,setData]=useState(null)
  const [error,setError]=useState('')
  const [filter,setFilter]=useState('all')
  const cid=localStorage.getItem('company_id')||1
  const h={'X-Company-ID':cid}

  const run=async()=>{
    setLoading(true);setError('')
    try{const r=await axios.post(`${API}/api/doc-checker`,{},{headers:h});setData(r.data)}
    catch(e){setError(e.response?.data?.error||e.message)}
    setLoading(false)
  }

  const filtered = data?.flagged?.filter(f=>filter==='all'||f.risk===filter)||[]

  return(
    <div style={{padding:20}}>
      {!data&&!loading&&(
        <div style={{textAlign:'center',padding:40}}>
          <div style={{fontSize:32,marginBottom:12}}>📎</div>
          <div style={{color:'#F5F0E6',fontWeight:600,marginBottom:6}}>Missing Document Checker</div>
          <div style={{color:'#4A6A8A',fontSize:13,marginBottom:20}}>Flags entries without bill/invoice reference — audit-critical</div>
          <button onClick={run} style={{background:'var(--gold-500)',color:'var(--navy-900)',border:'none',borderRadius:10,padding:'12px 28px',fontWeight:700,fontSize:14,cursor:'pointer'}}>
            Check Documents
          </button>
          {error&&<div style={{color:'#f87171',marginTop:12,fontSize:12}}>{error}</div>}
        </div>
      )}
      {loading&&<div style={{textAlign:'center',padding:40,color:'#C9A84C'}}>Scanning daybook...</div>}
      {data&&(
        <>
          <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:10,marginBottom:14}}>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>Flagged</div><div style={{color:'#f87171',fontSize:18,fontWeight:700}}>{data.flagged?.length||0}</div><div style={{color:'#4A6A8A',fontSize:10}}>entries</div></div>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>High Risk</div><div style={{color:'#f87171',fontSize:18,fontWeight:700}}>{data.high_risk_count||0}</div><div style={{color:'#4A6A8A',fontSize:10}}>missing bills</div></div>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>Amount at Risk</div><div style={{color:'#fbbf24',fontSize:18,fontWeight:700}}>{fmt(data.total_amount_at_risk)}</div><div style={{color:'#4A6A8A',fontSize:10}}>no docs</div></div>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>With Docs</div><div style={{color:'#34d399',fontSize:18,fontWeight:700}}>{data.documented||0}</div><div style={{color:'#4A6A8A',fontSize:10}}>entries OK</div></div>
          </div>

          <div style={{display:'flex',gap:8,marginBottom:12}}>
            {['all','high','medium','low'].map(f=>(
              <button key={f} onClick={()=>setFilter(f)} style={{fontSize:11,padding:'5px 12px',background:filter===f?'rgba(201,168,76,0.15)':'transparent',color:filter===f?'#C9A84C':'#4A6A8A',border:`1px solid ${filter===f?'rgba(201,168,76,0.3)':'var(--navy-600)'}`,borderRadius:8,cursor:'pointer',textTransform:'capitalize'}}>
                {f==='all'?`All (${data.flagged?.length||0})`:f+' risk'}
              </button>
            ))}
          </div>

          <div style={card}>
            {filtered.length===0?<div style={{color:'#4A6A8A',fontSize:12}}>No entries in this category.</div>:
            <table style={{width:'100%',borderCollapse:'collapse',fontSize:11}}>
              <thead><tr style={{borderBottom:'1px solid var(--navy-600)'}}>
                {['Date','Ledger','Narration','Amount','Risk','Issue'].map(h=>(
                  <th key={h} style={{textAlign:'left',padding:'6px 10px',color:'#4A6A8A',fontSize:10}}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {filtered.map((f,i)=>(
                  <tr key={i} style={{borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
                    <td style={{padding:'8px 10px',color:'#8AA8C0'}}>{f.date}</td>
                    <td style={{padding:'8px 10px',color:'#e2e8f0',fontWeight:500}}>{f.ledger}</td>
                    <td style={{padding:'8px 10px',color:'#8AA8C0',maxWidth:180,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{f.narration}</td>
                    <td style={{padding:'8px 10px',color:'#F5F0E6',fontWeight:600}}>{fmt(f.amount)}</td>
                    <td style={{padding:'8px 10px'}}>
                      <span style={{background:RISK_BG[f.risk],color:RISK_COLOR[f.risk],fontSize:10,padding:'2px 6px',borderRadius:99,textTransform:'capitalize'}}>{f.risk}</span>
                    </td>
                    <td style={{padding:'8px 10px',color:'#4A6A8A',fontSize:10}}>{f.issue}</td>
                  </tr>
                ))}
              </tbody>
            </table>}
          </div>

          {data.flagged?.length>0&&(
            <div style={{...card,borderLeft:'3px solid #C9A84C',borderRadius:'0 12px 12px 0'}}>
              <div style={{color:'#C9A84C',fontSize:12,fontWeight:600,marginBottom:4}}>Auditor's Note</div>
              <div style={{color:'#8AA8C0',fontSize:11}}>Collect bills/invoices for all {data.flagged.length} flagged entries before tax filing. High-risk entries without documents can be disallowed as expenses under Section 37(1) of Income Tax Act.</div>
            </div>
          )}
          <button onClick={()=>setData(null)} style={{fontSize:12,padding:'7px 14px',background:'var(--navy-700)',color:'#8AA8C0',border:'1px solid var(--navy-600)',borderRadius:8,cursor:'pointer',marginTop:4}}>Re-check</button>
        </>
      )}
    </div>
  )
}
