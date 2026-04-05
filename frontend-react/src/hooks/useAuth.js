/* ================================================
   T008 — src/hooks/useAuth.js
   Auth hook — quản lý JWT state
   ================================================ */

import { useState, useEffect, useCallback } from 'react'
import { loginApi, getMeApi } from '@/api/auth'

const TOKEN_KEY = 'pacs_token'
const USER_KEY  = 'pacs_user'

/**
 * useAuth — JWT authentication state management
 *
 * Returns:
 *  - user: { id, username, full_name, role } | null
 *  - token: string | null
 *  - loading: boolean
 *  - error: string | null
 *  - login(username, password): Promise<void>
 *  - logout(): void
 *  - isAuthenticated: boolean
 */
export function useAuth() {
  const [user,    setUser]    = useState(null)
  const [token,   setToken]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  // Khởi động: đọc token từ localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY)
    const storedUser  = localStorage.getItem(USER_KEY)

    if (!storedToken) {
      setLoading(false)
      return
    }

    // Có token — thử parse user cache
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser))
        setToken(storedToken)
        setLoading(false)
        return
      } catch {
        // Cache bị lỗi, xoá đi
        localStorage.removeItem(USER_KEY)
      }
    }

    // Không có user cache — verify token với server
    getMeApi(storedToken)
      .then((me) => {
        setUser(me)
        setToken(storedToken)
        localStorage.setItem(USER_KEY, JSON.stringify(me))
      })
      .catch(() => {
        // Token hết hạn — xoá
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
      })
      .finally(() => setLoading(false))
  }, [])

  /**
   * Đăng nhập — gọi API, lưu JWT, fetch user info
   */
  const login = useCallback(async (username, password) => {
    setError(null)
    setLoading(true)

    try {
      // 1. Lấy token
      const { access_token } = await loginApi(username, password)

      // 2. Lấy thông tin user
      const me = await getMeApi(access_token)

      // 3. Lưu vào localStorage
      localStorage.setItem(TOKEN_KEY, access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(me))

      // 4. Cập nhật state
      setToken(access_token)
      setUser(me)
    } catch (err) {
      setError(err.message)
      throw err // để LoginForm catch và hiện lỗi
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Đăng xuất — xoá token + user khỏi localStorage
   */
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
    setError(null)
  }, [])

  return {
    user,
    token,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user && !!token,
  }
}
