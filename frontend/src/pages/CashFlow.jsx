import { useState } from 'react'
import axios from 'axios'
const API = process.env.REACT_APP_API_URL || 'https://virtual-ca.onrender.com'
const fmt = n => '₹' + Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:0})
const card = {background:'var(--navy-800)',border:'1px solid var(--navy-600)',borderRadius:12,padding:16,marginBottom:10}

function ActivitySection({title,data:d,color,icon}){
  if(!d) return null
  return(
    <div style={card}>
      <div style={{display:'flex',justifyContent:'space-between',marginBottom:12,alignItems:'center'}}>
        <div style={{color,fontSize:13,fontWeight:700}}>{icon} {title}</div>
        <div style={{color:d.net>=0?'#34d399':'#f87171',fontSize:14,fontWeight:700}}>{d.net>=0?'+':''}{fmt(d.net)}</div>
      </div>
      {d.inflows?.length>0&&(
        <div style={{marginBottom:8}}>
          <div style={{color:'#4A6A8A',fontSize:10,marginBottom:4}}>INFLOWS</div>
          {d.inflows.map((it,i)=>(
            <div key={i} style={{display:'flex',justifyContent:'space-between',padding:'5px 0',borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
              <span style={{color:'#8AA8C0',fontSize:11}}>{it.label}</span>
              <span style={{color:'#34d399',fontSize:11,fontWeight:600}}>+{fmt(it.amount)}</span>
            </div>
          ))}
        </div>
      )}
      {d.outflows?.length>0&&(
        <div>
          <div style={{color:'#4A6A8A',fontSize:10,marginBottom:4}}>OUTFLOWS</div>
          {d.outflows.map((it,i)=>(
            <div key={i} style={{display:'flex',justifyContent:'space-between',padding:'5px 0',borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
              <span style={{color:'#8AA8C0',fontSize:11}}>{it.label}</span>
              <span style={{color:'#f87171',fontSize:11,fontWeight:600}}>-{fmt(it.amount)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function CashFlow() {
  const [loading,setLoading]=useState(false)
  const [data,setData]=useState(null)
  const [error,setError]=useState('')
  const cid=localStorage.getItem('company_id')||1
  const h={'X-Company-ID':cid}

  const run=async()=>{
    setLoading(true);setError('')
    try{const r=await axios.post(`${API}/api/cash-flow`,{},{headers:h});setData(r.data)}
    catch(e){setError(e.response?.data?.error||e.message)}
    setLoading(false)
  }

  return(
    <div style={{padding:20}}>
      {!data&&!loading&&(
        <div style={{textAlign:'center',padding:40}}>
          <div style={{fontSize:32,marginBottom:12}}>💧</div>
          <div style={{color:'#F5F0E6',fontWeight:600,marginBottom:6}}>Cash Flow Statement</div>
          <div style={{color:'#4A6A8A',fontSize:13,marginBottom:20}}>AS-3 format · Operating / Investing / Financing</div>
          <button onClick={run} style={{background:'var(--gold-500)',color:'var(--navy-900)',border:'none',borderRadius:10,padding:'12px 28px',fontWeight:700,fontSize:14,cursor:'pointer'}}>
            Generate Cash Flow
          </button>
          {error&&<div style={{color:'#f87171',marginTop:12,fontSize:12}}>{error}</div>}
        </div>
      )}
      {loading&&<div style={{textAlign:'center',padding:40,color:'#C9A84C'}}>Generating...</div>}
      {data&&(
        <>
          <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:10,marginBottom:14}}>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>Opening Cash</div><div style={{color:'#F5F0E6',fontSize:16,fontWeight:700}}>{fmt(data.opening_cash)}</div></div>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>Operating</div><div style={{color:data.operating?.net>=0?'#34d399':'#f87171',fontSize:16,fontWeight:700}}>{data.operating?.net>=0?'+':''}{fmt(data.operating?.net)}</div></div>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>Net Cash Flow</div><div style={{color:data.net_cash_flow>=0?'#34d399':'#f87171',fontSize:16,fontWeight:700}}>{data.net_cash_flow>=0?'+':''}{fmt(data.net_cash_flow)}</div></div>
            <div style={{...card,margin:0}}><div style={{color:'#4A6A8A',fontSize:11}}>Closing Cash</div><div style={{color:'#C9A84C',fontSize:16,fontWeight:700}}>{fmt(data.closing_cash)}</div></div>
          </div>

          <ActivitySection title="Operating Activities" data={data.operating} color="#60a5fa" icon="⚙️"/>
          <ActivitySection title="Investing Activities" data={data.investing} color="#a78bfa" icon="📊"/>
          <ActivitySection title="Financing Activities" data={data.financing} color="#fbbf24" icon="🏦"/>

          <div style={{...card,borderTop:'2px solid var(--navy-600)',borderRadius:'0 0 12px 12px'}}>
            <div style={{display:'flex',justifyContent:'space-between'}}>
              <span style={{color:'#F5F0E6',fontWeight:600,fontSize:13}}>Closing Cash & Cash Equivalents</span>
              <span style={{color:'#C9A84C',fontSize:14,fontWeight:700}}>{fmt(data.closing_cash)}</span>
            </div>
          </div>

          <div style={{display:'flex',gap:8,marginTop:4}}>
            <button onClick={()=>window.print()} style={{fontSize:12,padding:'7px 14px',background:'rgba(16,185,129,0.15)',color:'#34d399',border:'1px solid rgba(16,185,129,0.3)',borderRadius:8,cursor:'pointer'}}>Download PDF</button>
            <button onClick={()=>setData(null)} style={{fontSize:12,padding:'7px 14px',background:'var(--navy-700)',color:'#8AA8C0',border:'1px solid var(--navy-600)',borderRadius:8,cursor:'pointer'}}>Regenerate</button>
          </div>
        </>
      )}
    </div>
  )
}
