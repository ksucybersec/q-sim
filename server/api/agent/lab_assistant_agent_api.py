from typing import Any, Dict

from fastapi import HTTPException

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.lab_assistant.structures import (
    LabPeerAgentInput,
    VibeCodeInput,
)
from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.orchestration.coordinator import Coordinator


async def handle_lab_assistant(message_dict: Dict[str, Any]):
    task_id = message_dict.get("task_id", AgentTaskType.LAB_CODE_ASSIST.value)
    if task_id == AgentTaskType.LAB_CODE_ASSIST.value:
        message = VibeCodeInput(**message_dict)
        task_id = AgentTaskType.LAB_CODE_ASSIST
    elif task_id == AgentTaskType.LAB_PEER.value:
        message = LabPeerAgentInput(**message_dict)
        task_id = AgentTaskType.LAB_PEER
    else:
        raise HTTPException("Invalid task ID")

    agent_coordinator = Coordinator()
    response = await agent_coordinator.execute_workflow(
        WorkflowType.LAB_ASSISTANT_WORKFLOW.value,
        {
            "task_data": {
                "task_id": task_id,
                "input_data": message.model_dump(),
            }
        },
    )

    return response
