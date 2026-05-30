// Import both API implementations
import { mockApi } from './mockApi';
import { realApi } from './realApi';

// Set to true when the backend server is running (uvicorn backend.server:app --port 8000)
const USE_REAL_API = true;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const _useMock = mockApi as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const _useReal = realApi as any;

export const api = USE_REAL_API ? _useReal : _useMock;
