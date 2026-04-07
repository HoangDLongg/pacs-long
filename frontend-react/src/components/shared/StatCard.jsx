/* ================================================
   F07 — src/components/shared/StatCard.jsx
   Card thống kê: số + label (no icons)
   ================================================ */

/**
 * StatCard — hiển thị 1 số thống kê
 *
 * @param {number} value     - Con số
 * @param {string} label     - Mô tả
 * @param {string} variant   - 'primary' | 'warning' | 'info' | 'purple'
 */
export default function StatCard({ value, label, variant = 'primary' }) {
  return (
    <div className="stat-card">
      <div>
        <div className="stat-card__value">{value ?? '—'}</div>
        <div className="stat-card__label">{label}</div>
      </div>
    </div>
  )
}
