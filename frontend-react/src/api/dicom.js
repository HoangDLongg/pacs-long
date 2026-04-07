/* ================================================
   F12 — src/api/dicom.js
   DICOM API wrappers
   Endpoints: POST /api/dicom/upload, GET /api/dicom/wado
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
 * POST /api/dicom/upload — Upload file .dcm
 * Backend nhận multipart/form-data (UploadFile)
 * @param {File} file - File DICOM từ input hoặc drag-drop
 * @returns {{ status, message, patient_id, study_uid, orthanc_id }}
 */
export async function uploadDicom(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/dicom/upload`, {
    method: 'POST',
    headers: authHeaders(), // Không set Content-Type — browser tự thêm boundary
    body: formData,
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}

/**
 * GET /api/dicom/wado?objectId=xxx — Stream ảnh DICOM
 * @param {string} objectId - Orthanc instance ID
 * @returns {string} URL để fetch trực tiếp (dùng cho Cornerstone.js)
 */
export function getWadoUrl(objectId) {
  const token = localStorage.getItem(TOKEN_KEY)
  return `${BASE_URL}/dicom/wado?objectId=${objectId}&token=${token}`
}
