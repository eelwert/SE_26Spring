import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    css: true,
    include: ['tests/unit/**/*.{test,spec}.{ts,tsx}'],
    environmentOptions: {
      jsdom: {
        url: 'http://127.0.0.1:5173',
      },
    },
  },
});
