/* ================================================
   F14 — src/api/patient.js
   Patient API wrappers
   Endpoint: GET /api/my-studies (cần thêm backend endpoint)
   ================================================ */

const BASE_URL = '/api'
const TOKEN_KEY = 'pacs_token'

function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return {
    Authorization: `Bearer ${token}`,
  }
}

/**
 * GET /api/my-studies — Lấy danh sách ca chụp của patient đang login
 * ⚠️ Backend endpoint chưa có — sẽ thêm sau
 * @returns {{ studies: Array, total: number }}
 */
export async function getMyStudies() {
  const response = await fetch(`${BASE_URL}/my-studies`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = data.detail
    const msg = typeof detail === 'string' ? detail : 'Khong the lay du lieu'
    throw new Error(msg)
  }

  return response.json()
}
