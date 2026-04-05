/* ================================================
   BrandingPanel — Phần trái trang Login
   Ảnh bệnh viện full + overlay gradient + logo + text
   ================================================ */

export default function BrandingPanel() {
  return (
    <div style={{
      flex: '0 0 55%',
      position: 'relative',
      overflow: 'hidden',
      minHeight: '100vh',
    }}>

      {/* Ảnh bệnh viện full cover */}
      <img
        src="/benhvien.jpg"
        alt="Bệnh viện"
        style={{
          position: 'absolute',
          top: 0, left: 0,
          width: '100%', height: '100%',
          objectFit: 'cover',
        }}
      />

      {/* Overlay gradient tối — để text đọc được */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0,
        width: '100%', height: '100%',
        background: 'linear-gradient(135deg, rgba(10,15,26,0.85) 0%, rgba(10,15,26,0.6) 50%, rgba(10,15,26,0.85) 100%)',
      }} />

      {/* Content trên overlay */}
      <div style={{
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        padding: '48px',
      }}>

        {/* Logo */}
        <img
          src="/logo.svg"
          alt="PACS++ Logo"
          width={120}
          height={120}
          style={{
            objectFit: 'contain',
            marginBottom: '24px',
            filter: 'brightness(1.2)',
          }}
        />

        {/* System name */}
        <h1 style={{
          fontSize: '42px',
          fontWeight: 800,
          color: '#ffffff',
          letterSpacing: '-0.03em',
          marginBottom: '4px',
        }}>
          PACS++
        </h1>

        <p style={{
          fontSize: '13px',
          fontWeight: 600,
          color: '#4CAF50',
          textTransform: 'uppercase',
          letterSpacing: '0.2em',
          marginBottom: '32px',
        }}>
          Medical Imaging System
        </p>

        {/* Divider */}
        <div style={{
          width: 60,
          height: 2,
          background: 'linear-gradient(90deg, transparent, #4CAF50, transparent)',
          marginBottom: '32px',
        }} />

        {/* Description */}
        <p style={{
          fontSize: '15px',
          color: 'rgba(255,255,255,0.7)',
          textAlign: 'center',
          lineHeight: 1.8,
          maxWidth: 400,
          marginBottom: '48px',
        }}>
          He thong luu tru va truyen tai hinh anh y te
          tich hop tri tue nhan tao — ho tro bac si
          chan doan nhanh chong, chinh xac.
        </p>

        {/* Feature badges */}
        <div style={{
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}>
          {['DICOM Viewer', 'RAG Search', 'AI Diagnosis', 'PDF Report'].map(tag => (
            <span
              key={tag}
              style={{
                padding: '6px 16px',
                borderRadius: '20px',
                fontSize: '11px',
                fontWeight: 600,
                letterSpacing: '0.05em',
                color: 'rgba(255,255,255,0.8)',
                background: 'rgba(76,175,80,0.15)',
                border: '1px solid rgba(76,175,80,0.3)',
              }}
            >
              {tag}
            </span>
          ))}
        </div>

        {/* Version */}
        <p style={{
          position: 'absolute',
          bottom: '20px',
          fontSize: '11px',
          color: 'rgba(255,255,255,0.3)',
        }}>
          v2.0 — PACS++ System Hospitals
        </p>

      </div>
    </div>
  )
}
