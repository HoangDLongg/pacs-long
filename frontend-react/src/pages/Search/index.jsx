/* ================================================
   src/pages/Search/index.jsx
   Unified Smart Search — 1 ô search duy nhất
   Backend tự route: NL2SQL / RAG / Keyword
   Tách rõ: Keyword results (tên BN) vs RAG results
   ================================================ */

import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchKeyword, askQuestion } from '@/api/search'
import './search.css'

const INTENT_LABELS = {
  PATIENT_LOOKUP: { icon: '👤', label: 'Tìm bệnh nhân', color: 'hsl(140, 60%, 55%)' },
  STRUCTURED: { icon: '📊', label: 'Truy vấn SQL', color: 'var(--color-primary)' },
  SEMANTIC:   { icon: '🧠', label: 'Tìm kiếm ngữ nghĩa', color: 'hsl(280, 70%, 60%)' },
  HYBRID:     { icon: '⚡', label: 'Hybrid (SQL + RAG)', color: 'hsl(45, 90%, 55%)' },
}

export default function SearchPage() {
  const navigate = useNavigate()
  const [query,    setQuery]    = useState('')
  const [kwResults, setKwResults] = useState([])   // keyword results (exact match)
  const [ragResults, setRagResults] = useState([])  // RAG/semantic results
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [searched, setSearched] = useState(false)
  const [compareIds, setCompareIds] = useState([])
  const [askResult, setAskResult] = useState(null)
  const [detectedMethod, setDetectedMethod] = useState(null)

  // Unified search — gọi ask (auto-route) + keyword (tên bệnh nhân) song song
  const handleSearch = useCallback(async (e) => {
    e?.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setSearched(true)
    setCompareIds([])
    setAskResult(null)
    setDetectedMethod(null)
    setKwResults([])
    setRagResults([])

    try {
      // Gọi song song: ask (smart route) + keyword (bắt tên bệnh nhân)
      const [askData, kwData] = await Promise.allSettled([
        askQuestion(query),
        searchKeyword(query),
      ])

      // Process ask result
      const ask = askData.status === 'fulfilled' ? askData.value : null
      const kw  = kwData.status === 'fulfilled' ? kwData.value : null

      if (ask) {
        setAskResult(ask)
        setDetectedMethod(ask.intent)
      }

      // Keyword results (exact name / text match)
      const kwList = kw?.results || []
      setKwResults(kwList)

      // RAG results (semantic) — deduplicate với keyword results
      const ragList = ask?.rag_results || []
      const kwIds = new Set(kwList.map(r => r.report_id))
      const uniqueRag = ragList.filter(r => !kwIds.has(r.report_id))
      setRagResults(uniqueRag)
    } catch (err) {
      setError(err.message)
      setKwResults([])
      setRagResults([])
    } finally {
      setLoading(false)
    }
  }, [query])

  // Toggle compare selection (max 2)
  function toggleCompare(studyId) {
    setCompareIds(prev => {
      if (prev.includes(studyId)) return prev.filter(id => id !== studyId)
      if (prev.length >= 2) return [prev[1], studyId]
      return [...prev, studyId]
    })
  }

  // Navigate to compare page
  function goCompare() {
    if (compareIds.length === 2) {
      navigate(`/compare/${compareIds[0]}/${compareIds[1]}`)
    }
  }

  // Score bar color
  function getScoreColor(score) {
    if (score >= 0.85) return 'var(--color-success)'
    if (score >= 0.70) return 'var(--color-warning)'
    return 'var(--color-danger)'
  }

  // Format date
  function formatDate(dateStr) {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleDateString('vi-VN')
    } catch {
      return dateStr
    }
  }

  const intentInfo = INTENT_LABELS[detectedMethod]
  const totalResults = kwResults.length + ragResults.length + (askResult?.data?.length || 0)

  // Render a result card
  function renderCard(r, idx, globalIdx) {
    return (
      <div
        key={r.report_id || idx}
        className={`search-card ${compareIds.includes(r.study_id) ? 'search-card--selected' : ''}`}
      >
        {/* Rank badge */}
        <div className="search-card__rank">#{globalIdx + 1}</div>

        {/* Main content */}
        <div className="search-card__body">
          <div className="search-card__top">
            <h3 className="search-card__patient">{r.patient_name || 'N/A'}</h3>
            <span className="search-card__modality">{r.modality}</span>
            {r.method && (
              <span className={`search-card__method search-card__method--${r.method}`}>
                {r.method === 'keyword' ? '🔤' : r.method === 'dense' ? '🧠' : '⚡'} {r.method}
              </span>
            )}
            <span className="search-card__date">{formatDate(r.study_date)}</span>
          </div>

          {/* Score bar */}
          {r.score !== undefined && r.method !== 'keyword' && (
            <div className="search-card__score-section">
              <div className="search-card__score-bar">
                <div
                  className="search-card__score-fill"
                  style={{
                    width: `${Math.round(r.score * 100)}%`,
                    backgroundColor: getScoreColor(r.score),
                  }}
                />
              </div>
              <span className="search-card__score-text">
                {Math.round(r.score * 100)}%
              </span>
              {r.dense_score !== undefined && (
                <span className="search-card__score-detail">
                  (dense: {Math.round(r.dense_score * 100)}% · sparse: {Math.round((r.sparse_score || 0) * 100)}%)
                </span>
              )}
            </div>
          )}

          {/* Findings + Conclusion */}
          <div className="search-card__content">
            {r.findings && (
              <p className="search-card__findings">
                <strong>Mô tả:</strong> {r.findings.slice(0, 200)}{r.findings.length > 200 ? '...' : ''}
              </p>
            )}
            {r.conclusion && (
              <p className="search-card__conclusion">
                <strong>Kết luận:</strong> {r.conclusion.slice(0, 150)}{r.conclusion.length > 150 ? '...' : ''}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="search-card__actions">
          <button
            className="btn btn--outline btn--sm"
            onClick={() => navigate(`/viewer/${r.study_id}`)}
            title="Xem DICOM"
          >
            🖼️ Xem
          </button>
          <button
            className="btn btn--outline btn--sm"
            onClick={() => navigate(`/report/${r.study_id}`)}
            title="Xem báo cáo"
          >
            📄 Báo cáo
          </button>
          <button
            className={`btn btn--sm ${compareIds.includes(r.study_id) ? 'btn--primary' : 'btn--ghost'}`}
            onClick={() => toggleCompare(r.study_id)}
            title="Chọn để so sánh"
          >
            {compareIds.includes(r.study_id) ? '✓ Đã chọn' : '⊞ So sánh'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="search-page">
      {/* Header */}
      <div className="page-header">
        <h2 className="page-header__title">🔍 Tìm kiếm thông minh</h2>
        <p className="page-header__subtitle">
          Nhập bất kỳ nội dung gì — tên bệnh nhân, triệu chứng, câu hỏi thống kê — hệ thống tự nhận diện
        </p>
      </div>

      {/* Search Form */}
      <form className="search-form" onSubmit={handleSearch}>
        <div className="search-input-group">
          <div className="search-input-wrapper">
            <span className="search-input-icon">🔍</span>
            <input
              id="search-query-input"
              type="text"
              className="search-input search-input--unified"
              placeholder='VD: "Nguyễn Văn A", "tổn thương phổi dạng nốt", "bao nhiêu ca CT hôm nay?"'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
          </div>
          <button
            type="submit"
            className="btn btn--primary search-btn"
            disabled={loading || !query.trim()}
          >
            {loading ? '⏳ Đang xử lý...' : '🔍 Tìm kiếm'}
          </button>
        </div>

        {/* Hint chips */}
        <div className="search-hints">
          <span className="search-hint" onClick={() => setQuery('bao nhiêu ca CT hôm nay?')}>📊 Thống kê</span>
          <span className="search-hint" onClick={() => setQuery('tổn thương phổi dạng nốt')}>🧠 Nội dung y khoa</span>
          <span className="search-hint" onClick={() => setQuery('ca nào chưa đọc?')}>📋 Tra cứu trạng thái</span>
          <span className="search-hint" onClick={() => setQuery('thống kê theo modality')}>📈 Phân tích</span>
        </div>
      </form>

      {/* Compare bar */}
      {compareIds.length > 0 && (
        <div className="search-compare-bar">
          <span>Đã chọn {compareIds.length}/2 để so sánh</span>
          <button
            className="btn btn--primary"
            onClick={goCompare}
            disabled={compareIds.length !== 2}
          >
            So sánh side-by-side →
          </button>
          <button
            className="btn btn--ghost"
            onClick={() => setCompareIds([])}
          >
            Bỏ chọn
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="alert alert--error">❌ {error}</div>
      )}

      {/* NL2SQL Answer Panel — hiện khi có data từ SQL */}
      {askResult && askResult.data?.length > 0 && (
        <div className="ask-panel">
          <div className="ask-panel__header">
            <span className="ask-panel__intent">
              {askResult.intent === 'STRUCTURED' ? '📊 Kết quả thống kê' :
               askResult.intent === 'HYBRID' ? '⚡ Kết quả phân tích' :
               '🧠 Tìm kiếm ngữ nghĩa'}
            </span>
          </div>

          <div className="ask-panel__answer">{askResult.answer}</div>

          {/* Data table */}
          {askResult.data && askResult.data.length > 0 && (
            <div className="ask-panel__table-wrap">
              <table className="ask-panel__table">
                <thead>
                  <tr>
                    {Object.keys(askResult.data[0]).map(key => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {askResult.data.map((row, i) => (
                    <tr key={i}>
                      {Object.values(row).map((val, j) => (
                        <td key={j}>{val != null ? String(val) : '—'}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="search-loading">
          <div className="search-loading__spinner" />
          <span>AI đang phân tích và tìm kiếm...</span>
        </div>
      )}

      {/* ===== KEYWORD RESULTS SECTION (exact match — tên, mã BN, nội dung) ===== */}
      {searched && !loading && (
        <>
          {kwResults.length > 0 ? (
            <div className="search-section">
              <div className="search-section__header search-section__header--keyword">
                <span className="search-section__icon">🎯</span>
                <span className="search-section__title">
                  Khớp chính xác — {kwResults.length} kết quả
                </span>
                <span className="search-section__desc">Tên bệnh nhân, mã BN, nội dung báo cáo</span>
              </div>
              <div className="search-results">
                {kwResults.map((r, idx) => renderCard(r, idx, idx))}
              </div>
            </div>
          ) : (
            <div className="search-no-exact">
              <span>🔤 Không tìm thấy kết quả khớp chính xác với "<strong>{query}</strong>"</span>
            </div>
          )}

          {/* ===== RAG RESULTS SECTION (semantic/AI) ===== */}
          {ragResults.length > 0 && (
            <div className="search-section">
              <div className="search-section__header search-section__header--rag">
                <span className="search-section__icon">🧠</span>
                <span className="search-section__title">
                  AI gợi ý — {ragResults.length} kết quả tương tự
                </span>
                <span className="search-section__desc">Tìm kiếm ngữ nghĩa bằng AI</span>
                {intentInfo && (
                  <span className="search-detected-badge" style={{ borderColor: intentInfo.color, color: intentInfo.color }}>
                    {intentInfo.icon} {intentInfo.label}
                    {askResult?.confidence != null && ` (${Math.round(askResult.confidence * 100)}%)`}
                  </span>
                )}
              </div>
              <div className="search-results">
                {ragResults.map((r, idx) => renderCard(r, idx, kwResults.length + idx))}
              </div>
            </div>
          )}

          {/* No results at all */}
          {kwResults.length === 0 && ragResults.length === 0 && !askResult?.data?.length && (
            <div className="search-empty">
              <div className="search-empty__icon">🔍</div>
              <p>Không tìm thấy kết quả nào cho "<strong>{query}</strong>"</p>
              <p className="search-empty__hint">Thử tìm kiếm bằng từ khóa khác hoặc mô tả triệu chứng</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
