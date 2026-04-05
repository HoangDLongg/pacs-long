/* ================================================
   T007 — src/api/auth.js
   Auth API — US1 scope only
   Functions: loginApi, getMeApi
   ================================================ */

const BASE_URL = '/api'

/**
 * Đăng nhập — POST /api/auth/login
 * Backend nhận JSON { username, password }
 * @returns {{ token: string, user: object }}
 */
export async function loginApi(username, password) {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = data.detail
    // detail can be string or array of objects
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
 * @returns {{ id: number, username: string, full_name: string, role: string }}
 */
export async function getMeApi(token) {
  const response = await fetch(`${BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Token không hợp lệ hoặc đã hết hạn')
  }

  return response.json()
}
