/* ================================================
   src/pages/Viewer/index.jsx
   DICOM Viewer — Cornerstone3D v4 (npm)
   Spec US4: zoom, pan, window/level, scroll CT
   Route: /viewer/:id  (id = study DB id)
   Roles: All (patient chỉ xem ca của mình — enforced ở backend)
   ================================================ */

import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getStudyInstances } from '@/api/dicom'

// ====================== Cornerstone3D imports ======================
import {
  init as coreInit,
  RenderingEngine,
  Enums as csEnums,
  cache as csCache,
  metaData as csMetaData,
} from '@cornerstonejs/core'

import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader'

import * as cornerstoneTools from '@cornerstonejs/tools'

const {
  WindowLevelTool,
  ZoomTool,
  PanTool,
  StackScrollTool,
  LengthTool,
  AngleTool,
  ToolGroupManager,
  Enums: csToolsEnums,
  init: toolsInit,
} = cornerstoneTools

const { MouseBindings } = csToolsEnums
const { ViewportType } = csEnums

// IDs cố định
const RENDERING_ENGINE_ID = 'pacs-rendering-engine'
const VIEWPORT_ID = 'pacs-dicom-viewport'
const TOOL_GROUP_ID = 'pacs-tool-group'

// ====================== Init Cornerstone3D (chạy 1 lần) ======================
let csInitialized = false

async function initCornerstone() {
  if (csInitialized) return
  try {
    await coreInit()

    await dicomImageLoaderInit({
      maxWebWorkers: navigator.hardwareConcurrency || 4,
      preferWebWorkers: true,
    })

    await toolsInit()

    // Đăng ký tools
    cornerstoneTools.addTool(WindowLevelTool)
    cornerstoneTools.addTool(ZoomTool)
    cornerstoneTools.addTool(PanTool)
    cornerstoneTools.addTool(StackScrollTool)
    cornerstoneTools.addTool(LengthTool)
    cornerstoneTools.addTool(AngleTool)

    csInitialized = true
    console.log('[Cornerstone3D] Initialized successfully')
  } catch (err) {
    console.error('[Cornerstone3D] Init failed:', err)
    throw err
  }
}

// ====================== Component chính ======================
export default function ViewerPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const elementRef = useRef(null)   // div cho viewport
  const engineRef = useRef(null)   // RenderingEngine instance
  const toolGroupRef = useRef(null)   // ToolGroup instance

  const [instances, setInstances] = useState([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [studyInfo, setStudyInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [csReady, setCsReady] = useState(false)
  const [tool, setTool] = useState('WindowLevel')   // active tool name

  // ====================== 1. Init Cornerstone3D ======================
  useEffect(() => {
    initCornerstone()
      .then(() => setCsReady(true))
      .catch((err) => setError('Không thể khởi tạo Cornerstone3D: ' + err.message))
  }, [])

  // ====================== 2. Fetch instances từ backend ======================
  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)

    getStudyInstances(id)
      .then((data) => {
        setStudyInfo(data.study_info)
        setInstances(data.instances || [])
        setCurrentIdx(0)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  // ====================== 3. Setup RenderingEngine + Viewport ======================
  useEffect(() => {
    if (!csReady || !elementRef.current || instances.length === 0) return

    let cancelled = false
    const element = elementRef.current
    const token = localStorage.getItem('pacs_token')

    // Unique IDs cho mỗi mount cycle
    const engineId = RENDERING_ENGINE_ID + '-' + Date.now()
    const toolGroupId = TOOL_GROUP_ID + '-' + Date.now()

    // Build imageIds
    const imageIds = instances.map((inst) => {
      const instanceId = inst?.ID || inst
      return `wadouri:${window.location.origin}/api/dicom/wado?objectId=${instanceId}&token=${token}`
    })

    // Tạo RenderingEngine
    const renderingEngine = new RenderingEngine(engineId)
    engineRef.current = renderingEngine

    // Enable viewport
    renderingEngine.enableElement({
      viewportId: VIEWPORT_ID,
      element,
      type: ViewportType.STACK,
    })

    const viewport = renderingEngine.getViewport(VIEWPORT_ID)

    // Set stack + auto-VOI
    viewport.setStack(imageIds, 0).then(async () => {
      if (cancelled) return
      console.log(`[Cornerstone3D] Loaded ${imageIds.length} images`)

      // Auto-VOI: lấy pixel data trực tiếp từ canvas/vtk image
      try {
        // Approach: đọc pixel data từ vtkImageData (đã decode sẵn)
        const vtkImageData = viewport.getImageData()?.imageData
        if (vtkImageData) {
          const scalars = vtkImageData.getPointData().getScalars()
          if (scalars) {
            const data = scalars.getData()
            const range = scalars.getRange()
            const pxMin = range[0], pxMax = range[1]
            const pxRange = pxMax - pxMin

            // Check current VOI
            const props = viewport.getProperties()
            const curLower = props.voiRange?.lower ?? 0
            const curUpper = props.voiRange?.upper ?? 65535
            const curRange = curUpper - curLower

            console.log(`[CS3D] Pixel range: ${pxMin}-${pxMax}, Current VOI: ${curLower}-${curUpper}`)

            // Nếu VOI quá rộng so với pixel data → fix
            if (pxRange > 0 && curRange > pxRange * 3) {
              viewport.setProperties({
                voiRange: { lower: pxMin, upper: pxMax },
              })
              console.log(`[CS3D] Auto-VOI applied: ${pxMin}-${pxMax}`)
            }
          }
        }
      } catch (e) {
        console.warn('[CS3D] Auto-VOI failed:', e)
      }

      viewport.resetCamera()
      viewport.render()
    }).catch(err => {
      if (cancelled) return
      console.error('[Cornerstone3D] setStack error:', err)
      setError('Không thể load ảnh DICOM. Kiểm tra file hoặc Orthanc.')
    })

    // Setup ToolGroup
    try { ToolGroupManager.destroyToolGroup(toolGroupId) } catch (_) { }

    const toolGroup = ToolGroupManager.createToolGroup(toolGroupId)
    toolGroupRef.current = toolGroup

    toolGroup.addTool(WindowLevelTool.toolName)
    toolGroup.addTool(ZoomTool.toolName)
    toolGroup.addTool(PanTool.toolName)
    toolGroup.addTool(StackScrollTool.toolName)
    toolGroup.addTool(LengthTool.toolName)
    toolGroup.addTool(AngleTool.toolName)

    toolGroup.addViewport(VIEWPORT_ID, engineId)

    toolGroup.setToolActive(WindowLevelTool.toolName, {
      bindings: [{ mouseButton: MouseBindings.Primary }],
    })
    toolGroup.setToolActive(PanTool.toolName, {
      bindings: [{ mouseButton: MouseBindings.Auxiliary }],
    })
    toolGroup.setToolActive(ZoomTool.toolName, {
      bindings: [{ mouseButton: MouseBindings.Secondary }],
    })

    setTool('WindowLevel')

    // Cleanup (per user's suggestion — proper cleanup order)
    return () => {
      cancelled = true
      try {
        if (toolGroupRef.current) {
          ToolGroupManager.destroyToolGroup(toolGroupId)
          toolGroupRef.current = null
        }
      } catch (_) { }

      try {
        if (engineRef.current) {
          engineRef.current.disableElement(VIEWPORT_ID)  // quan trọng
          engineRef.current.destroy()
          engineRef.current = null
        }
      } catch (_) { }

      // Xóa canvas cũ
      if (elementRef.current) {
        elementRef.current.innerHTML = ''
      }
    }
  }, [csReady, instances])

  // ====================== 4. Scroll chuột để chuyển ảnh ======================
  useEffect(() => {
    const el = elementRef.current
    if (!el || instances.length <= 1 || !csReady) return

    const handleWheel = (e) => {
      e.preventDefault()
      const viewport = engineRef.current?.getViewport(VIEWPORT_ID)
      if (!viewport) return

      const currentImageIdIndex = viewport.getCurrentImageIdIndex()
      const totalImages = instances.length

      let newIndex
      if (e.deltaY > 0) {
        newIndex = Math.min(currentImageIdIndex + 1, totalImages - 1)
      } else {
        newIndex = Math.max(currentImageIdIndex - 1, 0)
      }

      if (newIndex !== currentImageIdIndex) {
        viewport.setImageIdIndex(newIndex)
        setCurrentIdx(newIndex)
      }
    }

    el.addEventListener('wheel', handleWheel, { passive: false })
    return () => el.removeEventListener('wheel', handleWheel)
  }, [csReady, instances])

  // ====================== 5. Tool activation ======================
  const activateTool = useCallback((toolName) => {
    const toolGroup = toolGroupRef.current
    if (!toolGroup) return

    // Deactivate tất cả tools khỏi primary mouse button trước
    const allTools = [
      WindowLevelTool.toolName,
      ZoomTool.toolName,
      PanTool.toolName,
      StackScrollTool.toolName,
      LengthTool.toolName,
      AngleTool.toolName,
    ]

    allTools.forEach((t) => {
      try { toolGroup.setToolPassive(t) } catch (_) { }
    })

    // Activate tool được chọn
    toolGroup.setToolActive(toolName, {
      bindings: [{ mouseButton: MouseBindings.Primary }],
    })

    setTool(toolName)
  }, [])

  // Reset view
  const resetView = useCallback(() => {
    const viewport = engineRef.current?.getViewport(VIEWPORT_ID)
    if (!viewport) return
    viewport.resetCamera()
    viewport.render()
  }, [])

  // ====================== Render ======================
  const tools = [
    { key: WindowLevelTool.toolName, label: 'W/L' },
    { key: ZoomTool.toolName, label: 'Zoom' },
    { key: PanTool.toolName, label: 'Pan' },
    { key: StackScrollTool.toolName, label: 'Scroll' },
    { key: LengthTool.toolName, label: 'Đo' },
    { key: AngleTool.toolName, label: 'Góc' },
  ]

  return (
    <div className="viewer-page">
      {/* ---- Header ---- */}
      <div className="viewer-header">
        <button
          className="btn btn--ghost viewer-back-btn"
          onClick={() => navigate(-1)}
        >
          ← Quay lại
        </button>

        {studyInfo && (
          <div className="viewer-study-meta">
            <span className="viewer-meta-item">
              BN: <strong>{studyInfo.patient_name}</strong>
            </span>
            <span className="viewer-meta-item">
              Ngày: <strong>{studyInfo.study_date}</strong>
            </span>
            <span className="viewer-meta-item">
              Modality: <strong>{studyInfo.modality}</strong>
            </span>
            {instances.length > 0 && (
              <span className="viewer-meta-item">
                Ảnh: <strong>{currentIdx + 1} / {instances.length}</strong>
              </span>
            )}
          </div>
        )}

        <button
          className="btn btn--primary btn--sm"
          onClick={() => navigate(`/report/${id}`)}
          style={{ marginLeft: 'auto' }}
        >
          Báo cáo
        </button>
      </div>

      {/* ---- Toolbar ---- */}
      <div className="viewer-toolbar">
        {tools.map((t) => (
          <button
            key={t.key}
            className={`btn btn--sm ${tool === t.key ? 'btn--primary' : 'btn--ghost'}`}
            onClick={() => activateTool(t.key)}
            title={t.label}
          >
            {t.label}
          </button>
        ))}

        <div className="viewer-toolbar__divider" />

        <button
          className="btn btn--sm btn--ghost"
          onClick={resetView}
          title="Reset"
        >
          Reset
        </button>
      </div>

      {/* ---- Canvas / States ---- */}
      <div className="viewer-canvas-area">
        {loading && (
          <div className="viewer-state">
            <div className="spinner" />
            <p>Đang tải dữ liệu...</p>
          </div>
        )}

        {!loading && error && (
          <div className="viewer-state viewer-state--error">
            <p>{error}</p>
            <button className="btn btn--ghost" onClick={() => window.location.reload()}>
              Thử lại
            </button>
          </div>
        )}

        {!loading && !error && instances.length === 0 && (
          <div className="viewer-state">
            {/* Spec US4 acceptance 4: ca chưa có DICOM → "Chưa có file DICOM" */}
            <p className="viewer-empty-text">Chưa có file DICOM cho ca này</p>
            <p className="viewer-empty-sub">
              KTV cần upload file .dcm trước khi xem ảnh
            </p>
          </div>
        )}

        {/* Cornerstone3D viewport element */}
        <div
          ref={elementRef}
          className={`viewer-canvas ${instances.length === 0 ? 'viewer-canvas--hidden' : ''}`}
          style={{ width: '100%', height: '100%' }}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>

      {/* ---- Thumbnail strip (nếu nhiều slice) ---- */}
      {instances.length > 1 && (
        <div className="viewer-filmstrip">
          {instances.slice(0, 20).map((inst, i) => (
            <button
              key={i}
              className={`viewer-thumb ${i === currentIdx ? 'viewer-thumb--active' : ''}`}
              onClick={() => {
                setCurrentIdx(i)
                const viewport = engineRef.current?.getViewport(VIEWPORT_ID)
                if (viewport) {
                  viewport.setImageIdIndex(i)
                }
              }}
            >
              {i + 1}
            </button>
          ))}
          {instances.length > 20 && (
            <span className="viewer-thumb-more">+{instances.length - 20}</span>
          )}
        </div>
      )}
    </div>
  )
}
