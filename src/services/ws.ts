/** WebSocket client for receiving real-time task updates from the backend. */

import { FRONTEND_WS_URL } from './api/config';

type TaskUpdate = {
  type: 'task_update';
  taskId: string;
  status: string;
  progress: number;
  results: string[];
};

type WSCallback = (update: TaskUpdate) => void;

class WSClient {
  private ws: WebSocket | null = null;
  private callbacks: WSCallback[] = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.shouldReconnect = true;
    this.ws = new WebSocket(FRONTEND_WS_URL);

    this.ws.onopen = () => {
      console.log('[WS] Connected to backend');
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as TaskUpdate;
        if (data.type === 'task_update') {
          this.callbacks.forEach((cb) => cb(data));
        }
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      if (!this.shouldReconnect) return;
      console.log('[WS] Disconnected, reconnecting in 3s...');
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };

    this.ws.onerror = () => {
      // onclose will fire after this, triggering reconnect
    };
  }

  onUpdate(cb: WSCallback) {
    this.callbacks.push(cb);
    return () => {
      this.callbacks = this.callbacks.filter((c) => c !== cb);
    };
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }
}

export const wsClient = new WSClient();
