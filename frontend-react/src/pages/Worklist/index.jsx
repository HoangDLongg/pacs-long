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

  return (
    <div className="fade-in">
      {/* Page header */}
      <div className="page-header">
        <h2 className="page-header__title">Worklist</h2>
        <p className="page-header__subtitle">Danh sach ca chup — {studies.length} ca</p>
      </div>

      {/* Stats row */}
      {stats && (
        <div className="stats-row">
          <StatCard value={stats.total}    label="Tong ca"    variant="primary" />
          <StatCard value={stats.pending}  label="Cho doc"    variant="warning" />
          <StatCard value={stats.reported} label="Da doc"     variant="info" />
          <StatCard value={stats.verified} label="Da duyet"   variant="purple" />
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
            {showUpload ? 'Dong' : 'Upload DICOM'}
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
                <th>#</th>
                <th>Ten benh nhan</th>
                <th>Ma BN</th>
                <th>Ngay chup</th>
                <th>Modality</th>
                <th>Trang thai</th>
                <th>Hanh dong</th>
              </tr>
            </thead>
            <tbody>
              {pagedStudies.map((study, idx) => (
                <tr key={study.id}>
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
                        Bao cao
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
          Khong co ca chup nao phu hop voi bo loc
        </div>
      )}
    </div>
  )
}
