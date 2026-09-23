import { useEffect } from 'react';
import { toast } from 'sonner';
import { useLiveStatus } from '../lib/live';
import { isLocalAlert } from '../lib/local-alerts';
import { buzz } from '../lib/utils';

// Toasts high-severity alerts pushed from elsewhere (another cab, the simulator).
// Pass machineId to only hear about one machine, as Cab Mode does.
export default function LiveAlertToaster({ machineId }) {
  const { subscribe } = useLiveStatus();

  useEffect(
    () =>
      subscribe(({ type, data }) => {
        if (type !== 'alert.created' || data.severity !== 'High' || isLocalAlert(data)) return;
        if (machineId && data.machine_id !== machineId) return;
        buzz();
        toast.error(`${data.type} alert · ${data.machine_id}`, {
          description: data.operator_id === 'SYSTEM' ? data.message : `${data.message} (${data.operator_id})`,
        });
      }),
    [subscribe, machineId],
  );

  return null;
}
