/* ================================================
   src/api/report.js
   Report API wrappers
   Spec: GET /api/report/{study_id}
         POST /api/report
         PUT  /api/report/{id}
         GET  /api/report/{study_id}/pdf  (UC11, FR-010)
   ================================================ */

const BASE_URL = '/api'
const TOKEN_KEY = 'pacs_token'   // spec FR-003

function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

function parseError(data) {
  const detail = data.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(d => d.msg).join(', ')
  return 'Loi khong xac dinh'
}

/**
 * GET /api/report/{study_id} — Xem báo cáo (all roles)
 * @param {number} studyId
 * @returns {{ report: object | null, message?: string }}
 */
export async function getReport(studyId) {
  const response = await fetch(`${BASE_URL}/report/${studyId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}

/**
 * POST /api/report — Tạo báo cáo mới (Doctor/Admin only)
 * Spec UC08: tạo + status PENDING → REPORTED
 * @param {{ study_id, findings, conclusion, recommendation? }} data
 * @returns {{ id, message }}
 */
export async function createReport(data) {
  const response = await fetch(`${BASE_URL}/report`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(parseError(errData))
  }

  return response.json()
}

/**
 * PUT /api/report/{id} — Cập nhật báo cáo (Doctor/Admin only)
 * Spec UC09
 * @param {number} reportId
 * @param {{ study_id, findings, conclusion, recommendation? }} data
 * @returns {{ message }}
 */
export async function updateReport(reportId, data) {
  const response = await fetch(`${BASE_URL}/report/${reportId}`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(parseError(errData))
  }

  return response.json()
}

/**
 * GET /api/report/{study_id}/pdf — Xuất PDF báo cáo
 * Spec UC11 + FR-010: PDF có header bệnh viện
 * Tự động trigger download trong browser
 * @param {number} studyId
 * @param {string} patientName — dùng để đặt tên file
 */
export async function exportPdf(studyId, patientName = 'bao-cao') {
  const token = localStorage.getItem(TOKEN_KEY)

  const response = await fetch(`${BASE_URL}/report/${studyId}/pdf`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(parseError(errData))
  }

  // Trigger download từ blob
  const blob = await response.blob()
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `report_${studyId}_${patientName.replace(/\s+/g, '_')}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
