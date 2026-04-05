/* ================================================
   T007 — src/api/auth.js
   Auth API — US1 scope only
   Functions: loginApi, getMeApi
   ================================================ */

const BASE_URL = '/api'

/**
 * Đăng nhập — POST /api/auth/login
 * Backend nhận OAuth2 form (application/x-www-form-urlencoded)
 * @returns {{ access_token: string, token_type: string }}
 */
export async function loginApi(username, password) {
  const body = new URLSearchParams({
    username,
    password,
    grant_type: 'password',
  })

  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: body.toString(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || 'Sai tài khoản hoặc mật khẩu')
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
