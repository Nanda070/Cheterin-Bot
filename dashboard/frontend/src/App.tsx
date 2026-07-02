import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/Login'
import { AccessDeniedPage } from './pages/AccessDenied'
import { DashboardShell } from './pages/DashboardShell'
import { HomePage } from './pages/Home'
import { MembersPage } from './pages/Members'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/access-denied" element={<AccessDeniedPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<HomePage />} />
            <Route path="members" element={<MembersPage />} />
            <Route path="lockdown" element={<div>Lockdown — скоро (Task 11)</div>} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
