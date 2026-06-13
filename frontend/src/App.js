import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'

import Sidebar from './components/Sidebar'
import Header from './components/Header'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import QuickAudit from './pages/QuickAudit'
import FullAudit from './pages/FullAudit'
import BankRec from './pages/BankRec'
import TDSAnalysis from './pages/TDSAnalysis'
import Compliance from './pages/Compliance'
import AskCA from './pages/AskCA'
import History from './pages/History'
import Admin from './pages/Admin'

function PrivateLayout({ children }) {
  const loggedIn = localStorage.getItem('logged_in')
  if (!loggedIn) return <Navigate to="/" replace />
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <div style={{ marginLeft: '256px', flex: 1, minHeight: '100vh', background: 'var(--navy-900)' }}>
        <Header />
        {children}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard"  element={<PrivateLayout><Dashboard /></PrivateLayout>} />
        <Route path="/quickaudit" element={<PrivateLayout><QuickAudit /></PrivateLayout>} />
        <Route path="/fullaudit"  element={<PrivateLayout><FullAudit /></PrivateLayout>} />
        <Route path="/bankrec"    element={<PrivateLayout><BankRec /></PrivateLayout>} />
        <Route path="/tds"        element={<PrivateLayout><TDSAnalysis /></PrivateLayout>} />
        <Route path="/compliance" element={<PrivateLayout><Compliance /></PrivateLayout>} />
        <Route path="/askca"      element={<PrivateLayout><AskCA /></PrivateLayout>} />
        <Route path="/history"    element={<PrivateLayout><History /></PrivateLayout>} />
        <Route path="/admin"      element={<PrivateLayout><Admin /></PrivateLayout>} />
        <Route path="*"           element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
