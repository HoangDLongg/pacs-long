/* ================================================
   Login Page — Full background + floating card
   ================================================ */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import LoginForm from './LoginForm'

export default function LoginPage() {
  const { login, loading, error, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/worklist', { replace: true })
    }
  }, [isAuthenticated, navigate])

  async function handleLogin(username, password) {
    try {
      await login(username, password)
      navigate('/worklist', { replace: true })
    } catch { }
  }

  return (
    <div style={{
      minHeight: '100vh',
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>

      {/* Background image full screen */}
      <img
        src="/benhvien.jpg"
        alt=""
        style={{
          position: 'fixed',
          top: 0, left: 0,
          width: '100vw', height: '100vh',
          objectFit: 'cover',
          zIndex: 0,
        }}
      />

      {/* Dark overlay */}
      <div style={{
        position: 'fixed',
        top: 0, left: 0,
        width: '100vw', height: '100vh',
        background: 'rgba(10, 15, 26, 0.65)',
        zIndex: 1,
      }} />

      {/* Floating login card */}
      <div style={{
        position: 'relative',
        zIndex: 2,
        width: '100%',
        maxWidth: 420,
        background: 'rgba(17, 24, 39, 0.85)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: 20,
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
        padding: '40px 36px',
      }}>

        {/* Logo + Title */}
        <div style={{ textAlign: 'center' }}>
          <img
            src="/logo.svg"
            alt="PACS++"
            width={270}
            height={270}
            style={{ objectFit: 'contain', filter: 'brightness(1.1)' }}
          />
        </div>

        {/* Login form */}
        <LoginForm
          onSubmit={handleLogin}
          loading={loading}
          error={error}
        />

      </div>

      {/* Bottom version */}
      <p style={{
        position: 'fixed',
        bottom: 16,
        left: '50%',
        transform: 'translateX(-50%)',
        fontSize: 11,
        color: 'rgba(255,255,255,0.25)',
        zIndex: 2,
      }}>
        v2.0 — PACS++ System Hospitals
      </p>
    </div>
  )
}
