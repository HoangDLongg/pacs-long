/* ================================================
   Placeholder — src/pages/Viewer/index.jsx
   DICOM Viewer — Cornerstone.js (Sprint 3)
   ================================================ */

import { useParams } from 'react-router-dom'

export default function ViewerPage() {
  const { id } = useParams()

  return (
    <div className="page-header">
      <h2 className="page-header__title">DICOM Viewer</h2>
      <p className="page-header__subtitle">Study ID: {id} — Cornerstone.js dang phat trien</p>
    </div>
  )
}
