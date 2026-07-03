import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    // @ → src/ 的别名，导入时写 @/api/xxx 就不用写 ../../api/xxx
    alias: { '@': resolve(__dirname, 'src') }
  },
  server: {
    port: 5173,
    proxy: {
      // 所有 /api 开头的请求都转发到 Flask 后端
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
