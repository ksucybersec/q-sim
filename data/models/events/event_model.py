from typing import Any, Dict, Optional, Union
from redis_om import JsonModel, Field
from datetime import datetime

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.consts.agent_type import AgentType
from config.config import get_config
from data.models.connection.redis import get_redis_conn
from data.models.events.event_enum import UserEventType
from data.models.topology.node_model import HOST_TYPES

config = get_config()

class UserEventModal(JsonModel):
    # Core Event Data
    user_id: str = Field(index=True)
    session_id: str = Field(index=True)
    event_type: UserEventType = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Config Environment
    ai_enabled : Optional[bool] = Field(default=config.control_config.enable_ai_feature)
    llm_model_name : Optional[str] = Field(default=config.llm.model)
    lite_llm_model_name : Optional[str] = Field(default=config.llm.lite_model)
    
    # Context
    page_url: Optional[str] = None
    module_name: Optional[str] = None
    world_id: Optional[str] = None
    lab_id: Optional[str] = None
    component_type: Optional[HOST_TYPES] = None
    
    # Interaction Details
    click_coordinates: Optional[Dict[str, int]] = None  # {"x": 100, "y": 200}
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    element_description: Optional[str] = None
    
    # Component/Lab Specific
    component_id: Optional[str] = None
    connection_from: Optional[str] = None
    connection_to: Optional[str] = None
    lab_step: Optional[Union[int, str]] = None
    lab_progress: Optional[float] = None
    
    # AI Help Analytics
    agent_message: Optional[str] = None
    agent_response: Optional[Dict[str, Any]] = None
    agent_id: Optional[AgentType] = None
    task_id: Optional[AgentTaskType] = None
    ai_message_extra_data: Optional[Dict[str, Any]] = None
    conversation_context: Optional[Dict[str, Any]] = None
    help_category: Optional[str] = None  # "conceptual", "procedural", "troubleshooting"
    help_effectiveness: Optional[int] = None  # 1-5 rating after task completion
    pre_help_attempts: Optional[int] = None  # failed attempts before asking AI
    post_help_success: Optional[bool] = None  # did student succeed after AI help
    help_sequence_id: Optional[str] = None  # links related help interactions
    question_complexity: Optional[int] = None  # 1-5 scale
    response_type: Optional[str] = None  # "direct_answer", "guided_discovery", "hint"
    time_to_apply_advice: Optional[int] = None  # ms between help and implementation
    
    # AI Help Analytics
    help_category: Optional[str] = None  # "conceptual", "procedural", "troubleshooting"
    help_effectiveness: Optional[int] = None  # 1-5 rating after task completion
    pre_help_attempts: Optional[int] = None  # failed attempts before asking AI
    post_help_success: Optional[bool] = None  # did student succeed after AI help
    
    # Parameter Changes
    parameter_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    # Performance Data
    response_time_ms: Optional[int] = None
    task_duration_ms: Optional[int] = None
    success: Optional[bool] = None
    
    # Assessment Data, TODO: Think, if there should be some assessments or not
    score: Optional[float] = None
    max_score: Optional[float] = None
    answer_data: Optional[Dict[str, Any]] = None
    
    # Survey/Rating Data
    rating: Optional[int] = None  # 1-5 scale
    rating_scale: Optional[str] = None  # "likert", "sus", "nasa_tlx"
    
    # Error Information
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    # Simulation Data
    simulation_config: Optional[Dict[str, Any]] = None
    simulation_results: Optional[Dict[str, Any]] = None
    
    # Additional Context
    metadata: Optional[Dict[str, Any]] = None
    
    class Meta:
        global_key_prefix = "network-sim"
        model_key_prefix = "user_events"
        database = get_redis_conn()