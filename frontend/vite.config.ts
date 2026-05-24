import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'vendor'
          }
          if (id.includes('node_modules/react-markdown') || id.includes('node_modules/remark')) {
            return 'markdown'
          }
          if (id.includes('node_modules/react-syntax-highlighter')) {
            return 'highlight'
          }
        },
      },
    },
  },
})
