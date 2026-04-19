/* ================================================
   src/pages/MyStudies/index.jsx
   Patient Portal — Lịch sử khám & kết quả
   Spec US8: Patient chỉ xem ca của mình (FR-009)
   Route: /my-studies — role=patient only (RoleGuard trong App.jsx)

   Acceptance Scenarios:
   1. Login patient → redirect đây (App.jsx DefaultRedirect)
   2. Chỉ thấy ca của mình (backend enforced)
   3. /worklist → redirect (RoleGuard)
   4. Ca có report → nút "Xem kết quả" → /report/:id
   5. Ca chưa có report → badge "Đang chờ"
   ================================================ */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getMyStudies } from '@/api/patient'

// ---- Badge status theo spec ----
const STATUS_MAP = {
  PENDING:  { label: 'Dang cho',    cls: 'badge badge--warning' },
  REPORTED: { label: 'Co ket qua',  cls: 'badge badge--info'    },
  VERIFIED: { label: 'Da xac nhan', cls: 'badge badge--success'  },
}

// ---- Modality color tag ----
const MODALITY_COLOR = {
  CT: '#38bdf8',
  MR: '#a78bfa',
  CR: '#4ade80',
  DX: '#4ade80',
  US: '#fb923c',
  MG: '#f472b6',
}

export default function MyStudiesPage() {
  const { user }    = useAuth()
  const navigate    = useNavigate()

  const [studies,   setStudies]   = useState([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState(null)

  // --- Load ca chụp ---
  useEffect(() => {
    setLoading(true)
    getMyStudies()
      .then((data) => {
        setStudies(data.studies || [])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  // ====================== RENDER ======================
  return (
    <div className="page-content">

      {/* ---- Header ---- */}
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Ca chup cua toi</h1>
          <p className="page-header__subtitle">
            Lich su kham &amp; ket qua chan doan &bull; {user?.full_name || user?.username}
          </p>
        </div>
        {!loading && !error && (
          <span className="mystudies-count">
            Tong: <strong>{studies.length}</strong> ca
          </span>
        )}
      </div>

      {/* ---- Loading ---- */}
      {loading && (
        <div className="viewer-state">
          <div className="spinner" />
          <p>Dang tai lich su kham...</p>
        </div>
      )}

      {/* ---- Error ---- */}
      {!loading && error && (
        <div className="alert alert--error">
          <span>{error}</span>
        </div>
      )}

      {/* ---- Empty (spec US8 acceptance: chưa có ca nào) ---- */}
      {!loading && !error && studies.length === 0 && (
        <div className="card mystudies-empty">
          <p className="viewer-empty-text">Chua co ca chup nao</p>
          <p className="viewer-empty-sub">
            Lien he KTV de duoc dang ky ca kham
          </p>
        </div>
      )}

      {/* ---- Danh sách ca chụp ---- */}
      {!loading && !error && studies.length > 0 && (
        <div className="mystudies-list">
          {studies.map((study) => {
            const status    = STATUS_MAP[study.status] || { label: study.status, cls: 'badge' }
            const modColor  = MODALITY_COLOR[study.modality] || '#94a3b8'
            const hasReport = study.status !== 'PENDING'

            return (
              <div key={study.id} className="card mystudies-item">

                {/* ---- Top row: modality + date + status ---- */}
                <div className="mystudies-item__header">
                  <span
                    className="mystudies-modality"
                    style={{ color: modColor, borderColor: modColor }}
                  >
                    {study.modality || '—'}
                  </span>

                  <span className="mystudies-date">{study.study_date}</span>

                  <span className={status.cls}>{status.label}</span>
                </div>

                {/* ---- Body: thông tin ---- */}
                <div className="mystudies-item__body">
                  {study.description && (
                    <p className="mystudies-desc">{study.description}</p>
                  )}
                  {study.body_part && (
                    <p className="mystudies-sub">Phan: {study.body_part}</p>
                  )}
                </div>

                {/* ---- Actions ---- */}
                <div className="mystudies-item__actions">
                  {/* Spec US8 ac.4: có report → "Xem kết quả" */}
                  {hasReport ? (
                    <button
                      className="btn btn--primary btn--sm"
                      onClick={() => navigate(`/report/${study.id}`)}
                    >
                      Xem ket qua
                    </button>
                  ) : (
                    /* Spec US8 ac.5: chưa có report */
                    <span className="mystudies-waiting">
                      Dang cho bac si doc phim...
                    </span>
                  )}

                  {/* Xem ảnh DICOM nếu đã có orthanc_id */}
                  {study.orthanc_id && (
                    <button
                      className="btn btn--ghost btn--sm"
                      onClick={() => navigate(`/viewer/${study.id}`)}
                    >
                      Xem anh
                    </button>
                  )}
                </div>

              </div>
            )
          })}
        </div>
      )}

    </div>
  )
}
