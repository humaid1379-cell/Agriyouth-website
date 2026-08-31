import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

/**
 * The dev server proxies the API so the browser talks to a single origin. There is no
 * external host in this configuration: everything resolves to the local workbench.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: false },
      '/health': { target: 'http://localhost:8000', changeOrigin: false },
    },
  },
  preview: { port: 5173, strictPort: true },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2022',
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
    css: false,
  },
});
