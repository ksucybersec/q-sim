from enum import Enum


class AgentTaskType(Enum):
    LOG_SUMMARIZATION = "summarize"
    LOG_QNA = "log_qna"
    REALTIME_LOG_SUMMARY = "realtime_summarization"
    EXTRACT_PATTERNS = "extract_patterns"
    OPTIMIZE_TOPOLOGY = "optimize_topology"
    SYNTHESIZE_TOPOLOGY = "synthesize_topology"
    TOPOLOGY_QNA = "topology_qna"
    ROUTING = "routing"
    VALIDATE_TOPOLOGY = "validate_topology"
    LAB_CODE_ASSIST = "lab_code_assist"
    LAB_PEER = "lab_peer"