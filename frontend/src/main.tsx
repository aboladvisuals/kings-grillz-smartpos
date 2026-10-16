import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import StaffAccess from './StaffAccess.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <StaffAccess />
  </StrictMode>,
)
