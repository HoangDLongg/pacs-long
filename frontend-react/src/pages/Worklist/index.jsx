/* ================================================
   F15 — src/pages/Worklist/index.jsx
   Worklist page — Dashboard + Table + Filter
   Gọi API: GET /api/worklist, GET /api/worklist/stats/dashboard
   ================================================ */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getWorklist, getStats } from '@/api/worklist'
import { uploadDicom } from '@/api/dicom'
import StatCard    from '@/components/shared/StatCard'
import StatusBadge from '@/components/shared/StatusBadge'
import FilterBar   from '@/components/shared/FilterBar'
import UploadZone  from '@/components/shared/UploadZone'

const PAGE_SIZE = 15

export default function WorklistPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // State
  const [studies, setStudies]     = useState([])
  const [stats, setStats]         = useState(null)
  const [filters, setFilters]     = useState({})
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const [page, setPage]           = useState(1)
  const [showUpload, setShowUpload] = useState(false)
  const [compareIds, setCompareIds] = useState([])  // multi-select cho compare

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [worklistRes, statsRes] = await Promise.all([
        getWorklist(filters),
        getStats(),
      ])
      setStudies(worklistRes.studies || [])
      setStats(statsRes)
    } catch (err) {
      setError(err.message)
      console.error('Worklist fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Filter change
  function handleFilterChange(key, value) {
    setFilters(prev => ({ ...prev, [key]: value || undefined }))
    setPage(1)
  }

  // Upload handler
  async function handleUpload(file) {
    const result = await uploadDicom(file)
    // Refresh data sau upload
    fetchData()
    return result
  }

  // Pagination
  const totalPages = Math.ceil(studies.length / PAGE_SIZE)
  const pagedStudies = studies.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  // Format date
  function formatDate(dateStr) {
    if (!dateStr) return '—'
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('vi-VN')
    } catch {
      return dateStr
    }
  }

  const canUpload = user?.role === 'admin' || user?.role === 'technician'

  // Toggle compare selection
  function toggleCompare(studyId) {
    setCompareIds(prev => {
      if (prev.includes(studyId)) return prev.filter(id => id !== studyId)
      if (prev.length >= 2) return [prev[1], studyId]  // giữ 2 cái mới nhất
      return [...prev, studyId]
    })
  }

  return (
    <div className="fade-in">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h2 className="page-header__title">Worklist</h2>
          <p className="page-header__subtitle">Danh sách ca chụp — {studies.length} ca</p>
        </div>
        {compareIds.length === 2 && (
          <button
            className="btn btn--primary"
            onClick={() => navigate(`/compare/${compareIds[0]}/${compareIds[1]}`)}
            style={{ marginLeft: 'auto' }}
          >
            So sánh 2 ca
          </button>
        )}
        {compareIds.length === 1 && (
          <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
            Chọn thêm 1 ca để so sánh...
          </span>
        )}
      </div>

      {/* Stats row */}
      {stats && (
        <div className="stats-row">
          <StatCard value={stats.total}    label="Tổng ca"    variant="primary" />
          <StatCard value={stats.pending}  label="Chờ đọc"    variant="warning" />
          <StatCard value={stats.reported} label="Đã đọc"     variant="info" />
          <StatCard value={stats.verified} label="Đã duyệt"   variant="purple" />
        </div>
      )}

      {/* Filter bar */}
      <FilterBar
        filters={filters}
        onChange={handleFilterChange}
        total={studies.length}
      />

      {/* Upload zone — toggle */}
      {canUpload && (
        <div>
          <button
            className="btn btn-primary"
            onClick={() => setShowUpload(!showUpload)}
            id="btn-toggle-upload"
          >
            {showUpload ? 'Đóng' : 'Upload DICOM'}
          </button>
          {showUpload && (
            <div className="fade-in" style={{ marginTop: 'var(--space-4)' }}>
              <UploadZone onUpload={handleUpload} />
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="alert alert--error">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
          <div className="spinner" />
        </div>
      )}

      {/* Data table */}
      {!loading && studies.length > 0 && (
        <>
          <table className="data-table" id="worklist-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th>#</th>
                <th>Tên bệnh nhân</th>
                <th>Mã BN</th>
                <th>Ngày chụp</th>
                <th>Modality</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {pagedStudies.map((study, idx) => (
                <tr key={study.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={compareIds.includes(study.id)}
                      onChange={() => toggleCompare(study.id)}
                      title="Chọn để so sánh"
                    />
                  </td>
                  <td>{(page - 1) * PAGE_SIZE + idx + 1}</td>
                  <td>{study.patient_name || '—'}</td>
                  <td>{study.patient_code || '—'}</td>
                  <td>{formatDate(study.study_date)}</td>
                  <td>{study.modality || '—'}</td>
                  <td><StatusBadge status={study.status} /></td>
                  <td>
                    <div className="data-table__actions">
                      <button
                        className="data-table__btn data-table__btn--primary"
                        onClick={() => navigate(`/viewer/${study.id}`)}
                      >
                        Xem
                      </button>
                      <button
                        className="data-table__btn"
                        onClick={() => navigate(`/report/${study.id}`)}
                      >
                        Báo cáo
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="pagination__btn"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                ←
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                <button
                  key={p}
                  className={`pagination__btn${p === page ? ' pagination__btn--active' : ''}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
              <button
                className="pagination__btn"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                →
              </button>
              <span className="pagination__info">
                Trang {page}/{totalPages}
              </span>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!loading && studies.length === 0 && !error && (
        <div className="alert alert--warning">
          Không có ca chụp nào phù hợp với bộ lọc
        </div>
      )}
    </div>
  )
}
