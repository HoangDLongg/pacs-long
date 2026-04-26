/* ================================================
   src/api/search.js
   Search API wrappers — UC12, UC13, UC14
   Endpoints: GET /api/search/keyword, POST /api/search
   ================================================ */

const BASE_URL = '/api'
const TOKEN_KEY = 'pacs_token'

function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

/**
 * UC12: Keyword search
 * GET /api/search/keyword?q=...&limit=10
 */
export async function searchKeyword(query, limit = 10) {
  const params = new URLSearchParams({ q: query, limit })
  const response = await fetch(`${BASE_URL}/search/keyword?${params}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw new Error('Lỗi tìm kiếm từ khóa')
  return response.json()
}

/**
 * UC13 + UC14: Dense / Hybrid search
 * POST /api/search
 */
export async function searchReports(query, method = 'hybrid', topK = 10) {
  const response = await fetch(`${BASE_URL}/search`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      query,
      method,
      top_k: topK,
      dense_weight: 0.6,
      sparse_weight: 0.4,
    }),
  })
  if (!response.ok) throw new Error('Lỗi tìm kiếm')
  return response.json()
}

/**
 * UC15: NL2SQL / Hỏi đáp tự nhiên
 * POST /api/search/ask
 */
export async function askQuestion(question) {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ question }),
  })
  if (!response.ok) throw new Error('Lỗi hỏi đáp')
  return response.json()
}
