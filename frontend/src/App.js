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
import BalanceSheet from './pages/BalanceSheet'
import TDSDetect from './pages/TDSDetect'
import GSTReturn from './pages/GSTReturn'
import SharesPnL from './pages/SharesPnL'
import CashFlow from './pages/CashFlow'
import PartyRec from './pages/PartyRec'
import DocChecker from './pages/DocChecker'
import BrokerRec from './pages/BrokerRec'

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
        <Route path="/admin"       element={<PrivateLayout><Admin /></PrivateLayout>} />
        <Route path="/balance-sheet" element={<PrivateLayout><BalanceSheet /></PrivateLayout>} />
        <Route path="/tds-detect"  element={<PrivateLayout><TDSDetect /></PrivateLayout>} />
        <Route path="/gst-return"  element={<PrivateLayout><GSTReturn /></PrivateLayout>} />
        <Route path="/shares-pnl"  element={<PrivateLayout><SharesPnL /></PrivateLayout>} />
        <Route path="/cash-flow"   element={<PrivateLayout><CashFlow /></PrivateLayout>} />
        <Route path="/party-rec"   element={<PrivateLayout><PartyRec /></PrivateLayout>} />
        <Route path="/doc-checker" element={<PrivateLayout><DocChecker /></PrivateLayout>} />
        <Route path="/broker-rec"  element={<PrivateLayout><BrokerRec /></PrivateLayout>} />
        <Route path="*"            element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
