/* ================================================
   T014 — src/pages/Placeholder.jsx
   Trang tạm sau khi login thành công (US2 sẽ thay = Worklist)
   ================================================ */

import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

/**
 * PlaceholderPage
 * Hiển thị khi đã login nhưng US2 (Worklist) chưa code
 * Dùng để verify redirect flow của US1
 */
export default function PlaceholderPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-base)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-xl)',
        padding: 'var(--space-10)',
        maxWidth: 480,
        width: '100%',
        textAlign: 'center',
      }}>

        {/* Logo nhỏ */}
        <img
          src="/logo.svg"
          alt="PACS++"
          width={64}
          height={64}
          style={{
            objectFit: 'contain',
            marginBottom: 'var(--space-5)',
          }}
        />

        <h2 style={{
          fontSize: 'var(--text-xl)',
          fontWeight: 'var(--font-bold)',
          color: 'var(--text-primary)',
          marginBottom: 'var(--space-2)',
        }}>
          US1 — Đăng nhập thành công
        </h2>

        <p style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--text-muted)',
          marginBottom: 'var(--space-6)',
          lineHeight: 1.7,
        }}>
          Xin chào, <strong style={{ color: 'var(--text-secondary)' }}>
            {user?.full_name || user?.username}
          </strong>.<br />
          Worklist (US2) đang được phát triển.
        </p>

        {/* User info */}
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
          textAlign: 'left',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-3)',
        }}>
          {[
            { label: 'Username', value: user?.username },
            { label: 'Vai trò',  value: user?.role },
            { label: 'Họ tên',   value: user?.full_name },
          ].map(item => (
            <div key={item.label}>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 2 }}>
                {item.label}
              </p>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)', fontWeight: 'var(--font-medium)' }}>
                {item.value || '—'}
              </p>
            </div>
          ))}
        </div>

        <button
          id="btn-logout-placeholder"
          type="button"
          className="btn btn-secondary btn-block"
          onClick={handleLogout}
        >
          Đăng xuất
        </button>

      </div>
    </div>
  )
}
