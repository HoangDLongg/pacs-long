/* ================================================
   F13 — src/api/report.js
   Report API wrappers
   Endpoints: GET /api/report/{study_id}, POST /api/report,
              PUT /api/report/{id}
   ================================================ */

const BASE_URL = '/api'
const TOKEN_KEY = 'pacs_token'

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
 * GET /api/report/{study_id} — Xem báo cáo
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
 * POST /api/report — Tạo báo cáo mới
 * @param {object} data - { study_id, findings, conclusion, recommendation? }
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
 * PUT /api/report/{id} — Cập nhật báo cáo
 * @param {number} reportId
 * @param {object} data - { study_id, findings, conclusion, recommendation? }
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
