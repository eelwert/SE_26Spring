import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';

function createStorageMock(): Storage {
  let values = new Map<string, string>();

  return {
    get length() {
      return values.size;
    },
    clear: () => {
      values = new Map<string, string>();
    },
    getItem: (key: string) => values.get(key) ?? null,
    key: (index: number) => Array.from(values.keys())[index] ?? null,
    removeItem: (key: string) => {
      values.delete(key);
    },
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
  };
}

const storageMock = createStorageMock();

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: storageMock,
});

Object.defineProperty(window, 'localStorage', {
  configurable: true,
  value: storageMock,
});

afterEach(() => {
  localStorage.clear();
});
