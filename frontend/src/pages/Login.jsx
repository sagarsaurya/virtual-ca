import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [tab, setTab]         = useState('login')   // 'login' | 'signup'
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()

  const handleLogin = async () => {
    setError(''); setSuccess('')
    if (!email || !password) { setError('Enter email and password'); return }
    setLoading(true)
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Login failed'); return }
      localStorage.setItem('auth_token', data.token)
      localStorage.setItem('auth_email', data.email)
      localStorage.setItem('logged_in', 'true')
      navigate('/dashboard')
    } catch (e) {
      setError('Network error — try again')
    } finally {
      setLoading(false)
    }
  }

  const handleSignup = async () => {
    setError(''); setSuccess('')
    if (!email || !password) { setError('Enter email and password'); return }
    if (password !== confirm) { setError('Passwords do not match'); return }
    if (password.length < 6) { setError('Password must be at least 6 characters'); return }
    setLoading(true)
    try {
      const res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Signup failed'); return }
      if (data.token) {
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('auth_email', data.email)
        localStorage.setItem('logged_in', 'true')
        navigate('/dashboard')
      } else {
        setSuccess('Account created! Check your email to confirm, then log in.')
        setTab('login')
      }
    } catch (e) {
      setError('Network error — try again')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-5"
            style={{background:'rgba(201,168,76,0.15)',border:'1px solid rgba(201,168,76,0.3)'}}>
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" stroke="#C9A84C" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M12 22V12M2 7l10 5 10-5" stroke="#C9A84C" strokeWidth="1.5"/>
            </svg>
          </div>
          <h1 className="font-display text-3xl font-bold text-white tracking-tight">VirtualCA</h1>
          <p className="mt-2 text-sm" style={{color:'#5A7A9A'}}>Intelligent Accounting. Trusted Results.</p>
        </div>

        <div className="glass rounded-2xl p-8">
          {/* Tab switcher */}
          <div style={{display:'flex',gap:'4px',background:'rgba(255,255,255,0.05)',borderRadius:'10px',padding:'4px',marginBottom:'24px'}}>
            {['login','signup'].map(t => (
              <button key={t} onClick={() => { setTab(t); setError(''); setSuccess('') }}
                style={{
                  flex:1, padding:'8px', borderRadius:'8px', fontSize:'13px', fontWeight:600,
                  border:'none', cursor:'pointer', transition:'all 0.2s',
                  background: tab===t ? 'rgba(201,168,76,0.2)' : 'transparent',
                  color: tab===t ? '#C9A84C' : '#5A7A9A',
                }}>
                {t === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <div style={{display:'flex',flexDirection:'column',gap:'14px'}}>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{color:'#8AA8C0'}}>Email Address</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-xl px-4 py-3 text-sm focus:outline-none"
                style={{background:'rgba(255,255,255,0.06)',border:'1px solid rgba(201,168,76,0.2)',color:'white'}}/>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{color:'#8AA8C0'}}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                onKeyDown={e => e.key==='Enter' && (tab==='login' ? handleLogin() : null)}
                className="w-full rounded-xl px-4 py-3 text-sm focus:outline-none"
                style={{background:'rgba(255,255,255,0.06)',border:'1px solid rgba(201,168,76,0.2)',color:'white'}}/>
            </div>
            {tab === 'signup' && (
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{color:'#8AA8C0'}}>Confirm Password</label>
                <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
                  placeholder="••••••••"
                  onKeyDown={e => e.key==='Enter' && handleSignup()}
                  className="w-full rounded-xl px-4 py-3 text-sm focus:outline-none"
                  style={{background:'rgba(255,255,255,0.06)',border:'1px solid rgba(201,168,76,0.2)',color:'white'}}/>
              </div>
            )}

            {error && (
              <div style={{background:'rgba(248,113,113,0.1)',border:'1px solid rgba(248,113,113,0.3)',borderRadius:'10px',padding:'10px 14px',color:'#f87171',fontSize:'13px'}}>
                {error}
              </div>
            )}
            {success && (
              <div style={{background:'rgba(52,211,153,0.1)',border:'1px solid rgba(52,211,153,0.3)',borderRadius:'10px',padding:'10px 14px',color:'#34d399',fontSize:'13px'}}>
                {success}
              </div>
            )}

            <button
              onClick={tab === 'login' ? handleLogin : handleSignup}
              disabled={loading}
              className="btn-gold w-full py-3 rounded-xl text-sm font-bold mt-1 transition"
              style={{opacity: loading ? 0.7 : 1, cursor: loading ? 'not-allowed' : 'pointer'}}>
              {loading ? 'Please wait...' : tab === 'login' ? 'Sign In →' : 'Create Account →'}
            </button>
          </div>
        </div>

        <p className="text-center text-xs mt-6" style={{color:'#2A4A62'}}>
          Secured &nbsp;·&nbsp; Your data is private &nbsp;·&nbsp; India
        </p>
      </div>
    </div>
  )
}
