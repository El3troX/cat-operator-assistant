import { PageHeader } from '../components/ui/page-header';
import AssignedTraining from '../features/coaching/AssignedTraining';
import TaskTimeEstimator from '../features/estimator/TaskTimeEstimator';
import IncidentForm from '../features/incidents/IncidentForm';
import IncidentList from '../features/incidents/IncidentList';
import FleetLiveTable from '../features/live/FleetLiveTable';
import MachineLiveCard from '../features/live/MachineLiveCard';
import AlertFeed from '../features/safety/AlertFeed';
import ProximityRadar from '../features/safety/ProximityRadar';
import SafetyCheck from '../features/safety/SafetyCheck';
import TrainingHub from '../features/training/TrainingHub';

export function SafetyPage() {
  return (
    <>
      <PageHeader title="Safety" description="Proximity hazards, seatbelt compliance and idling, checked live against the rule engine." />
      <div className="mb-4">
        <FleetLiveTable />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <ProximityRadar />
        <SafetyCheck />
      </div>
      <div className="mt-4">
        <AlertFeed />
      </div>
    </>
  );
}

export function IncidentsPage() {
  return (
    <>
      <PageHeader title="Incidents" description="Operator-reported incidents across the fleet." />
      <div className="grid gap-4 lg:grid-cols-[420px_minmax(0,1fr)] lg:items-start">
        <IncidentForm />
        <IncidentList />
      </div>
    </>
  );
}

export function TrainingPage() {
  return (
    <>
      <PageHeader title="Training hub" description="E-learning videos, simulations and instructor sessions." />
      <TrainingHub />
    </>
  );
}

export function EstimatorPage() {
  return (
    <>
      <PageHeader title="Task time estimator" description="Predict how long a job will take from task type, weather, operator skill and machine age." />
      <TaskTimeEstimator />
    </>
  );
}

export function CabTrainingPage() {
  return (
    <div className="space-y-6">
      <AssignedTraining />
      <TrainingHub size="lg" />
    </div>
  );
}

export function CabSafetyPage() {
  return (
    <div className="space-y-4">
      <MachineLiveCard />
      <ProximityRadar size="lg" />
      <SafetyCheck size="lg" />
    </div>
  );
}
