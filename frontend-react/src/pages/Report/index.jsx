/* ================================================
   Placeholder — src/pages/Report/index.jsx
   Bao cao chan doan — edit/readonly theo role
   ================================================ */

import { useParams } from 'react-router-dom'

export default function ReportPage() {
  const { id } = useParams()

  return (
    <div className="page-header">
      <h2 className="page-header__title">Bao cao chan doan</h2>
      <p className="page-header__subtitle">Study ID: {id} — dang phat trien</p>
    </div>
  )
}
