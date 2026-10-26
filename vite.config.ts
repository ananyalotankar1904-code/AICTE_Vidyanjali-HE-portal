import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: false,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8020',
        changeOrigin: true,
      },
      '/health': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8020',
        changeOrigin: true,
      },
    },
  },
});
