/* ================================================
   src/pages/Compare/index.jsx
   Multi-study Compare — 2 DICOM viewports side-by-side
   Route: /compare/:leftId/:rightId
   Roles: All (backend enforces patient isolation)
   ================================================ */

import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getStudyInstances } from '@/api/dicom'

import {
  init as coreInit,
  RenderingEngine,
  Enums as csEnums,
} from '@cornerstonejs/core'

import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader'
import * as cornerstoneTools from '@cornerstonejs/tools'

const {
  WindowLevelTool,
  ZoomTool,
  PanTool,
  StackScrollTool,
  ToolGroupManager,
  Enums: csToolsEnums,
  init: toolsInit,
} = cornerstoneTools

const { MouseBindings } = csToolsEnums
const { ViewportType } = csEnums

// ---- Init CS3D (shared singleton) ----
let csInitialized = false
async function initCornerstone() {
  if (csInitialized) return
  await coreInit()
  await dicomImageLoaderInit({ maxWebWorkers: navigator.hardwareConcurrency || 4, preferWebWorkers: true })
  await toolsInit()
  cornerstoneTools.addTool(WindowLevelTool)
  cornerstoneTools.addTool(ZoomTool)
  cornerstoneTools.addTool(PanTool)
  cornerstoneTools.addTool(StackScrollTool)
  csInitialized = true
}

// ---- Single viewport panel ----
function ViewportPanel({ studyId, panelId, csReady }) {
  const elementRef = useRef(null)
  const engineRef = useRef(null)
  const toolGroupRef = useRef(null)

  const [studyInfo, setStudyInfo] = useState(null)
  const [instances, setInstances] = useState([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTool, setActiveTool] = useState('WindowLevel')

  // Fetch instances
  useEffect(() => {
    if (!studyId) return
    setLoading(true)
    getStudyInstances(studyId)
      .then((data) => {
        setStudyInfo(data.study_info)
        setInstances(data.instances || [])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [studyId])

  // Setup viewport
  useEffect(() => {
    if (!csReady || !elementRef.current || instances.length === 0) return

    let cancelled = false
    const token = localStorage.getItem('pacs_token')
    const engineId = `compare-engine-${panelId}-${Date.now()}`
    const viewportId = `compare-vp-${panelId}`
    const toolGroupId = `compare-tg-${panelId}-${Date.now()}`

    const imageIds = instances.map((inst) => {
      const id = inst?.ID || inst
      return `wadouri:${window.location.origin}/api/dicom/wado?objectId=${id}&token=${token}`
    })

    const renderingEngine = new RenderingEngine(engineId)
    engineRef.current = renderingEngine

    renderingEngine.enableElement({
      viewportId,
      element: elementRef.current,
      type: ViewportType.STACK,
    })

    const viewport = renderingEngine.getViewport(viewportId)

    viewport.setStack(imageIds, 0).then(() => {
      if (cancelled) return

      // Auto-VOI
      try {
        const vtkImageData = viewport.getImageData()?.imageData
        if (vtkImageData) {
          const scalars = vtkImageData.getPointData().getScalars()
          if (scalars) {
            const range = scalars.getRange()
            const pxMin = range[0], pxMax = range[1]
            const props = viewport.getProperties()
            const curRange = (props.voiRange?.upper ?? 65535) - (props.voiRange?.lower ?? 0)
            if ((pxMax - pxMin) > 0 && curRange > (pxMax - pxMin) * 3) {
              viewport.setProperties({ voiRange: { lower: pxMin, upper: pxMax } })
            }
          }
        }
      } catch (_) {}

      viewport.resetCamera()
      viewport.render()
    })

    // Tools
    try { ToolGroupManager.destroyToolGroup(toolGroupId) } catch (_) {}
    const toolGroup = ToolGroupManager.createToolGroup(toolGroupId)
    toolGroupRef.current = toolGroup
    toolGroup.addTool(WindowLevelTool.toolName)
    toolGroup.addTool(ZoomTool.toolName)
    toolGroup.addTool(PanTool.toolName)
    toolGroup.addTool(StackScrollTool.toolName)
    toolGroup.addViewport(viewportId, engineId)
    toolGroup.setToolActive(WindowLevelTool.toolName, {
      bindings: [{ mouseButton: MouseBindings.Primary }],
    })
    toolGroup.setToolActive(ZoomTool.toolName, {
      bindings: [{ mouseButton: MouseBindings.Secondary }],
    })

    // Scroll
    const handleWheel = (e) => {
      e.preventDefault()
      const vp = engineRef.current?.getViewport(viewportId)
      if (!vp) return
      const cur = vp.getCurrentImageIdIndex()
      const next = e.deltaY > 0
        ? Math.min(cur + 1, instances.length - 1)
        : Math.max(cur - 1, 0)
      if (next !== cur) {
        vp.setImageIdIndex(next)
        setCurrentIdx(next)
      }
    }
    elementRef.current?.addEventListener('wheel', handleWheel, { passive: false })

    return () => {
      cancelled = true
      elementRef.current?.removeEventListener('wheel', handleWheel)
      try { ToolGroupManager.destroyToolGroup(toolGroupId) } catch (_) {}
      try {
        engineRef.current?.disableElement(viewportId)
        engineRef.current?.destroy()
        engineRef.current = null
      } catch (_) {}
      if (elementRef.current) elementRef.current.innerHTML = ''
    }
  }, [csReady, instances, panelId])

  // Tool switching
  function switchTool(toolName) {
    const tg = toolGroupRef.current
    if (!tg) return
    ;[WindowLevelTool.toolName, ZoomTool.toolName, PanTool.toolName, StackScrollTool.toolName]
      .forEach(t => { try { tg.setToolPassive(t) } catch (_) {} })
    tg.setToolActive(toolName, { bindings: [{ mouseButton: MouseBindings.Primary }] })
    setActiveTool(toolName)
  }

  function resetView() {
    const viewportId = `compare-vp-${panelId}`
    const vp = engineRef.current?.getViewport(viewportId)
    if (vp) { vp.resetCamera(); vp.render() }
  }

  const panelLabel = panelId === 'left' ? 'A' : 'B'

  return (
    <div className="compare-panel">
      {/* Panel header — study info */}
      <div className="compare-panel__header">
        <span className="compare-panel__label">{panelLabel}</span>
        {studyInfo ? (
          <>
            <span className="compare-panel__meta">
              BN: <strong>{studyInfo.patient_name}</strong>
            </span>
            <span className="compare-panel__meta">
              {studyInfo.modality}
            </span>
            <span className="compare-panel__meta">
              {studyInfo.study_date}
            </span>
            {instances.length > 1 && (
              <span className="compare-panel__meta">
                Ảnh: {currentIdx + 1}/{instances.length}
              </span>
            )}
          </>
        ) : (
          <span className="compare-panel__meta">Study #{studyId}</span>
        )}
      </div>

      {/* Panel toolbar */}
      <div className="compare-panel__toolbar">
        {[
          { key: WindowLevelTool.toolName, label: 'W/L' },
          { key: ZoomTool.toolName, label: 'Zoom' },
          { key: PanTool.toolName, label: 'Pan' },
          { key: StackScrollTool.toolName, label: 'Scroll' },
        ].map(t => (
          <button
            key={t.key}
            className={`btn btn--xs ${activeTool === t.key ? 'btn--primary' : 'btn--ghost'}`}
            onClick={() => switchTool(t.key)}
          >
            {t.label}
          </button>
        ))}
        <button className="btn btn--xs btn--ghost" onClick={resetView}>Reset</button>
      </div>

      {/* Viewport */}
      <div className="compare-panel__canvas">
        {loading && (
          <div className="viewer-state">
            <div className="spinner" />
            <p>Đang tải...</p>
          </div>
        )}
        {!loading && error && (
          <div className="viewer-state viewer-state--error">
            <p>{error}</p>
          </div>
        )}
        {!loading && !error && instances.length === 0 && (
          <div className="viewer-state">
            <p>Chưa có file DICOM</p>
          </div>
        )}
        <div
          ref={elementRef}
          className={`viewer-canvas ${instances.length === 0 ? 'viewer-canvas--hidden' : ''}`}
          style={{ width: '100%', height: '100%' }}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
    </div>
  )
}

// ---- Compare Page ----
export default function ComparePage() {
  const { leftId, rightId } = useParams()
  const navigate = useNavigate()
  const [csReady, setCsReady] = useState(false)

  useEffect(() => {
    initCornerstone()
      .then(() => setCsReady(true))
      .catch(() => {})
  }, [])

  return (
    <div className="page-content" style={{ padding: 0, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="viewer-header" style={{ padding: '0.5rem 1rem', flexShrink: 0 }}>
        <button className="btn btn--ghost" onClick={() => navigate(-1)}>
          ← Quay lại
        </button>
        <span style={{ color: 'var(--text-muted)', marginLeft: '1rem' }}>
          So sánh: Study #{leftId} vs #{rightId}
        </span>
      </div>

      {/* 2 panels side-by-side */}
      <div className="compare-container">
        <ViewportPanel studyId={leftId} panelId="left" csReady={csReady} />
        <div className="compare-divider" />
        <ViewportPanel studyId={rightId} panelId="right" csReady={csReady} />
      </div>
    </div>
  )
}
