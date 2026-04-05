/* ================================================
   T010 — src/pages/Login/LoginForm.jsx
   Form đăng nhập: input, button, error, test accounts
   ================================================ */

import { useState } from 'react'

/**
 * Danh sách tài khoản test nhanh
 * Không dùng emoji — text label rõ ràng
 */
const TEST_ACCOUNTS = [
  { username: 'admin',     password: 'admin123',  label: 'Admin'          },
  { username: 'dr.nam',    password: 'doctor123', label: 'Bác sĩ'         },
  { username: 'tech.hung', password: 'tech123',   label: 'Kỹ thuật viên'  },
]

/**
 * LoginForm
 * Props:
 *  - onSubmit(username, password): async function
 *  - loading: boolean
 *  - error: string | null
 */
export default function LoginForm({ onSubmit, loading, error }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim() || !password) return
    onSubmit(username.trim(), password)
  }

  function fillTestAccount(account) {
    setUsername(account.username)
    setPassword(account.password)
  }

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-12)',
    }}>
      <div style={{ width: '100%', maxWidth: 380 }}>

        {/* Heading */}
        <div style={{ marginBottom: 'var(--space-8)' }}>
          <h2 style={{
            fontSize: 'var(--text-xl)',
            fontWeight: 'var(--font-bold)',
            color: 'var(--text-primary)',
            marginBottom: 'var(--space-1)',
          }}>
            Đăng nhập hệ thống
          </h2>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
            Nhập thông tin tài khoản để tiếp tục
          </p>
        </div>

        {/* Form */}
        <form id="login-form" onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>

            {/* Username */}
            <div className="form-group">
              <label
                className="form-label form-label--required"
                htmlFor="input-username"
              >
                Tài khoản
              </label>
              <input
                id="input-username"
                type="text"
                className={`form-input${error ? ' form-input--error' : ''}`}
                placeholder="Nhập username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
                disabled={loading}
              />
            </div>

            {/* Password */}
            <div className="form-group">
              <label
                className="form-label form-label--required"
                htmlFor="input-password"
              >
                Mật khẩu
              </label>
              <input
                id="input-password"
                type="password"
                className={`form-input${error ? ' form-input--error' : ''}`}
                placeholder="Nhập mật khẩu"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                disabled={loading}
              />
            </div>

            {/* Error message */}
            {error && (
              <div id="login-error" className="alert alert--error">
                {error}
              </div>
            )}

            {/* Submit button */}
            <button
              id="btn-login-submit"
              type="submit"
              className="btn btn-primary btn-block btn-lg"
              disabled={loading || !username.trim() || !password}
              style={{ marginTop: 'var(--space-2)' }}
            >
              {loading ? (
                <>
                  <span className="spinner" style={{ width: 16, height: 16 }} />
                  Đang đăng nhập...
                </>
              ) : (
                'Đăng nhập'
              )}
            </button>

          </div>
        </form>

        {/* Divider */}
        <div className="divider" style={{ margin: 'var(--space-6) 0' }} />

        {/* Test accounts */}
        <div>
          <p style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: 'var(--space-3)',
          }}>
            Tài khoản test nhanh
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {TEST_ACCOUNTS.map((account) => (
              <button
                key={account.username}
                id={`btn-test-${account.username}`}
                type="button"
                className="btn btn-secondary"
                onClick={() => fillTestAccount(account)}
                disabled={loading}
                style={{
                  justifyContent: 'space-between',
                  padding: 'var(--space-2) var(--space-4)',
                }}
              >
                <span style={{
                  fontFamily: 'monospace',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--accent)',
                }}>
                  {account.username}
                </span>
                <span style={{
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-muted)',
                  background: 'var(--bg-elevated)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                }}>
                  {account.label}
                </span>
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
