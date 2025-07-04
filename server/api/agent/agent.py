import traceback
from typing import Any, Dict
from fastapi import APIRouter, Body
from ai_agent.src.consts.agent_type import AgentType
from fastapi import HTTPException

from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.orchestration.coordinator import Coordinator
from data.models.conversation.conversation_model import MessageRole
from data.models.conversation.conversation_ops import add_chat_message, create_conversation_metadata, get_conversation_metadata
from server.api.agent.agent_request import AgentInteractionRequest, AgentRouterRequest
from server.api.agent.lab_assistant_agent_api import handle_lab_assistant
from server.api.agent.summarize import handle_summary_request
from server.api.agent.topology_agent_api import handle_topology_design


agent_router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


async def handle_routing_request(message_dict: Dict[str, Any]):
    message = AgentRouterRequest(**message_dict)
    agent_coordinator = Coordinator()
    response = await agent_coordinator.execute_workflow(WorkflowType.ROUTING, message.model_dump())
    return response

agent_to_handler = {
    AgentType.LOG_SUMMARIZER.value: handle_summary_request,
    AgentType.ORCHESTRATOR.value: handle_routing_request,
    AgentType.TOPOLOGY_DESIGNER.value: handle_topology_design,
    AgentType.LAB_ASSISTANT_AGENT.value: handle_lab_assistant
}

@agent_router.post("/message")
async def get_agent_message(message: Dict[str, Any] = Body()):
    try:
        validated_message = AgentInteractionRequest(**message)
        conversation_metadata = get_conversation_metadata(validated_message.conversation_id)
        if conversation_metadata is None:
            conversation_metadata = create_conversation_metadata(validated_message.conversation_id)

        add_chat_message(conversation_metadata.pk, MessageRole.USER, message.get('user_query'))
        response = await agent_to_handler[message['agent_id']](message)

        return response
    except KeyError  as e:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {message.get('agent_id', 'INVALID_AGENT_ID')}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
