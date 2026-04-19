/* ================================================
   T007 — src/api/auth.js
   Auth API — login, me, refresh
   Spec FR-003: JWT stored as 'pacs_token'
   ================================================ */

const BASE_URL = '/api'

/**
 * Đăng nhập — POST /api/auth/login
 * @returns {{ access_token, refresh_token, token_type, user }}
 */
export async function loginApi(username, password) {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = data.detail
    const msg = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map(d => d.msg).join(', ')
        : 'Sai tài khoản hoặc mật khẩu'
    throw new Error(msg)
  }

  return response.json()
}

/**
 * Lấy thông tin user hiện tại — GET /api/auth/me
 * @param {string} token - access token
 * @returns {{ id, username, full_name, role, is_active }}
 */
export async function getMeApi(token) {
  const response = await fetch(`${BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw new Error('Token không hợp lệ hoặc đã hết hạn')
  return response.json()
}

/**
 * Làm mới Access Token — POST /api/auth/refresh
 * @returns {{ access_token, refresh_token, token_type, user }}
 */
export async function refreshTokenApi() {
  const refreshToken = localStorage.getItem('pacs_refresh_token')
  if (!refreshToken) throw new Error('Không có refresh token')

  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  if (!response.ok) throw new Error('Refresh token hết hạn hoặc không hợp lệ')
  return response.json()
}
