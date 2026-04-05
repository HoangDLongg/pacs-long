/* ================================================
   T013 — src/App.jsx
   App router — US1 scope only
   /login → LoginPage
   /worklist (placeholder) → PlaceholderPage
   /* → redirect /login
   ================================================ */

import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import LoginPage      from '@/pages/Login/index'
import PlaceholderPage from '@/pages/Placeholder'
import LoadingScreen  from '@/components/LoadingScreen'

/**
 * ProtectedRoute
 * Nếu chưa đăng nhập → redirect /login
 * Nếu đang check auth (loading) → hiện loading screen
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <LoadingScreen />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <HashRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected — US1: placeholder cho /worklist */}
        <Route
          path="/worklist"
          element={
            <ProtectedRoute>
              <PlaceholderPage />
            </ProtectedRoute>
          }
        />

        {/* Mọi route khác → /login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </HashRouter>
  )
}
