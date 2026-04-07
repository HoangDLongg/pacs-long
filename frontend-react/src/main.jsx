/* ================================================
   T012 — src/main.jsx
   App entry point — import CSS, mount React app
   ================================================ */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

// CSS — thứ tự quan trọng: variables → base → components → layout
import '@/styles/variables.css'
import '@/styles/base.css'
import '@/styles/components.css'
import '@/styles/layout.css'

import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
