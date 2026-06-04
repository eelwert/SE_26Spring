import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'python -m uvicorn backend.server:app --host 127.0.0.1 --port 18000',
      url: 'http://127.0.0.1:18000/api/health',
      reuseExistingServer: false,
      timeout: 30_000,
      env: {
        ...process.env,
        DEEPSEEK_API_KEY: '',
        QWEN_API_KEY: '',
        ZHIPU_API_KEY: '',
      },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        VITE_BACKEND_ORIGIN: 'http://127.0.0.1:18000',
        VITE_API_BASE_URL: 'http://127.0.0.1:18000/api',
        VITE_WS_URL: 'ws://127.0.0.1:18000/ws/frontend',
      },
    },
  ],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
