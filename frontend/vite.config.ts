import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// @author zhangzhihao
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // 成片/镜头媒资由后端 StaticFiles 提供，开发时需代理到 8000
      '/outputs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
