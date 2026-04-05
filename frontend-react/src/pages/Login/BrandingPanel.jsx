/* ================================================
   T009 — src/pages/Login/BrandingPanel.jsx
   Phần trái của trang Login: logo + tên + mô tả
   ================================================ */

/**
 * BrandingPanel
 * Hiển thị logo thật và thông tin hệ thống PACS++
 * Không dùng icon/emoji — clean hospital style
 */
export default function BrandingPanel() {
  return (
    <div style={{
      flex: '0 0 420px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-12)',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border)',
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* Subtle background gradient */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0,
        width: '100%', height: '100%',
        background:
          'radial-gradient(ellipse at 50% 0%, rgba(45,125,50,0.06) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Logo */}
      <img
        src="/logo.svg"
        alt="PACS++ System Hospitals"
        width={200}
        height={200}
        style={{
          objectFit: 'contain',
          marginBottom: 'var(--space-6)',
          mixBlendMode: 'multiply',
        }}
      />

      {/* System name */}
      <h1 style={{
        fontSize: 'var(--text-2xl)',
        fontWeight: 'var(--font-bold)',
        color: 'var(--text-primary)',
        letterSpacing: '-0.02em',
        marginBottom: 'var(--space-1)',
        textAlign: 'center',
      }}>
        PACS++
      </h1>

      <p style={{
        fontSize: 'var(--text-sm)',
        fontWeight: 'var(--font-semibold)',
        color: 'var(--color-brand-light)',
        textTransform: 'uppercase',
        letterSpacing: '0.12em',
        marginBottom: 'var(--space-8)',
      }}>
        System Hospitals
      </p>

      {/* Divider */}
      <div style={{
        width: 48,
        height: 2,
        background: 'var(--accent)',
        borderRadius: 'var(--radius-full)',
        marginBottom: 'var(--space-8)',
        opacity: 0.6,
      }} />

      {/* Description */}
      <p style={{
        fontSize: 'var(--text-sm)',
        color: 'var(--text-muted)',
        textAlign: 'center',
        lineHeight: 1.8,
        maxWidth: 300,
      }}>
        Hệ thống lưu trữ và truyền tải hình ảnh y tế tích hợp trí tuệ nhân tạo — hỗ trợ bác sĩ chẩn đoán nhanh chóng, chính xác.
      </p>

      {/* Version tag */}
      <p style={{
        position: 'absolute',
        bottom: 'var(--space-4)',
        fontSize: 'var(--text-xs)',
        color: 'var(--text-disabled)',
      }}>
        v1.0 — Sprint 1
      </p>

    </div>
  )
}
