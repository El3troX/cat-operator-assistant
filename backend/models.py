from sqlalchemy import Column, Float, Integer, String, Text
from database import Base


class OperationLog(Base):
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    timestamp = Column(Text, nullable=False)
    machine_id = Column(Text, nullable=False, index=True)
    operator_id = Column(Text, nullable=False, index=True)
    engine_hours = Column(Float, nullable=True)
    fuel_used_l = Column(Float, nullable=True)
    load_cycles = Column(Integer, nullable=True)
    idling_time_min = Column(Integer, nullable=True)
    seatbelt_status = Column(Text, nullable=True)
    safety_alert_triggered = Column(Integer, nullable=True)


class TaskTimeData(Base):
    __tablename__ = "task_time_data"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    task_id = Column(Text, nullable=True)
    task_type = Column(Text, nullable=True)
    weather = Column(Text, nullable=True)
    operator_skill = Column(Text, nullable=True)
    machine_age_yrs = Column(Integer, nullable=True)
    estimated_time_min = Column(Integer, nullable=True)
    actual_time_min = Column(Integer, nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    machine_id = Column(Text, nullable=False, index=True)
    operator_id = Column(Text, nullable=False, index=True)
    task_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="Pending", server_default="Pending")
    scheduled_time = Column(Text, nullable=True)
    estimated_time_min = Column(Integer, nullable=True)
    actual_time_min = Column(Integer, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    machine_id = Column(Text, nullable=False, index=True)
    operator_id = Column(Text, nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(Text, nullable=True)
    timestamp = Column(Text, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    machine_id = Column(Text, nullable=False, index=True)
    operator_id = Column(Text, nullable=False, index=True)
    type = Column(Text, nullable=False)
    severity = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    timestamp = Column(Text, nullable=False)


class TrainingModule(Base):
    __tablename__ = "training_modules"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(Text, nullable=False)
    format = Column(Text, nullable=True)
    duration_min = Column(Integer, nullable=True)
    completed = Column(Integer, nullable=True, default=0, server_default="0")
