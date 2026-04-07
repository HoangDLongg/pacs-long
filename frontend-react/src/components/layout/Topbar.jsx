/* ================================================
   F02 — src/components/layout/Topbar.jsx
   Top bar: page title + user role badge
   ================================================ */

import { useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

/**
 * Map route → page title
 */
const PAGE_TITLES = {
  '/worklist': 'Worklist',
  '/viewer': 'DICOM Viewer',
  '/report': 'Bao cao chan doan',
  '/search': 'Tim kiem',
  '/my-studies': 'Ca cua toi',
  '/admin': 'Quan tri he thong',
}

function getPageTitle(pathname) {
  // Exact match
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname]
  // Prefix match (e.g. /viewer/123)
  for (const [path, title] of Object.entries(PAGE_TITLES)) {
    if (pathname.startsWith(path)) return title
  }
  return 'PACS++'
}

export default function Topbar() {
  const { user } = useAuth()
  const location = useLocation()

  const pageTitle = getPageTitle(location.pathname)
  const role = user?.role || 'doctor'

  return (
    <header className="topbar">

      <div className="topbar__left">
        <span className="topbar__breadcrumb">PACS++ /</span>
        <h1 className="topbar__page-title">{pageTitle}</h1>
      </div>

      <div className="topbar__right">
        <span className={`role-badge role-badge--${role}`}>
          {role}
        </span>
      </div>

    </header>
  )
}
