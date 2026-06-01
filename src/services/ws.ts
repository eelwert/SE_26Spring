/** WebSocket client for receiving real-time task updates from the backend. */

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

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const url = `ws://localhost:8000/ws/frontend`;
    this.ws = new WebSocket(url);

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
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    this.ws?.close();
    this.ws = null;
  }
}

export const wsClient = new WSClient();
