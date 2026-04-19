import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteCommonjs } from '@originjs/vite-plugin-commonjs'   // ← Dùng cái này thay vì vite-plugin-commonjs
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    viteCommonjs(),        // Quan trọng: plugin này xử lý tốt hơn với các module codec
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'credentialless',   // credentialless cho phép proxy API hoạt động
    },
  },

  optimizeDeps: {
    exclude: [
      '@cornerstonejs/dicom-image-loader',
      '@cornerstonejs/codec-libjpeg-turbo-8bit',
      '@cornerstonejs/codec-libjpeg-turbo-12bit',   // thêm nếu có
      '@cornerstonejs/codec-charls',
      '@cornerstonejs/codec-openjpeg',
      '@cornerstonejs/codec-openjph',
    ],
    include: ['dicom-parser'],
  },

  worker: {
    format: 'es',
  },

  assetsInclude: ['**/*.wasm'],

  build: {
    commonjsOptions: {
      include: [/node_modules/],
    },
  },
})