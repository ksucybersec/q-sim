
from typing import Any, Dict

from fastapi import HTTPException

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.lab_assistant.structures import VibeCodeInput
from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.orchestration.coordinator import Coordinator


async def handle_lab_assistant(message_dict: Dict[str, Any]):
    # if (message_dict.get('task_id') == AgentTaskType.LAB_CODE_ASSIST.value):
    message = VibeCodeInput(**message_dict)
    # else:
    #     raise HTTPException("Invalid task ID")
    
    agent_coordinator = Coordinator()
    
    response = await agent_coordinator.execute_workflow(
        WorkflowType.LAB_ASSISTANT_WORKFLOW.value,
        {
            "task_data": {
                "task_id": AgentTaskType.LAB_CODE_ASSIST,
                "input_data": message.model_dump(),
            }
        },
    )
    
    return response