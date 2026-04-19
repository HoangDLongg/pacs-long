/* ================================================
   T008 — src/hooks/useAuth.js (Improved Version)
   Auth hook — quản lý JWT + Refresh Token logic
   ================================================ */

import { useState, useEffect, useCallback, useRef } from 'react'
import { loginApi, getMeApi, refreshTokenApi } from '@/api/auth'  // ← thêm refreshTokenApi

const ACCESS_TOKEN_KEY = 'pacs_token'           // spec FR-003
const REFRESH_TOKEN_KEY = 'pacs_refresh_token'
const USER_KEY = 'pacs_user'

/**
 * useAuth — JWT authentication state management (Secure version)
 *
 * Returns: (giữ nguyên như cũ)
 *  - user, token, loading, error, login, logout, isAuthenticated
 */
export function useAuth() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)   // access token
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refreshPromiseRef = useRef(null)   // tránh gọi refresh nhiều lần cùng lúc

  // Hàm kiểm tra token hết hạn (dùng jwt-decode hoặc tự parse)
  const isTokenExpired = useCallback((jwt) => {
    if (!jwt) return true
    try {
      const payload = JSON.parse(atob(jwt.split('.')[1]))
      return payload.exp * 1000 < Date.now() + 60_000 // hết hạn trong 1 phút tới
    } catch {
      return true
    }
  }, [])

  // Khởi tạo auth khi app load
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(ACCESS_TOKEN_KEY)
      const storedUser = localStorage.getItem(USER_KEY)

      if (!storedToken || isTokenExpired(storedToken)) {
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setLoading(false)
        return
      }

      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser))
          setToken(storedToken)
          setLoading(false)
          return
        } catch {
          localStorage.removeItem(USER_KEY)
        }
      }

      // Verify token với server nếu cần
      try {
        const me = await getMeApi(storedToken)
        setUser(me)
        setToken(storedToken)
        localStorage.setItem(USER_KEY, JSON.stringify(me))
      } catch {
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [isTokenExpired])

  // Hàm refresh token (silent)
  const refreshAccessToken = useCallback(async () => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current
    }

    refreshPromiseRef.current = (async () => {
      try {
        const result = await refreshTokenApi()   // backend trả { token: newAccessToken, user? }
        const newToken = result.token || result.access_token

        if (!newToken) throw new Error('Refresh thất bại')

        const userInfo = result.user || await getMeApi(newToken)

        localStorage.setItem(ACCESS_TOKEN_KEY, newToken)
        localStorage.setItem(USER_KEY, JSON.stringify(userInfo))

        setToken(newToken)
        setUser(userInfo)

        return newToken
      } catch (err) {
        logout()   // refresh fail → buộc logout
        throw err
      } finally {
        refreshPromiseRef.current = null
      }
    })()

    return refreshPromiseRef.current
  }, [])

  // Login (giữ nguyên logic, chỉ đổi key)
  const login = useCallback(async (username, password) => {
    setError(null)
    setLoading(true)

    try {
      const result = await loginApi(username, password)
      const jwt = result.token || result.access_token
      const me = result.user

      if (!jwt) throw new Error('Không nhận được token')

      const userInfo = me || await getMeApi(jwt)

      localStorage.setItem(ACCESS_TOKEN_KEY, jwt)
      localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
      // Lưu refresh token nếu có
      if (result.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, result.refresh_token)
      }

      setToken(jwt)
      setUser(userInfo)
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // Logout
  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
    setError(null)
  }, [])

  return {
    user,
    token,                    // access token
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user && !!token,
    refreshAccessToken,       // export thêm nếu cần gọi thủ công
  }
}