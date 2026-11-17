import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // The dev server forwards any request that starts with /api to the
    // backend. Docker Compose uses this: it sets VITE_API_URL=/api, so the
    // browser calls the frontend's own address, and API_PROXY_TARGET points
    // at the backend container. Without Docker, api.js calls the backend
    // directly and this proxy goes unused.
    proxy: {
      '/api': process.env.API_PROXY_TARGET || 'http://127.0.0.1:5000',
    },
  },
})
