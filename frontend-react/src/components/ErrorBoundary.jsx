/**
 * ErrorBoundary — Bắt lỗi React toàn cục
 * Khi component con crash → hiện UI lỗi thay vì trắng màn hình
 */
import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error('[ErrorBoundary]', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: '2rem',
          color: 'var(--text-primary, #e0e0e0)',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}>
          <div style={{
            background: 'var(--surface-card, #1e1e2e)',
            border: '1px solid var(--border, #333)',
            borderRadius: '12px',
            padding: '2.5rem',
            maxWidth: '500px',
            width: '100%',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
            <h2 style={{ margin: '0 0 0.5rem', fontSize: '1.25rem', color: 'var(--danger, #ef4444)' }}>
              Đã xảy ra lỗi
            </h2>
            <p style={{ color: 'var(--text-secondary, #999)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              {this.state.error?.message || 'Ứng dụng gặp sự cố không mong muốn.'}
            </p>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <button
                onClick={this.handleReset}
                style={{
                  padding: '0.6rem 1.5rem',
                  borderRadius: '8px',
                  border: 'none',
                  background: 'var(--primary, #3b82f6)',
                  color: '#fff',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                }}
              >
                Thử lại
              </button>
              <button
                onClick={() => window.location.href = '/worklist'}
                style={{
                  padding: '0.6rem 1.5rem',
                  borderRadius: '8px',
                  border: '1px solid var(--border, #555)',
                  background: 'transparent',
                  color: 'var(--text-primary, #e0e0e0)',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                }}
              >
                Về trang chính
              </button>
            </div>

            {/* Dev mode: hiện stack trace */}
            {import.meta.env.DEV && this.state.errorInfo && (
              <details style={{ marginTop: '1.5rem', textAlign: 'left' }}>
                <summary style={{ cursor: 'pointer', color: 'var(--text-secondary, #999)', fontSize: '0.8rem' }}>
                  Chi tiết lỗi (dev only)
                </summary>
                <pre style={{
                  marginTop: '0.5rem',
                  padding: '1rem',
                  background: '#0d0d1a',
                  borderRadius: '6px',
                  fontSize: '0.7rem',
                  overflow: 'auto',
                  maxHeight: '200px',
                  color: '#ff6b6b',
                }}>
                  {this.state.error?.stack}
                  {'\n\n'}
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
