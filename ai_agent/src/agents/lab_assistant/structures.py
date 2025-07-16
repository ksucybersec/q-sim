import json
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, conint

from ai_agent.src.agents.base.base_structures import BaseAgentInput
from data.models.topology.world_model import WorldModal

class VibeCodeInput(BaseAgentInput):
    student_code: str = Field(
        ..., 
        description="The full content of the student's current code file."
    )
    
    user_query: str = Field(
        ...,
        description="The natural language query from the student."
    )
    
    cursor_line_number: int = Field(
        ...,
        ge=1,
        description="The 1-indexed line number of the user's cursor. This is used to identify the target function."
    )

    solution_code: Optional[str] = Field(
        default="",
        description="The complete, correct solution code for the lab. This serves as the ground truth.",
    )


class VibeCodeFunctionOutput(BaseModel):
    function_name: str = Field(
        ...,
        description="The name of the function that should be replaced (e.g., 'create_bell_pair')."
    )

    start_line_number: int = Field(
        ...,
        ge=1,
        description="The 1-indexed line number where the function definition (`def function_name(...):`) begins in the student's code."
    )

    generated_code: str = Field(
        ...,
        description="The full, correctly-indented source code for the entire function, from the 'def' line to the last line of its body. Only send this if query is about code generation. Otherwise, this should be an empty string."
    )
    
    explanation: str = Field(
        ...,
        description="A user-facing explanation of the provided code's logic and purpose."
    )
    
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="The agent's confidence in the accuracy and relevance of the response."
    )


class LabPeerAgentInput(BaseAgentInput):
    lab_instructions: Dict[str, Any] = Field(..., description="Detailed instructions provided by the peer for the lab.")
    current_topology: Optional[WorldModal] = Field(None, description="Current topology information for the lab.")


class LabPeerAgentOutput(BaseModel):
    response: str = Field(..., description="Response to the peer's question.")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="The agent's confidence in the accuracy and relevance of the response.")
    thought_process: str = Field(..., description="The agent's thought process leading to the answer.")
    response_type: Literal["direct_answer", "guided_discovery", "hint"] = Field("direct_answer", description="Type of response provided by the agent.")