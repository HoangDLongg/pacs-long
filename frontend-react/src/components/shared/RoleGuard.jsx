/* ================================================
   F10 — src/components/shared/RoleGuard.jsx
   Wrapper check quyền — redirect nếu sai role
   ================================================ */

import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

/**
 * RoleGuard — chặn truy cập theo role
 *
 * Usage:
 *   <RoleGuard roles={['admin', 'doctor']}>
 *     <SomePage />
 *   </RoleGuard>
 *
 * Nếu role không nằm trong danh sách:
 *   - patient → redirect /my-studies
 *   - others → redirect /worklist
 */
export default function RoleGuard({ roles, children }) {
  const { user } = useAuth()

  const userRole = user?.role

  // Nếu không có role restriction → cho qua
  if (!roles || roles.length === 0) return children

  // Role hợp lệ → render children
  if (roles.includes(userRole)) return children

  // Role không hợp lệ → redirect
  if (userRole === 'patient') {
    return <Navigate to="/my-studies" replace />
  }

  return <Navigate to="/worklist" replace />
}
