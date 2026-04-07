/* ================================================
   F06 — src/components/shared/StatusBadge.jsx
   Badge: PENDING (vàng), REPORTED (xanh), VERIFIED (tím)
   ================================================ */

/**
 * StatusBadge — hiển thị trạng thái ca chụp
 *
 * @param {string} status - 'PENDING' | 'REPORTED' | 'VERIFIED'
 */
export default function StatusBadge({ status }) {
  const s = (status || 'PENDING').toUpperCase()

  const labels = {
    PENDING:  'Cho doc',
    REPORTED: 'Da doc',
    VERIFIED: 'Da duyet',
  }

  return (
    <span
      className={`status-badge status-badge--${s.toLowerCase()}`}
      id={`status-${s.toLowerCase()}`}
    >
      {labels[s] || s}
    </span>
  )
}
