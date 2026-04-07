/* ================================================
   F11 — src/api/worklist.js
   Worklist API wrappers
   Endpoints: GET /api/worklist, GET /api/worklist/stats/dashboard,
              GET /api/worklist/{id}
   ================================================ */

const BASE_URL = '/api'
const TOKEN_KEY = 'pacs_token'

function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return {
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
 * GET /api/worklist — Danh sách ca chụp + filter
 * @param {object} filters - { date?, modality?, status? }
 * @returns {{ studies: Array, total: number }}
 */
export async function getWorklist(filters = {}) {
  const params = new URLSearchParams()
  if (filters.date)     params.set('date', filters.date)
  if (filters.modality) params.set('modality', filters.modality)
  if (filters.status)   params.set('status', filters.status)

  const qs = params.toString()
  const url = `${BASE_URL}/worklist${qs ? '?' + qs : ''}`

  const response = await fetch(url, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}

/**
 * GET /api/worklist/stats/dashboard — 4 con số thống kê
 * @returns {{ total, pending, reported, verified }}
 */
export async function getStats() {
  const response = await fetch(`${BASE_URL}/worklist/stats/dashboard`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}

/**
 * GET /api/worklist/{id} — Chi tiết 1 ca chụp
 * @param {number} studyId
 * @returns {object} study detail
 */
export async function getStudyDetail(studyId) {
  const response = await fetch(`${BASE_URL}/worklist/${studyId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}
