/* ================================================
   F05 — src/App.jsx
   App router — All routes + AppLayout + RoleGuard
   ================================================ */

import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth }     from '@/hooks/useAuth'
import LoadingScreen   from '@/components/LoadingScreen'
import AppLayout       from '@/components/layout/AppLayout'
import RoleGuard       from '@/components/shared/RoleGuard'

// Pages
import LoginPage       from '@/pages/Login/index'
import WorklistPage    from '@/pages/Worklist/index'
import ViewerPage      from '@/pages/Viewer/index'
import ReportPage      from '@/pages/Report/index'
import SearchPage      from '@/pages/Search/index'
import MyStudiesPage   from '@/pages/MyStudies/index'
import AdminPage       from '@/pages/Admin/index'
import ComparePage     from '@/pages/Compare/index'

/**
 * ProtectedRoute — redirect /login nếu chưa đăng nhập
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <LoadingScreen />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

/**
 * DefaultRedirect — redirect theo role sau login
 */
function DefaultRedirect() {
  const { user } = useAuth()

  if (user?.role === 'patient') return <Navigate to="/my-studies" replace />
  return <Navigate to="/worklist" replace />
}

export default function App() {
  return (
    <HashRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected — wrapped in AppLayout */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* Worklist — admin, doctor, technician */}
          <Route
            path="/worklist"
            element={
              <RoleGuard roles={['admin', 'doctor', 'technician']}>
                <WorklistPage />
              </RoleGuard>
            }
          />

          {/* Viewer — all roles */}
          <Route path="/viewer/:id" element={<ViewerPage />} />

          {/* Compare — 2 studies side-by-side */}
          <Route path="/compare/:leftId/:rightId" element={<ComparePage />} />

          {/* Report — all roles (edit/readonly xử lý trong page) */}
          <Route path="/report/:id" element={<ReportPage />} />

          {/* Search — admin, doctor */}
          <Route
            path="/search"
            element={
              <RoleGuard roles={['admin', 'doctor']}>
                <SearchPage />
              </RoleGuard>
            }
          />

          {/* My Studies — patient only */}
          <Route
            path="/my-studies"
            element={
              <RoleGuard roles={['patient']}>
                <MyStudiesPage />
              </RoleGuard>
            }
          />

          {/* Admin — admin only */}
          <Route
            path="/admin"
            element={
              <RoleGuard roles={['admin']}>
                <AdminPage />
              </RoleGuard>
            }
          />
        </Route>

        {/* Default — redirect theo role */}
        <Route path="*" element={<DefaultRedirect />} />
      </Routes>
    </HashRouter>
  )
}
