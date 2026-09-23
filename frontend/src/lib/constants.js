// Mirrors CONTRACT.md §1 — keep in sync with backend/schemas.py.
export const TASK_TYPES = ['Earth Excavation', 'Trenching', 'Material Loading', 'Grading', 'Demolition'];
export const WEATHERS = ['Sunny', 'Rainy', 'Cloudy', 'Windy'];
export const OPERATOR_SKILLS = ['Beginner', 'Intermediate', 'Expert'];
export const TASK_STATUSES = ['Pending', 'In Progress', 'Completed'];
export const SEVERITIES = ['Low', 'Medium', 'High'];
export const SEATBELT = ['Fastened', 'Unfastened'];

export const MACHINES = ['EXC001', 'EXC002', 'EXC003', 'EXC004', 'EXC005'];
export const OPERATORS = Array.from({ length: 10 }, (_, i) => `OP${1001 + i}`);

export const IDLE_THRESHOLD_MIN = 45;
export const PROXIMITY_ALERT_M = 2;
