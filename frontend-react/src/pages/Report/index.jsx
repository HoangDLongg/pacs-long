/* ================================================
   src/pages/Report/index.jsx
   Báo cáo chẩn đoán
   Spec US5: Doctor edit, Tech/Patient readonly, xuất PDF
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
      setSaveMsg({ type: 'error', text: 'Kết quả và Kết luận không được để trống' })
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
        setSaveMsg({ type: 'success', text: 'Cập nhật báo cáo thành công' })
      } else {
        // Spec UC08: create
        const result = await createReport(payload)
        setReportId(result.id)
        setSaveMsg({ type: 'success', text: 'Tạo báo cáo thành công. Trạng thái → REPORTED' })
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
      setSaveMsg({ type: 'error', text: `Xuất PDF thất bại: ${err.message}` })
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
          <p>Đang tải báo cáo...</p>
        </div>
      </div>
    )
  }

  if (loadErr) {
    return (
      <div className="page-content">
        <div className="viewer-state viewer-state--error">
          <p>{loadErr}</p>
          <button className="btn btn--ghost" onClick={() => navigate(-1)}>Quay lại</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-content">

      {/* ---- Page header ---- */}
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Báo cáo chẩn đoán</h1>
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
              {exporting ? 'Đang xuất...' : 'Xuất PDF'}
            </button>
          )}

          {/* Edit button — doctor/admin khi đang xem */}
          {canEdit && report && !editMode && (
            <button
              className="btn btn--primary btn--sm"
              onClick={() => setEditMode(true)}
            >
              Chỉnh sửa
            </button>
          )}

          <button className="btn btn--ghost btn--sm" onClick={() => navigate(-1)}>
            Quay lại
          </button>
        </div>
      </div>

      {/* ---- Thông tin ca chụp ---- */}
      {study && (
        <div className="card report-study-card">
          <div className="report-study-grid">
            <div><span className="report-label">Bệnh nhân</span><span className="report-value">{study.patient_name}</span></div>
            <div><span className="report-label">Mã BN</span><span className="report-value">{study.patient_code}</span></div>
            <div><span className="report-label">Giới tính</span><span className="report-value">{study.gender === 'M' ? 'Nam' : study.gender === 'F' ? 'Nữ' : '—'}</span></div>
            <div><span className="report-label">Ngày sinh</span><span className="report-value">{study.birth_date || '—'}</span></div>
            <div><span className="report-label">Ngày chụp</span><span className="report-value">{study.study_date}</span></div>
            <div><span className="report-label">Modality</span><span className="report-value">{study.modality}</span></div>
            {study.description && (
              <div className="report-study-grid__full">
                <span className="report-label">Mô tả</span>
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
              Xem ảnh DICOM
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
              <span>Bác sĩ: <strong>{report.doctor_name}</strong></span>
              <span>Ngày báo cáo: <strong>{String(report.report_date || '').slice(0, 10)}</strong></span>
            </div>

            <div className="report-section">
              <h3 className="report-section__title">Kết quả</h3>
              <p className="report-section__content">{report.findings}</p>
            </div>

            <div className="report-section">
              <h3 className="report-section__title">Kết luận</h3>
              <p className="report-section__content">{report.conclusion}</p>
            </div>

            {report.recommendation && (
              <div className="report-section">
                <h3 className="report-section__title">Đề nghị</h3>
                <p className="report-section__content">{report.recommendation}</p>
              </div>
            )}
          </div>

        ) : canEdit ? (
          /* ==================== EDIT MODE (Doctor/Admin) ==================== */
          <div className="report-edit">
            {!report && (
              <p className="report-edit__notice">
                Ca này chưa có báo cáo. Điền vào form để tạo mới.
              </p>
            )}

            <div className="form-group">
              <label className="form-label" htmlFor="findings">
                Kết quả <span className="form-required">*</span>
              </label>
              <textarea
                id="findings"
                className="form-textarea"
                rows={6}
                value={findings}
                onChange={(e) => setFindings(e.target.value)}
                placeholder="Mô tả chi tiết kết quả hình ảnh..."
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="conclusion">
                Kết luận <span className="form-required">*</span>
              </label>
              <textarea
                id="conclusion"
                className="form-textarea"
                rows={4}
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
                placeholder="Kết luận chẩn đoán..."
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="recommendation">
                Đề nghị <span className="form-label--optional">(tùy chọn)</span>
              </label>
              <textarea
                id="recommendation"
                className="form-textarea"
                rows={3}
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value)}
                placeholder="Hướng điều trị, tái khám..."
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
                  Hủy
                </button>
              )}
              <button
                className="btn btn--primary"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Đang lưu...' : reportId ? 'Cập nhật' : 'Tạo báo cáo'}
              </button>
            </div>
          </div>

        ) : (
          /* ==================== NO REPORT (Tech/Patient) ==================== */
          <div className="viewer-state">
            {/* Spec US5 acceptance 3: tech thấy readonly */}
            {/* Spec US8 acceptance 5: patient thấy "Đang chờ kết quả" */}
            <p className="viewer-empty-text">
              {isPatient ? 'Đang chờ kết quả' : 'Chưa có báo cáo'}
            </p>
            <p className="viewer-empty-sub">
              {isPatient
                ? 'Bác sĩ đang xử lý. Vui lòng kiểm tra lại sau.'
                : 'Bác sĩ chưa viết báo cáo cho ca chụp này.'}
            </p>
          </div>
        )}
      </div>

    </div>
  )
}
