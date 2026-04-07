/* ================================================
   F09 — src/components/shared/UploadZone.jsx
   Drag & drop upload DICOM file
   Calls POST /api/dicom/upload (multipart/form-data)
   ================================================ */

import { useState, useRef } from 'react'

/**
 * UploadZone — khu vực upload file DICOM
 *
 * @param {function} onUpload  - (file: File) => Promise<result>
 * @param {boolean}  disabled  - Disable upload (e.g. đang upload)
 */
export default function UploadZone({ onUpload, disabled = false }) {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState(null)
  const inputRef = useRef(null)

  async function handleFile(file) {
    if (!file || !onUpload) return

    setUploading(true)
    setProgress(30)
    setMessage(null)

    try {
      setProgress(60)
      const result = await onUpload(file)
      setProgress(100)
      setMessage({ type: 'success', text: result?.message || 'Upload thanh cong' })
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Upload that bai' })
    } finally {
      setUploading(false)
      setTimeout(() => setProgress(0), 1500)
    }
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  function handleDragOver(e) {
    e.preventDefault()
    setDragOver(true)
  }

  function handleDragLeave() {
    setDragOver(false)
  }

  function handleClick() {
    if (!uploading && !disabled) {
      inputRef.current?.click()
    }
  }

  function handleInputChange(e) {
    const file = e.target.files[0]
    handleFile(file)
    e.target.value = '' // Reset để có thể upload lại cùng file
  }

  return (
    <div
      className={`upload-zone${dragOver ? ' upload-zone--dragover' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
      id="upload-zone"
    >
      <input
        ref={inputRef}
        type="file"
        accept=".dcm,.dicom,application/dicom"
        onChange={handleInputChange}
        hidden
      />

      <div className="upload-zone__icon">+</div>

      {uploading ? (
        <>
          <p className="upload-zone__text">Dang upload...</p>
          <div className="upload-zone__progress">
            <div
              className="upload-zone__progress-bar"
              style={{ width: `${progress}%` }}
            />
          </div>
        </>
      ) : (
        <p className="upload-zone__text">
          Keo file <strong>.dcm</strong> vao day hoac <strong>click</strong> de chon
        </p>
      )}

      {message && (
        <div className={`alert alert--${message.type}`}>
          {message.text}
        </div>
      )}
    </div>
  )
}
