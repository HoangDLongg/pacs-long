/* ================================================
   src/api/patient.js
   Patient Portal API wrappers
   Spec US8: FR-009 — patient chỉ xem ca của mình
   ================================================ */

const BASE_URL = '/api'
const TOKEN_KEY = 'pacs_token'   // spec FR-003

function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return { Authorization: `Bearer ${token}` }
}

function parseError(data) {
  const detail = data.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(d => d.msg).join(', ')
  return 'Khong the lay du lieu'
}

/**
 * GET /api/worklist/my-studies — Danh sách ca chụp của patient đang login
 * Spec US8 acceptance 2: chỉ trả ca của patient này (FR-009 backend enforced)
 * @returns {{ studies: Array, total: number, message?: string }}
 */
export async function getMyStudies() {
  const response = await fetch(`${BASE_URL}/worklist/my-studies`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}

/**
 * GET /api/report/{study_id} — Lấy báo cáo của 1 ca chụp
 * Dùng trong My Studies để check status report
 * Spec US8 acceptance 4+5: có report → hiện kết quả, chưa → "Đang chờ"
 * @param {number} studyId
 * @returns {{ report: object | null }}
 */
export async function getMyReport(studyId) {
  const response = await fetch(`${BASE_URL}/report/${studyId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}
