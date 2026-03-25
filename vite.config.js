import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [vue()],
  // Build output is served by FastAPI under /webapp/.
  base: command === 'build' ? '/webapp/' : '/',
}))
