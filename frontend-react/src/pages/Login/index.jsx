/* ================================================
   T011 — src/pages/Login/index.jsx
   Login page — layout 2 cột: BrandingPanel + LoginForm
   ================================================ */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import BrandingPanel from './BrandingPanel'
import LoginForm     from './LoginForm'

/**
 * LoginPage
 * - Nếu đã đăng nhập → redirect /worklist
 * - Layout 2 cột: trái là brand, phải là form
 */
export default function LoginPage() {
  const { login, loading, error, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  // Đã login rồi → vào Worklist
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/worklist', { replace: true })
    }
  }, [isAuthenticated, navigate])

  async function handleLogin(username, password) {
    try {
      await login(username, password)
      navigate('/worklist', { replace: true })
    } catch {
      // Error đã được set trong useAuth, LoginForm sẽ hiển thị
    }
  }

  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        minHeight: '100vh',
        background: 'var(--bg-base)',
      }}
    >
      <BrandingPanel />
      <LoginForm
        onSubmit={handleLogin}
        loading={loading}
        error={error}
      />
    </div>
  )
}
