const stripTrailingSlash = (value: string) => value.replace(/\/+$/, '');

const defaultBackendOrigin = 'http://localhost:8000';

export const BACKEND_START_COMMAND =
  'python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload';

export const API_BASE_URL = stripTrailingSlash(
  import.meta.env.VITE_API_BASE_URL ?? `${defaultBackendOrigin}/api`,
);

export const BACKEND_ORIGIN = stripTrailingSlash(
  import.meta.env.VITE_BACKEND_ORIGIN ?? API_BASE_URL.replace(/\/api$/, ''),
);

export const FRONTEND_WS_URL =
  import.meta.env.VITE_WS_URL ??
  `${BACKEND_ORIGIN.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')}/ws/frontend`;

export const backendFetchUrl = (path: string) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

export const backendConnectionMessage = () =>
  `无法连接后端服务。请先启动：${BACKEND_START_COMMAND}`;
