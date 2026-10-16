import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import StaffAccess from './StaffAccess.tsx'

// Register service worker for PWA (static assets only)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('SW registration failed:', err);
    });
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <StaffAccess />
  </StrictMode>,
)
