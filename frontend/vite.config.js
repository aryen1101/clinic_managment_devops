import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// During `npm run dev`, forward API calls to the backend on :8000
// (in Docker/Kubernetes, nginx does this job instead).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/ready': 'http://localhost:8000',
    },
  },
});
