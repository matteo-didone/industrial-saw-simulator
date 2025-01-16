import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true
  },
  // Aggiungiamo anche la configurazione per il proxy se necessario
  proxy: {
    '/api': {
      target: 'http://edge-device:5000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
})