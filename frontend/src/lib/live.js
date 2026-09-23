import { createContext, useContext } from 'react';
import { API_BASE_URL } from './api';

const WS_BASE = API_BASE_URL.replace(/^http/, 'ws');
const MAX_BACKOFF_MS = 10_000;

// Split so 2 s telemetry frames only re-render telemetry consumers, not every query hook.
export const LiveStatusContext = createContext({ status: 'closed', subscribe: () => () => {} });
export const TelemetryContext = createContext(null);

export const useLiveStatus = () => useContext(LiveStatusContext);

export function useMachineTelemetry(machineId) {
  const frame = useContext(TelemetryContext);
  return frame?.machines.find((m) => m.machine_id === machineId) ?? null;
}

export const useFleetTelemetry = () => useContext(TelemetryContext);

// Opens a WebSocket that reconnects with capped exponential backoff; returns a close function.
export function connectLive(path, { onMessage, onStatus }) {
  let socket;
  let timer;
  let attempt = 0;
  let stopped = false;

  const open = () => {
    onStatus('connecting');
    socket = new WebSocket(`${WS_BASE}${path}`);
    socket.onopen = () => {
      attempt = 0;
      onStatus('open');
    };
    socket.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch {
        // ignore malformed frames
      }
    };
    socket.onclose = () => {
      if (stopped) return;
      onStatus('closed');
      timer = setTimeout(open, Math.min(1000 * 2 ** attempt++, MAX_BACKOFF_MS));
    };
  };

  open();
  return () => {
    stopped = true;
    clearTimeout(timer);
    socket?.close();
  };
}
