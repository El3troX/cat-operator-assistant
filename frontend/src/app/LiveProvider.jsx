import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { connectLive, LiveStatusContext, TelemetryContext } from '../lib/live';

// Scores depend on alerts, incidents and training completion, so those events refresh them too.
const INVALIDATES = {
  'alert.created': ['alerts', 'scores'],
  'incident.created': ['incidents', 'scores'],
  'task.updated': ['tasks'],
  'training.updated': ['training', 'scores'],
};
// Refreshed on every (re)connect: events may have been missed, and an open socket proves the API is back.
const LIVE_QUERY_ROOTS = ['alerts', 'incidents', 'tasks', 'training', 'scores', 'health'];

export default function LiveProvider({ children }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('connecting');
  const [telemetry, setTelemetry] = useState(null);
  const listeners = useRef(new Set());

  useEffect(() => {
    const closeEvents = connectLive('/ws/events', {
      onMessage: (event) => {
        (INVALIDATES[event.type] ?? []).forEach((root) => queryClient.invalidateQueries({ queryKey: [root] }));
        listeners.current.forEach((listener) => listener(event));
      },
      onStatus: (next) => {
        if (next === 'open') LIVE_QUERY_ROOTS.forEach((root) => queryClient.invalidateQueries({ queryKey: [root] }));
        // A dropped socket usually means the API went down; confirm now rather than at the next health poll.
        if (next === 'closed') queryClient.invalidateQueries({ queryKey: ['health'] });
        setStatus(next);
      },
    });
    const closeTelemetry = connectLive('/ws/telemetry', {
      onMessage: setTelemetry,
      onStatus: (next) => next === 'closed' && setTelemetry(null),
    });
    return () => {
      closeEvents();
      closeTelemetry();
    };
  }, [queryClient]);

  const subscribe = useCallback((listener) => {
    listeners.current.add(listener);
    return () => listeners.current.delete(listener);
  }, []);

  const statusValue = useMemo(() => ({ status, subscribe }), [status, subscribe]);

  return (
    <LiveStatusContext.Provider value={statusValue}>
      <TelemetryContext.Provider value={telemetry}>{children}</TelemetryContext.Provider>
    </LiveStatusContext.Provider>
  );
}
