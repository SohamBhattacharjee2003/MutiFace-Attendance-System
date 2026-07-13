import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // The frontend now uses same-origin relative URLs (see utils/api.js), so in dev Vite
    // has to forward every backend route to Flask. In production Flask serves the built
    // app itself, so no proxy is involved and the same relative URLs just work.
    // Every backend route now lives under /api, so one proxy rule covers all of them.
    // Anything else is a React Router page and must be handled by Vite, not Flask.
    proxy: {
      "/api": { target: "http://127.0.0.1:5000", changeOrigin: true, secure: false },
    },
  },
})
