import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import '../../../packages/shared/tokens.css'
import './App.css'
import App from './App.tsx'
import { installGlobalErrorTracking } from './services/telemetryErrors'

installGlobalErrorTracking()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
