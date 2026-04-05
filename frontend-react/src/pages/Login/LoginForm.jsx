/* ================================================
   LoginForm — compact form inside floating card
   ================================================ */

import { useState } from 'react'

const TEST_ACCOUNTS = [
  { username: 'admin',     password: 'admin123',  label: 'Admin'          },
  { username: 'dr.nam',    password: 'doctor123', label: 'Bac si'         },
  { username: 'tech.hung', password: 'tech123',   label: 'Ky thuat vien' },
]

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
    <div>
      {/* Form */}
      <form id="login-form" onSubmit={handleSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Username */}
          <div>
            <label style={{
              display: 'block',
              fontSize: 12,
              fontWeight: 600,
              color: 'rgba(255,255,255,0.6)',
              marginBottom: 6,
            }}>
              Tai khoan
            </label>
            <input
              id="input-username"
              type="text"
              placeholder="Nhap username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              disabled={loading}
              style={{
                width: '100%',
                padding: '10px 14px',
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 10,
                color: '#e0e6ed',
                fontSize: 14,
                outline: 'none',
                transition: 'all 0.2s',
                boxSizing: 'border-box',
              }}
              onFocus={e => {
                e.target.style.borderColor = '#4CAF50'
                e.target.style.boxShadow = '0 0 0 3px rgba(76,175,80,0.12)'
              }}
              onBlur={e => {
                e.target.style.borderColor = 'rgba(255,255,255,0.12)'
                e.target.style.boxShadow = 'none'
              }}
            />
          </div>

          {/* Password */}
          <div>
            <label style={{
              display: 'block',
              fontSize: 12,
              fontWeight: 600,
              color: 'rgba(255,255,255,0.6)',
              marginBottom: 6,
            }}>
              Mat khau
            </label>
            <input
              id="input-password"
              type="password"
              placeholder="Nhap mat khau"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={loading}
              style={{
                width: '100%',
                padding: '10px 14px',
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 10,
                color: '#e0e6ed',
                fontSize: 14,
                outline: 'none',
                transition: 'all 0.2s',
                boxSizing: 'border-box',
              }}
              onFocus={e => {
                e.target.style.borderColor = '#4CAF50'
                e.target.style.boxShadow = '0 0 0 3px rgba(76,175,80,0.12)'
              }}
              onBlur={e => {
                e.target.style.borderColor = 'rgba(255,255,255,0.12)'
                e.target.style.boxShadow = 'none'
              }}
            />
          </div>

          {/* Error */}
          {error && (
            <div style={{
              padding: '8px 12px',
              borderRadius: 8,
              background: 'rgba(239,83,80,0.12)',
              border: '1px solid rgba(239,83,80,0.25)',
              color: '#ef5350',
              fontSize: 13,
            }}>
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            id="btn-login-submit"
            type="submit"
            disabled={loading || !username.trim() || !password}
            style={{
              width: '100%',
              padding: '12px',
              border: 'none',
              borderRadius: 10,
              fontSize: 14,
              fontWeight: 700,
              cursor: 'pointer',
              color: '#fff',
              background: loading ? '#333' : 'linear-gradient(135deg, #4CAF50, #2E7D32)',
              transition: 'all 0.2s',
              marginTop: 4,
              opacity: (!username.trim() || !password) ? 0.5 : 1,
            }}
          >
            {loading ? 'Dang dang nhap...' : 'Dang nhap'}
          </button>

        </div>
      </form>

      {/* Divider */}
      <div style={{
        height: 1,
        background: 'rgba(255,255,255,0.08)',
        margin: '20px 0',
      }} />

      {/* Test accounts */}
      <div>
        <p style={{
          fontSize: 10,
          color: 'rgba(255,255,255,0.35)',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          marginBottom: 8,
        }}>
          Test nhanh
        </p>

        <div style={{ display: 'flex', gap: 6 }}>
          {TEST_ACCOUNTS.map(account => (
            <button
              key={account.username}
              type="button"
              onClick={() => fillTestAccount(account)}
              disabled={loading}
              style={{
                flex: 1,
                padding: '6px 4px',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8,
                background: 'rgba(255,255,255,0.04)',
                color: 'rgba(255,255,255,0.6)',
                fontSize: 11,
                cursor: 'pointer',
                transition: 'all 0.2s',
                textAlign: 'center',
              }}
              onMouseEnter={e => {
                e.target.style.borderColor = 'rgba(76,175,80,0.4)'
                e.target.style.background = 'rgba(76,175,80,0.08)'
              }}
              onMouseLeave={e => {
                e.target.style.borderColor = 'rgba(255,255,255,0.1)'
                e.target.style.background = 'rgba(255,255,255,0.04)'
              }}
            >
              <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#4CAF50', marginBottom: 2 }}>
                {account.username}
              </div>
              <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.35)' }}>
                {account.label}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
