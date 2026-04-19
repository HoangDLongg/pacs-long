/* ================================================
   src/api/dicom.js
   DICOM API wrappers
   Spec plan.md: POST /api/dicom/upload, GET /api/dicom/wado,
                 GET /api/dicom/instances/{study_id}
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
  return 'Loi khong xac dinh'
}

/**
 * POST /api/dicom/upload — Upload file .dcm
 * Spec US3: auto-parse metadata, sync DB, upload Orthanc
 * @param {File} file - File DICOM từ input hoặc drag-drop
 * @returns {{ status, message, patient_id, study_uid, orthanc_id }}
 */
export async function uploadDicom(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/dicom/upload`, {
    method: 'POST',
    headers: authHeaders(),   // Không set Content-Type — browser tự thêm boundary
    body: formData,
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}

/**
 * GET /api/dicom/instances/{studyId} — Danh sách instance IDs từ Orthanc
 * Spec plan.md line 306 — dùng cho Cornerstone.js Viewer (spec US4)
 * @param {number} studyId - DB study ID
 * @returns {{ study_id, orthanc_study_id, study_info, instances: [], total }}
 */
export async function getStudyInstances(studyId) {
  const response = await fetch(`${BASE_URL}/dicom/instances/${studyId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data))
  }

  return response.json()
}

/**
 * GET /api/dicom/wado?objectId=xxx — URL stream ảnh DICOM
 * Dùng cho Cornerstone.js imageId format: wado:...
 * @param {string} instanceId - Orthanc instance ID
 * @returns {string} URL dùng làm Cornerstone imageId
 */
export function getWadoUrl(instanceId) {
  const token = localStorage.getItem(TOKEN_KEY)
  // Cornerstone WADO-URI format
  return `/api/dicom/wado?objectId=${instanceId}&token=${token}`
}

/**
 * Tạo Cornerstone imageId từ instanceId
 * Format: wadouri:/api/dicom/wado?objectId=xxx&token=xxx
 * @param {string} instanceId - Orthanc instance ID
 * @returns {string} Cornerstone imageId
 */
export function buildCornerstoneImageId(instanceId) {
  const token = localStorage.getItem(TOKEN_KEY)
  return `wadouri:${window.location.origin}/api/dicom/wado?objectId=${instanceId}&token=${token}`
}
