/* ================================================
   src/pages/Admin/index.jsx
   Admin Panel — Quản lý users + thông tin hệ thống
   Route: /admin — role=admin only (RoleGuard trong App.jsx)
   Spec: UC16 (xem users), UC17 (system info)
   ================================================ */

import { useState, useEffect } from 'react'

const TOKEN_KEY = 'pacs_token'

function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return { Authorization: `Bearer ${token}` }
}

// ---- Role badge colors ----
const ROLE_MAP = {
  admin:       { label: 'Admin',       cls: 'badge badge--danger' },
  doctor:      { label: 'Bác sĩ',     cls: 'badge badge--info' },
  technician:  { label: 'Kỹ thuật',   cls: 'badge badge--warning' },
  patient:     { label: 'Bệnh nhân',  cls: 'badge badge--success' },
}

export default function AdminPage() {
  const [users, setUsers]       = useState([])
  const [system, setSystem]     = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/admin/users', { headers: authHeaders() }).then(r => r.json()),
      fetch('/api/admin/system', { headers: authHeaders() }).then(r => r.json()),
    ])
      .then(([userData, sysData]) => {
        setUsers(userData.users || [])
        setSystem(sysData)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="viewer-state">
        <div className="spinner" />
        <p>Đang tải...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert alert--error">
        <span>{error}</span>
      </div>
    )
  }

  return (
    <div className="page-content">

      {/* ---- Header ---- */}
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Quản trị hệ thống</h1>
          <p className="page-header__subtitle">Quản lý tài khoản và thông tin hệ thống</p>
        </div>
      </div>

      {/* ---- System Stats ---- */}
      {system && (
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-card__value">{system.users}</div>
            <div className="stat-card__label">Tài khoản</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__value">{system.patients}</div>
            <div className="stat-card__label">Bệnh nhân</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__value">{system.studies}</div>
            <div className="stat-card__label">Ca chụp</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__value">{system.reports}</div>
            <div className="stat-card__label">Báo cáo</div>
          </div>
        </div>
      )}

      {/* ---- Role breakdown ---- */}
      {system?.roles && (
        <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
          <h3 style={{ marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            Phân bổ vai trò
          </h3>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            <span>Admin: <strong>{system.roles.admins}</strong></span>
            <span>Bác sĩ: <strong>{system.roles.doctors}</strong></span>
            <span>Kỹ thuật: <strong>{system.roles.technicians}</strong></span>
            <span>Bệnh nhân: <strong>{system.roles.patients}</strong></span>
          </div>
        </div>
      )}

      {/* ---- Users Table ---- */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border)' }}>
          <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>
            Danh sách tài khoản ({users.length})
          </h3>
        </div>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Họ tên</th>
                <th>Vai trò</th>
                <th>Trạng thái</th>
                <th>Ngày tạo</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => {
                const role = ROLE_MAP[u.role] || { label: u.role, cls: 'badge' }
                return (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td><strong>{u.username}</strong></td>
                    <td>{u.full_name || '—'}</td>
                    <td><span className={role.cls}>{role.label}</span></td>
                    <td>
                      <span className={u.is_active ? 'badge badge--success' : 'badge badge--danger'}>
                        {u.is_active ? 'Hoạt động' : 'Khóa'}
                      </span>
                    </td>
                    <td>{u.created_at ? new Date(u.created_at).toLocaleDateString('vi-VN') : '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ---- Default accounts info ---- */}
      <div className="card" style={{ marginTop: '1.5rem', padding: '1.25rem' }}>
        <h3 style={{ marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
          Tài khoản mặc định
        </h3>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Password</th>
                <th>Vai trò</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>admin</td><td>admin123</td><td>Quản trị viên</td></tr>
              <tr><td>dr.nam</td><td>doctor123</td><td>Bác sĩ</td></tr>
              <tr><td>dr.lan</td><td>doctor123</td><td>Bác sĩ</td></tr>
              <tr><td>tech.hung</td><td>tech123</td><td>Kỹ thuật viên</td></tr>
              <tr><td>tech.mai</td><td>tech123</td><td>Kỹ thuật viên</td></tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
