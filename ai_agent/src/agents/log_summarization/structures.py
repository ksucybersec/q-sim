from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from datetime import datetime

from ai_agent.src.agents.base.base_structures import BaseAgentInput
from data.models.simulation.log_model import LogEntryModel


class SummarizeInput(BaseAgentInput):
    """Input schema for log summarization tasks."""

    simulation_id: str
    simulation_id: str = Field(
        description="The unique identifier for the simulation run to be summarized."
    )


class ExtractPattersInput(LogEntryModel):
    pass


class SummaryPeriod(BaseModel):
    """Defines the time range covered by the summary."""

    start: Optional[datetime] = Field(
        default=None,
        description="The start timestamp of the period included in the summary. Null if not applicable or calculable.",
    )
    end: Optional[datetime] = Field(
        default=None,
        description="The end timestamp of the period included in the summary. Null if not applicable or calculable.",
    )


class CommunicationFlow(BaseModel):
    """Describes a specific communication path observed between two components."""

    source: str = Field(
        description="The identifier of the component/node where the communication flow originated."
    )
    destination: str = Field(
        description="The identifier of the component/node where the communication flow terminated."
    )
    packet_count: int = Field(
        description="The total number of packets observed traveling from the source to the destination along this path."
    )
    path: List[str] = Field(
        description="An ordered list of component identifiers representing the path taken by packets in this flow."
    )
    relevant_log_pks: List[str] = Field(
        description="A list of primary keys (pks) from the original log entries that provide evidence for this communication flow."
    )


class DetectedIssue(BaseModel):
    """Represents a specific error, warning, or notable anomaly found in the logs."""

    issue: str = Field(
        description="A textual description of the detected issue (e.g., 'Packet timeout', 'QKD key rate low', 'Component error')."
    )
    relevant_log_pks: List[str] = Field(
        description="A list of primary keys (pks) from the original log entries related to this specific issue."
    )


class DetailedSummary(BaseModel):
    """Contains granular metrics and structured information derived from the logs."""

    total_packets_transmitted: Optional[int] = Field(
        default=0,
        description="The overall count of packets transmitted within the summary period across all components.",
    )
    packets_by_source: Dict[str, int] = Field(
        default={},
        description="A dictionary mapping source component identifiers to the number of packets they transmitted.",
    )
    packets_by_destination: Dict[str, int] = Field(
        default={},
        description="A dictionary mapping destination component identifiers to the number of packets they received.",
    )
    communication_flows: List[CommunicationFlow] = Field(
        default=[],
        description="A list detailing specific communication flows identified between components, including paths and packet counts.",
    )
    errors_found: int = Field(
        default=0,
        description="The total count of log entries classified as errors within the summary period.",
    )
    warnings_found: int = Field(
        default=0,
        description="The total count of log entries classified as warnings within the summary period.",
    )
    detected_issues: List[DetectedIssue] = Field(
        default=[],
        description="A list of specific notable issues or anomalies detected during log analysis, beyond simple errors/warnings.",
    )


class KeyLogEvent(BaseModel):
    """A single log entry with details about an event."""

    timestamp: str = Field(description="The date and time when the event occurred.")
    event_type: str = Field(description="The type of event that occurred.")
    description: str = Field(description="A detailed description of the event.")
    severity: Literal["info", "warning", "error", "success"] = Field(
        description="The severity level of the event."
    )


class LogSummaryOutput(BaseModel):
    """The overall structured summary output for a simulation log analysis."""

    simulation_id: str = Field(
        description="The unique identifier for the simulation run being summarized."
    )
    summary_period: Optional[SummaryPeriod] = Field(
        default=None,
        description="Specifies the time window (start and end) that this summary covers, if applicable.",
    )
    short_summary: str = Field(
        description="A brief, human-readable overview of the main events, activities, or findings from the simulation logs."
    )
    key_events: List[KeyLogEvent] = Field(
        default=[],
        description="A list of human readable significant events or milestones identified in the logs from user's perfective.",
    )
    detailed_summary: DetailedSummary = Field(
        description="A nested structure containing detailed quantitative and qualitative analysis derived from the logs."
    )


class LogQnARequest(BaseAgentInput):
    user_query: str = Field(description="Question about the simulation logs.")
    simulation_id: str = Field(
        description="The ID of the simulation to analyze logs of."
    )
    optional_instructions: Optional[str] = Field(
        description="Optional instructions for the analysis process."
    )


class LogQnAOutput(BaseModel):
    status: Literal["answered", "clarification_needed", "error", "unanswerable"] = (
        Field(description="The outcome status of the QnA attempt.")
    )
    answer: str = Field(
        description="The natural language answer if status is 'answered'; the clarifying question if status is 'clarification_needed'; or an error/unanswerable message if status is 'error' or 'unanswerable'."
    )
    cited_log_entries: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="A list of relevant log entry objects (or key parts) that support the answer, only if status is 'answered'.",
    )
    error_message: Optional[str] = Field(
        None, description="Specific error details if status is 'error'."
    )


class RealtimeLogSummaryInput(BaseAgentInput):
    simulation_id: str = Field(
        description="The ID of the simulation to analyze logs of."
    )
    previous_summary: List[str] = Field(
        description="Log summary generated in previous iteration."
    )
    new_logs: List[str] = Field(description="New logs to be analyzed.")
    optional_instructions: Optional[str] = Field(
        description="Optional instructions for the analysis process."
    )


class RealtimeLogSummaryOutput(BaseModel):
    summary_text: List[str] = Field(description="Summary text generated based on the logs. Each index represent a delta summary of logs in each iteration")
    cited_log_entries: List[str] = Field(
        [],
        description="A list of relevant log ids that support the answer. Only if status is 'answered'. Example []'log_1', 'log_2'....]",
    )
    error_message: Optional[str] = Field(
        None, description="Specific error details if status is 'error'."
    )
    thought_process: str = Field(description="Thought process leading to the summary.")
