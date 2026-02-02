from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from ai_agent.src.agents.base.base_agent import AgentTask
from ai_agent.src.agents.base.base_structures import BaseAgentInput, BaseAgentOutput
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.consts.agent_type import AgentType
from server.api.agent.agent_request import AgentRouterRequest

class RoutingInput(BaseAgentInput):
    agent_details: List[str] = Field(
        description="Details about the agents available for routing. This should include their capabilities and any other relevant information."
    )
    user_query: Union[Dict[str, Any], AgentRouterRequest] = None


class RoutingOutput(BaseAgentOutput):
    """Structured output for agent routing decision."""
    agent_id: AgentType = Field(
        None,
        description="The unique ID of the selected agent. Null if no suitable agent was found."
    )
    task_id: AgentTaskType = Field(
        description=f"Task ID for the selected agent's selected task. (For example Task ID for summarizing logs is '{AgentTaskType.LOG_SUMMARIZATION.value}' for {AgentType.LOG_SUMMARIZER.value} agent)"
    )
    input_data: Dict[str, Any] = Field(
        description="The original user query that was evaluated."
    )
    # agent_description: AgentTask = Field(
    #     description="The task that the selected agent will perform. This is a structured object with fields like 'task_id', 'description', 'input_schema', and 'output_schema'.",
    # )
    reason: str = Field(
        description="Explanation of why the specific agent was chosen, or why no agent was deemed suitable. (Addressed to user)"
    )
    suggestion: Optional[str] = Field(
        None,
        description="A suggestion to help the user if no suitable agent was found (e.g., rephrase query, list available functions)."
    )
    agent_response: Optional[Any] = None