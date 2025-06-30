"""Log model for network simulation"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from redis_om import JsonModel, Field as RedisField, Migrator

from core.enums import NodeType
from data.models.connection.redis import get_redis_conn


class LogLevel(str, Enum):
    """Log level types"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntryModel(JsonModel):
    """Model representing a log entry in a simulation"""

    simulation_id: str = RedisField(index=True)
    timestamp: datetime = RedisField(index=True, default_factory=datetime.now)
    level: LogLevel = RedisField(index=True, default=LogLevel.INFO)
    component: str = RedisField(index=True)
    entity_type: Optional[NodeType] = None
    entity_id: Optional[str] = RedisField(index=True, default=None)
    details: Dict[str, Any] = {}

    def to_human_string(self) -> str:
        """Convert log entry to human-readable string"""
        details_str = ", ".join(f"{key}: {value}" for key, value in self.details.items()) if self.details else ""
        return f"{self.timestamp} [{self.level}] {self.component}: {details_str}"

    class Meta:
        global_key_prefix = "network-sim"
        model_key_prefix = "log"
        database = get_redis_conn()


def add_log_entry(log_data: Dict[str, Any]) -> LogEntryModel:
    """Add a log entry to Redis"""
    # Ensure we have a connection
    get_redis_conn()

    # Ensure indexes are created
    Migrator().run()

    # Create LogEntry instance
    log_entry = LogEntryModel(**log_data)

    # Save to Redis
    log_entry.save()

    return log_entry


def get_log_entry(primary_key: str) -> Optional[LogEntryModel]:
    """Retrieve log entry from Redis by primary key"""
    # Ensure we have a connection
    get_redis_conn()

    try:
        return LogEntryModel.get(primary_key)
    except Exception as e:
        print(f"Error retrieving log entry: {e}")
        return None


def get_logs_by_simulation(
    simulation_id: str,
    level: Optional[LogLevel] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[LogEntryModel]:
    """Get logs for a specific simulation with optional filtering"""
    # Ensure we have a connection
    get_redis_conn()

    query = LogEntryModel.find(LogEntryModel.simulation_id == simulation_id)

    # Add level filter if provided
    if level:
        query = query.find(LogEntryModel.level == level)

    # Sort by timestamp descending (newest first)
    query = query.sort_by("-timestamp")

    # Apply pagination
    query = query.offset(offset).limit(limit)

    return query.all()


def get_entity_logs(
    simulation_id: str, entity_type: NodeType, entity_id: str
) -> List[LogEntryModel]:
    """Get logs related to a specific entity in a simulation"""
    # Ensure we have a connection
    get_redis_conn()

    return (
        LogEntryModel.find(LogEntryModel.simulation_id == simulation_id)
        .find(LogEntryModel.entity_type == entity_type)
        .find(LogEntryModel.entity_id == entity_id)
        .sort_by("-timestamp")
        .all()
    )


def clear_simulation_logs(simulation_id: str) -> bool:
    """Delete all logs for a specific simulation"""
    # Ensure we have a connection
    get_redis_conn()

    try:
        # Find all logs for the simulation
        logs = LogEntryModel.find(LogEntryModel.simulation_id == simulation_id).all()

        # Delete each log
        for log in logs:
            log.delete()

        return True
    except Exception as e:
        print(f"Error clearing simulation logs: {e}")
        return False
