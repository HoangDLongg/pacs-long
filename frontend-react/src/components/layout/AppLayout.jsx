/* ================================================
   F03 — src/components/layout/AppLayout.jsx
   Layout wrapper: Sidebar + Topbar + <Outlet/>
   Dùng cho tất cả authenticated pages
   ================================================ */

import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar  from './Topbar'

export default function AppLayout() {
  return (
    <div className="app-layout fade-in">
      <Sidebar />
      <Topbar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
