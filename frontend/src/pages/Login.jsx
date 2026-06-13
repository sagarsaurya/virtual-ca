import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [email, setEmail] = useState('admin@company.com')
  const [password, setPassword] = useState('password')
  const navigate = useNavigate()

  const handleLogin = () => {
    localStorage.setItem('logged_in', 'true')
    navigate('/dashboard')
  }

  return (
    <div className="login-page min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-5" style={{background:'rgba(201,168,76,0.15)',border:'1px solid rgba(201,168,76,0.3)'}}>
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" stroke="#C9A84C" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M12 22V12M2 7l10 5 10-5" stroke="#C9A84C" strokeWidth="1.5"/>
            </svg>
          </div>
          <h1 className="font-display text-3xl font-bold text-white tracking-tight">VirtualCA</h1>
          <p className="mt-2 text-sm" style={{color:'#5A7A9A'}}>Intelligent Accounting. Trusted Results.</p>
        </div>

        <div className="glass rounded-2xl p-8">
          <p className="text-xs font-semibold uppercase tracking-widest mb-6" style={{color:'var(--gold-400)'}}>Client Portal</p>
          <div style={{display:'flex',flexDirection:'column',gap:'16px'}}>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{color:'#8AA8C0'}}>Email Address</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full rounded-xl px-4 py-3 text-sm focus:outline-none"
                style={{background:'rgba(255,255,255,0.06)',border:'1px solid rgba(201,168,76,0.2)',color:'white'}}/>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{color:'#8AA8C0'}}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key==='Enter' && handleLogin()}
                className="w-full rounded-xl px-4 py-3 text-sm focus:outline-none"
                style={{background:'rgba(255,255,255,0.06)',border:'1px solid rgba(201,168,76,0.2)',color:'white'}}/>
            </div>
            <button onClick={handleLogin} className="btn-gold w-full py-3 rounded-xl text-sm font-bold mt-2 transition">
              Sign In →
            </button>
          </div>
          <p className="text-center text-xs mt-5" style={{color:'#3A5A72'}}>Demo: any email / any password</p>
        </div>

        <p className="text-center text-xs mt-6" style={{color:'#2A4A62'}}>
          Secured &nbsp;·&nbsp; FY 2025–26 &nbsp;·&nbsp; India
        </p>
      </div>
    </div>
  )
}
