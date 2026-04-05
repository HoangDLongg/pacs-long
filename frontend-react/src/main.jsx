/* ================================================
   T012 — src/main.jsx
   App entry point — import CSS, mount React app
   ================================================ */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

// CSS — thứ tự quan trọng: variables trước, rồi base, rồi components
import '@/styles/variables.css'
import '@/styles/base.css'
import '@/styles/components.css'

import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
