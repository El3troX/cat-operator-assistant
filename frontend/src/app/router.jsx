import { createBrowserRouter, Navigate } from 'react-router';
import AnomalyPanel from '../features/anomalies/AnomalyPanel';
import CoachingBoard from '../features/coaching/CoachingBoard';
import IncidentForm from '../features/incidents/IncidentForm';
import CabTasks from '../features/tasks/CabTasks';
import TaskBoard from '../features/tasks/TaskBoard';
import CabLayout from '../layouts/CabLayout';
import CommandLayout from '../layouts/CommandLayout';
import { CabSafetyPage, CabTrainingPage, EstimatorPage, IncidentsPage, SafetyPage, TrainingPage } from './pages';

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/command" replace /> },
  {
    path: '/command',
    element: <CommandLayout />,
    children: [
      { index: true, element: <TaskBoard /> },
      { path: 'safety', element: <SafetyPage /> },
      { path: 'incidents', element: <IncidentsPage /> },
      { path: 'anomalies', element: <AnomalyPanel /> },
      { path: 'coaching', element: <CoachingBoard /> },
      { path: 'training', element: <TrainingPage /> },
      { path: 'estimator', element: <EstimatorPage /> },
    ],
  },
  {
    path: '/cab',
    element: <CabLayout />,
    children: [
      { index: true, element: <CabTasks /> },
      { path: 'safety', element: <CabSafetyPage /> },
      { path: 'report', element: <IncidentForm size="lg" /> },
      { path: 'training', element: <CabTrainingPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/command" replace /> },
]);
