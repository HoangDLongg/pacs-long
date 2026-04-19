/* ================================================
   src/pages/Report/index.jsx
   Bao cao chan doan
   Spec US5: Doctor edit, Tech/Patient readonly, xuat PDF
   Route: /report/:id  (id = study DB id)
   ================================================ */

import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getReport, createReport, updateReport, exportPdf } from '@/api/report'
import { getStudyDetail } from '@/api/worklist'

export default function ReportPage() {
  const { id }     = useParams()          // study_id
  const navigate   = useNavigate()
  const { user }   = useAuth()

  const studyId    = parseInt(id, 10)
  const canEdit    = ['doctor', 'admin'].includes(user?.role)   // spec role matrix
  const isPatient  = user?.role === 'patient'

  // ---- State ----
  const [study,       setStudy]     = useState(null)
  const [report,      setReport]    = useState(null)    // null = chưa có báo cáo
  const [reportId,    setReportId]  = useState(null)
  const [loadErr,     setLoadErr]   = useState(null)
  const [loading,     setLoading]   = useState(true)

  // Form fields
  const [findings,        setFindings]        = useState('')
  const [conclusion,      setConclusion]       = useState('')
  const [recommendation,  setRecommendation]   = useState('')

  const [saving,    setSaving]    = useState(false)
  const [saveMsg,   setSaveMsg]   = useState(null)   // { type: 'success'|'error', text }
  const [exporting, setExporting] = useState(false)

  const [editMode,  setEditMode]  = useState(false)   // bắt đầu read, bấm Edit mới cho edit

  // ---- Load data ----
  useEffect(() => {
    if (!studyId) return
    setLoading(true)
    setLoadErr(null)

    Promise.all([
      getStudyDetail(studyId).catch(() => null),
      getReport(studyId),
    ]).then(([studyData, reportData]) => {
      setStudy(studyData)

      const r = reportData?.report
      if (r) {
        setReport(r)
        setReportId(r.id)
        setFindings(r.findings || '')
        setConclusion(r.conclusion || '')
        setRecommendation(r.recommendation || '')
        setEditMode(false)   // có report → xem trước
      } else {
        // Chưa có báo cáo → nếu doctor/admin thì bật edit luôn
        setReport(null)
        setEditMode(canEdit)
      }
    }).catch((err) => {
      setLoadErr(err.message)
    }).finally(() => setLoading(false))
  }, [studyId])

  // ---- Save (create or update) ----
  const handleSave = useCallback(async () => {
    if (!findings.trim() || !conclusion.trim()) {
      setSaveMsg({ type: 'error', text: 'Ket qua va Ket luan khong duoc de trong' })
      return
    }

    setSaving(true)
    setSaveMsg(null)

    const payload = {
      study_id:       studyId,
      findings:       findings.trim(),
      conclusion:     conclusion.trim(),
      recommendation: recommendation.trim() || null,
    }

    try {
      if (reportId) {
        // Spec UC09: update
        await updateReport(reportId, payload)
        setSaveMsg({ type: 'success', text: 'Cap nhat bao cao thanh cong' })
      } else {
        // Spec UC08: create
        const result = await createReport(payload)
        setReportId(result.id)
        setSaveMsg({ type: 'success', text: 'Tao bao cao thanh cong. Trang thai → REPORTED' })
      }
      setEditMode(false)
      // Reload report để có doctor_name, timestamp mới
      const fresh = await getReport(studyId)
      if (fresh?.report) setReport(fresh.report)
    } catch (err) {
      setSaveMsg({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }, [studyId, reportId, findings, conclusion, recommendation])

  // ---- Export PDF (Spec UC11, FR-010) ----
  const handleExportPdf = useCallback(async () => {
    setExporting(true)
    try {
      await exportPdf(studyId, study?.patient_name)
    } catch (err) {
      setSaveMsg({ type: 'error', text: `Xuat PDF that bai: ${err.message}` })
    } finally {
      setExporting(false)
    }
  }, [studyId, study])

  // ---- Status badge ----
  const statusClass = {
    PENDING:  'badge badge--warning',
    REPORTED: 'badge badge--info',
    VERIFIED: 'badge badge--success',
  }

  // ====================== RENDER ======================
  if (loading) {
    return (
      <div className="page-content">
        <div className="viewer-state">
          <div className="spinner" />
          <p>Dang tai bao cao...</p>
        </div>
      </div>
    )
  }

  if (loadErr) {
    return (
      <div className="page-content">
        <div className="viewer-state viewer-state--error">
          <p>{loadErr}</p>
          <button className="btn btn--ghost" onClick={() => navigate(-1)}>Quay lai</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-content">

      {/* ---- Page header ---- */}
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Bao cao chan doan</h1>
          {study && (
            <p className="page-header__subtitle">
              {study.patient_name} &bull; {study.patient_code} &bull; {study.study_date} &bull; {study.modality}
            </p>
          )}
        </div>

        <div className="page-header__actions">
          {/* Status badge */}
          {study?.status && (
            <span className={statusClass[study.status] || 'badge'}>
              {study.status}
            </span>
          )}

          {/* Xuất PDF — hiện khi đã có report (spec UC11) */}
          {report && (
            <button
              className="btn btn--ghost btn--sm"
              onClick={handleExportPdf}
              disabled={exporting}
            >
              {exporting ? 'Dang xuat...' : 'Xuat PDF'}
            </button>
          )}

          {/* Edit button — doctor/admin khi đang xem */}
          {canEdit && report && !editMode && (
            <button
              className="btn btn--primary btn--sm"
              onClick={() => setEditMode(true)}
            >
              Chinh sua
            </button>
          )}

          <button className="btn btn--ghost btn--sm" onClick={() => navigate(-1)}>
            Quay lai
          </button>
        </div>
      </div>

      {/* ---- Thông tin ca chụp ---- */}
      {study && (
        <div className="card report-study-card">
          <div className="report-study-grid">
            <div><span className="report-label">Benh nhan</span><span className="report-value">{study.patient_name}</span></div>
            <div><span className="report-label">Ma BN</span><span className="report-value">{study.patient_code}</span></div>
            <div><span className="report-label">Gioi tinh</span><span className="report-value">{study.gender === 'M' ? 'Nam' : study.gender === 'F' ? 'Nu' : '—'}</span></div>
            <div><span className="report-label">Ngay sinh</span><span className="report-value">{study.birth_date || '—'}</span></div>
            <div><span className="report-label">Ngay chup</span><span className="report-value">{study.study_date}</span></div>
            <div><span className="report-label">Modality</span><span className="report-value">{study.modality}</span></div>
            {study.description && (
              <div className="report-study-grid__full">
                <span className="report-label">Mo ta</span>
                <span className="report-value">{study.description}</span>
              </div>
            )}
          </div>

          {/* Link xem Viewer */}
          <div style={{ marginTop: 'var(--space-3)' }}>
            <button
              className="btn btn--ghost btn--sm"
              onClick={() => navigate(`/viewer/${studyId}`)}
            >
              Xem anh DICOM
            </button>
          </div>
        </div>
      )}

      {/* ---- Save Message ---- */}
      {saveMsg && (
        <div className={`alert ${saveMsg.type === 'success' ? 'alert--success' : 'alert--error'}`}>
          {saveMsg.text}
          <button
            className="alert__close"
            onClick={() => setSaveMsg(null)}
          >x</button>
        </div>
      )}

      {/* ---- Form bao cao ---- */}
      <div className="card report-form-card">
        {report && !editMode ? (
          /* ==================== VIEW MODE ==================== */
          <div className="report-view">
            <div className="report-view__meta">
              <span>Bac si: <strong>{report.doctor_name}</strong></span>
              <span>Ngay bao cao: <strong>{String(report.report_date || '').slice(0, 10)}</strong></span>
            </div>

            <div className="report-section">
              <h3 className="report-section__title">Ket qua</h3>
              <p className="report-section__content">{report.findings}</p>
            </div>

            <div className="report-section">
              <h3 className="report-section__title">Ket luan</h3>
              <p className="report-section__content">{report.conclusion}</p>
            </div>

            {report.recommendation && (
              <div className="report-section">
                <h3 className="report-section__title">De nghi</h3>
                <p className="report-section__content">{report.recommendation}</p>
              </div>
            )}
          </div>

        ) : canEdit ? (
          /* ==================== EDIT MODE (Doctor/Admin) ==================== */
          <div className="report-edit">
            {!report && (
              <p className="report-edit__notice">
                Ca nay chua co bao cao. Dien vao form de tao moi.
              </p>
            )}

            <div className="form-group">
              <label className="form-label" htmlFor="findings">
                Ket qua <span className="form-required">*</span>
              </label>
              <textarea
                id="findings"
                className="form-textarea"
                rows={6}
                value={findings}
                onChange={(e) => setFindings(e.target.value)}
                placeholder="Mo ta chi tiet ket qua hinh anh..."
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="conclusion">
                Ket luan <span className="form-required">*</span>
              </label>
              <textarea
                id="conclusion"
                className="form-textarea"
                rows={4}
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
                placeholder="Ket luan chan doan..."
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="recommendation">
                De nghi <span className="form-label--optional">(tuy chon)</span>
              </label>
              <textarea
                id="recommendation"
                className="form-textarea"
                rows={3}
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value)}
                placeholder="Huong dieu tri, tai kham..."
              />
            </div>

            <div className="report-edit__actions">
              {report && (
                <button
                  className="btn btn--ghost"
                  onClick={() => {
                    setEditMode(false)
                    setFindings(report.findings || '')
                    setConclusion(report.conclusion || '')
                    setRecommendation(report.recommendation || '')
                    setSaveMsg(null)
                  }}
                >
                  Huy
                </button>
              )}
              <button
                className="btn btn--primary"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Dang luu...' : reportId ? 'Cap nhat' : 'Tao bao cao'}
              </button>
            </div>
          </div>

        ) : (
          /* ==================== NO REPORT (Tech/Patient) ==================== */
          <div className="viewer-state">
            {/* Spec US5 acceptance 3: tech thấy readonly */}
            {/* Spec US8 acceptance 5: patient thấy "Đang chờ kết quả" */}
            <p className="viewer-empty-text">
              {isPatient ? 'Dang cho ket qua' : 'Chua co bao cao'}
            </p>
            <p className="viewer-empty-sub">
              {isPatient
                ? 'Bac si dang xu ly. Vui long kiem tra lai sau.'
                : 'Bac si chua viet bao cao cho ca chup nay.'}
            </p>
          </div>
        )}
      </div>

    </div>
  )
}
