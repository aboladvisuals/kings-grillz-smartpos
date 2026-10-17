import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  // Android System WebView on the Pixel 4 emulator is Chromium 83.
  // Logical assignment (||=, &&=, ??=) requires Chrome 85+. Target
  // es2020 so esbuild transpiles those operators without affecting
  // modern browsers or the desktop app.
  build: {
    target: ['es2020', 'chrome80', 'safari14'],
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8000' } },
  },
  preview: { host: '127.0.0.1' },
})
