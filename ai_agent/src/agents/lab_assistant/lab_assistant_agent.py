import logging
import traceback
from typing import Any, Dict, Union

from fastapi import HTTPException
from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.lab_assistant.prompt import (
    LAB_CODE_ASSIST_PROMPT,
    LAB_PEER_PROMPT,
)
from ai_agent.src.agents.lab_assistant.solution_code import SOLUTION_CODE_LAB_4
from ai_agent.src.agents.lab_assistant.structures import (
    LabPeerAgentInput,
    LabPeerAgentOutput,
    VibeCodeFunctionOutput,
    VibeCodeInput,
)
from ai_agent.src.consts.agent_type import AgentType

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai_agent.src.agents.base.base_structures import BaseAgentInput
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.exceptions.llm_exception import LLMDoesNotExists, LLMError
from data.models.topology.summarizer import generate_topology_summary


class LabAssistantAgent(BaseAgent):

    logger = logging.getLogger(__name__)

    def __init__(self, llm=None):
        super().__init__(
            agent_id=AgentType.LOG_SUMMARIZER,
            description="Analyzes and summarizes system logs to extract key insights and patterns",
        )
        self.llm: ChatOpenAI = llm

    def _register_tasks(self):
        return {
            AgentTaskType.LAB_CODE_ASSIST: AgentTask(
                task_id=AgentTaskType.LAB_CODE_ASSIST,
                description="Assists with writing code based on provided specifications.",
                input_schema=VibeCodeInput,
                output_schema=VibeCodeFunctionOutput,
                examples=[],
            ),
            AgentTaskType.LAB_PEER: AgentTask(
                task_id=AgentTaskType.LAB_PEER,
                description="Provides feedback and guidance to students on their code.",
                input_schema=LabPeerAgentInput,
                output_schema=LabPeerAgentOutput,
                examples=[],
            ),
        }

    async def process_message(self, message):
        return await super().process_message(message)

    async def run(
        self, task_id: AgentTaskType, input_data: Union[Dict[str, Any], BaseAgentInput]
    ):
        validated_input = self.validate_input(task_id, input_data)
        if task_id == AgentTaskType.LAB_CODE_ASSIST:
            result = await self._lab_code_assist(validated_input)
        elif task_id == AgentTaskType.LAB_PEER:
            result = await self._lab_peer_agent(validated_input)
        else:
            raise ValueError(f"Task {task_id} not supported")

        # Validate output
        return self.validate_output(task_id, result)

    async def _lab_code_assist(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        input_code = input_data.get("student_code", "")
        if not input_code:
            raise HTTPException(
                status_code=400,
                detail={"message": "No code provided"},
            )

        if not self.llm:
            raise LLMError("LLM not available")

        prompt = ChatPromptTemplate.from_messages([
            ("system", LAB_CODE_ASSIST_PROMPT),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm.with_structured_output(VibeCodeFunctionOutput)

        try:
            result = await chain.ainvoke({
                "student_code": input_data.get("student_code"),
                "query": input_data.get("user_query"),
                "cursor_line_number": input_data.get("cursor_line_number"),
                "solution_code": SOLUTION_CODE_LAB_4,
                "input": input_data.get("user_query"),
            })

            if isinstance(result, VibeCodeFunctionOutput):
                return result
            else:
                return {"summary": "Failed to generate structured output."}
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during lab code assist!")
            raise LLMError(f"Error during lab code assist: {e}")

    async def _lab_peer_agent(self, input_data):

        try:
            lite_llm = self.llm.use("lite")
        except LLMDoesNotExists as e:
            print(f"Failed to initialize LLM: {e}")
            # Fallback to using the main model
            lite_llm = self.llm

        # Pre-fetch chat history
        chat_history = self._get_chat_history(input_data.get("conversation_id"), 2)

        prompt = ChatPromptTemplate.from_messages([
            ("system", LAB_PEER_PROMPT),
            ("human", "{input}"),
        ])

        chain = prompt | lite_llm.with_structured_output(LabPeerAgentOutput)

        try:
            result = await chain.ainvoke({
                "LAB_JSON": input_data.get("lab_instructions"),
                "CURRENT_TOPOLOGY": generate_topology_summary(input_data.get("current_topology")) if input_data.get("current_topology") else 'No topology created yet!',
                "CONVERSATION_HISTORY": chat_history,
                "input": input_data.get("user_query"),
            })

            if isinstance(result, LabPeerAgentOutput):
                return result
            else:
                return {"summary": "Failed to generate structured output."}
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during lab peer agent!")
            raise LLMError(f"Error during lab peer agent: {e}")
