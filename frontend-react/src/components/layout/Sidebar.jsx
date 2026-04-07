/* ================================================
   F01 — src/components/layout/Sidebar.jsx
   Menu sidebar — filtered by user role
   ================================================ */

import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

/**
 * Menu items theo role (spec kit)
 * Admin:      Worklist | Search | Admin
 * Doctor:     Worklist | Search
 * Technician: Worklist
 * Patient:    My Studies
 */
const MENU_ITEMS = [
  {
    path: '/worklist',
    label: 'Worklist',
    roles: ['admin', 'doctor', 'technician'],
  },
  {
    path: '/search',
    label: 'Tim kiem',
    roles: ['admin', 'doctor'],
  },
  {
    path: '/my-studies',
    label: 'Ca cua toi',
    roles: ['patient'],
  },
  {
    path: '/admin',
    label: 'Quan tri',
    roles: ['admin'],
  },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const role = user?.role || 'doctor'
  const visibleItems = MENU_ITEMS.filter(item => item.roles.includes(role))

  // Lấy chữ cái đầu cho avatar
  const initials = (user?.full_name || user?.username || 'U')
    .split(' ')
    .map(w => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="sidebar">

      {/* Header: Logo + Title */}
      <div className="sidebar__header">
        <img src="/logo.svg" alt="PACS++" className="sidebar__logo" />
        <div>
          <div className="sidebar__title">PACS++</div>
          <div className="sidebar__subtitle">System Hospitals</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        {visibleItems.map(item => {
          const isActive = location.pathname === item.path ||
            location.pathname.startsWith(item.path + '/')

          return (
            <button
              key={item.path}
              className={`sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
              onClick={() => navigate(item.path)}
              id={`nav-${item.path.replace('/', '')}`}
            >
              <span className="sidebar__label">{item.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Footer: User info + Logout */}
      <div className="sidebar__footer">
        <div className="sidebar__user">
          <div className="sidebar__avatar">{initials}</div>
          <div>
            <div className="sidebar__user-name">{user?.full_name || user?.username}</div>
            <div className="sidebar__user-role">{role}</div>
          </div>
        </div>
        <button
          id="btn-logout"
          className="btn btn-secondary btn-block"
          onClick={handleLogout}
        >
          Dang xuat
        </button>
      </div>

    </aside>
  )
}
