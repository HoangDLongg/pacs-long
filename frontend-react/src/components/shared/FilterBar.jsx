/* ================================================
   F08 — src/components/shared/FilterBar.jsx
   Filter: date, modality dropdown, status, search text
   Matches backend GET /api/worklist?date=&modality=&status=
   ================================================ */

/**
 * FilterBar — bộ lọc cho Worklist
 *
 * @param {object}   filters   - { date, modality, status }
 * @param {function} onChange  - (key, value) => void
 * @param {number}   total     - Tổng số kết quả
 */
export default function FilterBar({ filters = {}, onChange, total }) {
  function handleChange(key) {
    return (e) => onChange(key, e.target.value)
  }

  return (
    <div className="filter-bar" id="filter-bar">
      {/* Date */}
      <input
        type="date"
        className="filter-bar__input"
        value={filters.date || ''}
        onChange={handleChange('date')}
        id="filter-date"
      />

      {/* Modality */}
      <select
        className="filter-bar__select"
        value={filters.modality || ''}
        onChange={handleChange('modality')}
        id="filter-modality"
      >
        <option value="">Tat ca modality</option>
        <option value="CR">CR — X-Quang</option>
        <option value="CT">CT — Cat lop</option>
        <option value="MR">MR — Cong huong tu</option>
        <option value="US">US — Sieu am</option>
        <option value="DX">DX — X-Quang so</option>
        <option value="MG">MG — Nhu anh</option>
      </select>

      {/* Status */}
      <select
        className="filter-bar__select"
        value={filters.status || ''}
        onChange={handleChange('status')}
        id="filter-status"
      >
        <option value="">Tat ca trang thai</option>
        <option value="PENDING">Cho doc</option>
        <option value="REPORTED">Da doc</option>
        <option value="VERIFIED">Da duyet</option>
      </select>

      <div className="filter-bar__spacer" />

      {/* Count */}
      {total !== undefined && (
        <span className="filter-bar__count">
          {total} ket qua
        </span>
      )}
    </div>
  )
}
