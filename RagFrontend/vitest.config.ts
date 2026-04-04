import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// 独立的 vitest 测试配置，不依赖 vite.config.ts 的异步 devtools 加载
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      include: ['src/utils/**', 'src/store/**', 'src/composables/**', 'src/router/**'],
      exclude: ['src/**/*.vue', 'src/main.ts'],
      thresholds: {
        statements: 95,
        lines: 95,
        branches: 80,
        functions: 75
      }
    }
  }
})
