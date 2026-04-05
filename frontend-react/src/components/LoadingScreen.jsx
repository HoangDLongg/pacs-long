/* ================================================
   src/components/LoadingScreen.jsx
   Màn hình loading toàn trang — dùng khi check auth
   ================================================ */

/**
 * LoadingScreen
 * Hiển thị khi đang kiểm tra trạng thái đăng nhập
 */
export default function LoadingScreen() {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-base)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 'var(--space-4)',
    }}>
      <img
        src="/logo.svg"
        alt="PACS++"
        width={56}
        height={56}
        style={{
          objectFit: 'contain',
          opacity: 0.85,
        }}
      />
      <span className="spinner" style={{ width: 28, height: 28 }} />
      <p style={{
        fontSize: 'var(--text-sm)',
        color: 'var(--text-muted)',
      }}>
        Đang tải...
      </p>
    </div>
  )
}
