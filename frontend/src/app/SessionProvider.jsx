import { useEffect, useMemo, useState } from 'react';
import { SessionContext } from '../lib/session';
import { MACHINES, OPERATORS } from '../lib/constants';

const STORAGE_KEY = 'soa.session';
const DEFAULT_SESSION = { machineId: MACHINES[0], operatorId: OPERATORS[0] };

function loadSession() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (MACHINES.includes(saved?.machineId) && OPERATORS.includes(saved?.operatorId)) return saved;
  } catch {
    // storage unavailable or corrupt
  }
  return DEFAULT_SESSION;
}

export default function SessionProvider({ children }) {
  const [session, setSession] = useState(loadSession);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    } catch {
      // storage unavailable
    }
  }, [session]);

  const value = useMemo(
    () => ({
      ...session,
      setMachineId: (machineId) => setSession((s) => ({ ...s, machineId })),
      setOperatorId: (operatorId) => setSession((s) => ({ ...s, operatorId })),
    }),
    [session],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
