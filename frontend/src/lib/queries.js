import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from './api';
import { useLiveStatus } from './live';

// Fallback only: while the /ws/events socket is open, pushed events refresh these queries.
const FALLBACK_POLL_MS = 5000;

function usePollWhenOffline() {
  const { status } = useLiveStatus();
  return status === 'open' ? false : FALLBACK_POLL_MS;
}

export const keys = {
  health: ['health'],
  tasks: ['tasks'],
  alerts: (machineId) => ['alerts', machineId ?? 'all'],
  incidents: (machineId) => ['incidents', machineId ?? 'all'],
  anomalies: (machineId) => ['anomalies', machineId ?? 'all'],
  training: ['training'],
};

export function useHealth() {
  return useQuery({ queryKey: keys.health, queryFn: api.health, refetchInterval: 10000, retry: false });
}

export function useTasks() {
  return useQuery({ queryKey: keys.tasks, queryFn: api.tasksToday });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }) => api.updateTask(id, patch),
    onMutate: async ({ id, patch }) => {
      await qc.cancelQueries({ queryKey: keys.tasks });
      const previous = qc.getQueryData(keys.tasks);
      qc.setQueryData(keys.tasks, (tasks = []) => tasks.map((t) => (t.id === id ? { ...t, ...patch } : t)));
      return { previous };
    },
    onError: (err, _vars, ctx) => {
      qc.setQueryData(keys.tasks, ctx?.previous);
      toast.error('Task update failed', { description: err.message });
    },
    onSettled: () => qc.invalidateQueries({ queryKey: keys.tasks }),
  });
}

export function useAlerts(machineId) {
  return useQuery({
    queryKey: keys.alerts(machineId),
    queryFn: () => api.alerts(machineId),
    refetchInterval: usePollWhenOffline(),
  });
}

export function useSafetyCheck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.safetyCheck,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
    onError: (err) => toast.error('Safety check failed', { description: err.message }),
  });
}

export function useProximity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.proximity,
    onSuccess: (res) => {
      if (res.triggered) qc.invalidateQueries({ queryKey: ['alerts'] });
    },
    onError: (err) => toast.error('Proximity reading failed', { description: err.message }),
  });
}

export function useIncidents(machineId) {
  return useQuery({
    queryKey: keys.incidents(machineId),
    queryFn: () => api.incidents(machineId),
    refetchInterval: usePollWhenOffline(),
  });
}

export function useCreateIncident() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createIncident,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incidents'] }),
    onError: (err) => toast.error('Could not log incident', { description: err.message }),
  });
}

export function useAnomalies(machineId) {
  return useQuery({ queryKey: keys.anomalies(machineId), queryFn: () => api.anomalies(machineId) });
}

export function useTraining() {
  return useQuery({ queryKey: keys.training, queryFn: api.trainingModules });
}

export function useUpdateTraining() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, completed }) => api.updateTrainingModule(id, { completed }),
    onMutate: async ({ id, completed }) => {
      await qc.cancelQueries({ queryKey: keys.training });
      const previous = qc.getQueryData(keys.training);
      qc.setQueryData(keys.training, (mods = []) => mods.map((m) => (m.id === id ? { ...m, completed } : m)));
      return { previous };
    },
    onError: (err, _vars, ctx) => {
      qc.setQueryData(keys.training, ctx?.previous);
      toast.error('Could not update module', { description: err.message });
    },
    onSettled: () => qc.invalidateQueries({ queryKey: keys.training }),
  });
}

export function usePredictTaskTime() {
  return useMutation({
    mutationFn: api.predictTaskTime,
    onError: (err) => toast.error('Prediction failed', { description: err.message }),
  });
}
