import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor

import re

from ai_agent.src.agents.base.base_structures import BaseAgentInput
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.log_summarization.examples import (
    LOG_SUMMARY_EXAMPLES,
    REALTIME_LOG_SUMMARY_EXAMPLES,
)
from ai_agent.src.agents.log_summarization.prompt import (
    LOG_QNA_AGENT,
    REALTIME_LOG_SUMMARY_AGENT_PROMPT,
    get_system_prompt,
)
from ai_agent.src.agents.log_summarization.structures import (
    LogQnAOutput,
    LogQnARequest,
    LogSummaryOutput,
    RealtimeLogSummaryInput,
    RealtimeLogSummaryOutput,
    SummarizeInput,
)
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMDoesNotExists, LLMError
from data.embedding.embedding_util import EmbeddingUtil
from data.embedding.langchain_integration import SimulationLogRetriever
from ai_agent.src.agents.base.base_agent import BaseAgent, AgentTask
from data.models.topology.world_model import WorldModal

from langchain_ollama import ChatOllama


class LogSummarizationAgent(BaseAgent):
    """Agent for summarizing and analyzing system logs."""

    logger = logging.getLogger(__name__)

    def __init__(self, llm=None):
        super().__init__(
            agent_id=AgentType.LOG_SUMMARIZER,
            description="Analyzes and summarizes system logs to extract key insights and patterns",
        )
        self.llm: ChatOpenAI = llm

    def _register_tasks(self) -> Dict[str, AgentTask]:
        """Register all tasks this agent can perform."""
        return {
            AgentTaskType.LOG_SUMMARIZATION: AgentTask(
                task_id=AgentTaskType.LOG_SUMMARIZATION,
                description="Summarize log entries to identify key issues and patterns",
                input_schema=SummarizeInput,
                output_schema=LogSummaryOutput,
                examples=LOG_SUMMARY_EXAMPLES,
            ),
            AgentTaskType.LOG_QNA: AgentTask(
                task_id=AgentTaskType.LOG_QNA,
                description="Answer questions about specific events or patterns in logs",
                input_schema=LogQnARequest,
                output_schema=LogQnAOutput,
                examples=[],
            ),
            AgentTaskType.REALTIME_LOG_SUMMARY: AgentTask(
                task_id=AgentTaskType.REALTIME_LOG_SUMMARY,
                description="Generate real-time summaries of log entries",
                input_schema=RealtimeLogSummaryInput,
                output_schema=RealtimeLogSummaryOutput,
                examples=REALTIME_LOG_SUMMARY_EXAMPLES,
            ),
        }

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct message to this agent."""
        content = message.get("content", "")

        # Determine appropriate task based on message content
        if "summarize" in content.lower() or "summary" in content.lower():
            task_id = AgentTaskType.LOG_SUMMARIZATION
        elif "pattern" in content.lower() or "anomaly" in content.lower():
            task_id = AgentTaskType.EXTRACT_PATTERNS
        else:
            task_id = AgentTaskType.LOG_SUMMARIZATION  # Default task

        # Extract log entries from message if present
        log_entries = self._extract_logs_from_message(content)

        # Run the appropriate task
        result = await self.run(task_id, {"logs": log_entries})
        return result

    def _extract_logs_from_message(self, content: str) -> List[str]:
        """Extract log entries from message content."""
        # Simple extraction logic - improve as needed
        lines = content.split("\n")
        log_pattern = r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}"
        return [line for line in lines if re.match(log_pattern, line)]

    async def run(
        self, task_id: AgentTaskType, input_data: Union[Dict[str, Any], BaseAgentInput]
    ) -> Dict[str, Any]:
        """Execute a specific task with the given input data."""
        # Validate input
        validated_input = self.validate_input(task_id, input_data)

        if task_id == AgentTaskType.LOG_SUMMARIZATION:
            result = await self._summarize_logs(validated_input)
        elif task_id == AgentTaskType.LOG_QNA:
            result = await self.log_qna(validated_input)
        elif task_id == AgentTaskType.EXTRACT_PATTERNS:
            result = await self._extract_patterns(validated_input)
        elif task_id == AgentTaskType.REALTIME_LOG_SUMMARY:
            result = await self.realtime_log_summary(validated_input)
        else:
            raise ValueError(f"Task {task_id} not supported")

        # Validate output
        return self.validate_output(task_id, result)

    async def _summarize_logs(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize log entries using create_tool_calling_agent (needs tools to fetch logs)."""
        simulation_id = input_data.get("simulation_id")
        if simulation_id:
            logs = self._get_relevant_logs(simulation_id, "*")
        else:
            logs = input_data.get("logs", [])

        if not logs:
            raise HTTPException(
                status_code=400,
                detail={"message": "No logs provided", "simulation_id": simulation_id},
            )
        
        if self.config.dev.enable_mock_responses:
            with open("docs/sample_files/log_summary_mock_response.json", "r") as f:
                json_str = f.read()
                json_obj = json.loads(json_str)
                return LogSummaryOutput.model_validate(json_obj['action_input'])

        if not self.llm:
            raise LLMError("LLM not available")

        focus_components = input_data.get("focus_components")
        user_query = input_data.get("message")

        # Pattern B: create_tool_calling_agent — uses native tool calling API
        prompt = ChatPromptTemplate.from_messages([
            ("system", get_system_prompt()),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="force",
        )

        try:
            response = await agent_executor.ainvoke(
                {
                    "simulation_id": simulation_id,
                    "logs": json.dumps([logs[0], logs[-1]]),
                    "total_logs": len(logs),
                    "input": user_query
                    or f"Summarize logs for simulation ID: {simulation_id}",
                }
            )
            if "output" in response:
                self.save_agent_response(response)
                output = response["output"]
                # Parse string output if needed
                if isinstance(output, str):
                    try:
                        return LogSummaryOutput.model_validate_json(output)
                    except Exception:
                        return {"summary": output}
                return output
            else:
                return {"summary": "Failed to generate structured output."}
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during agent execution!")
            raise LLMError(f"Error during agent execution: {e}")

    async def _extract_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract recurring patterns from logs."""
        summary_result = await self._summarize_logs(input_data)

        # Add pattern-specific analysis here
        summary_result["summary_text"] = (
            "Pattern analysis: " + summary_result["summary_text"]
        )

        return summary_result

    async def log_qna(self, input_data: Union[Dict[str, Any], LogQnARequest]):
        """Answer questions about logs using create_tool_calling_agent (needs tools to fetch specific logs)."""
        if isinstance(input_data, Dict):
            input_data = LogQnARequest(**input_data)

        if self.config.dev.enable_mock_responses:
            with open("docs/sample_files/log_qna_mock_response.json", "r") as f:
                json_str = f.read()
                json_obj = json.loads(json_str)
                return LogQnAOutput.model_validate(json_obj['action_input'])

        if not self.llm:
            raise LLMError("LLM not available")

        # Pre-fetch topology and chat history (these are always needed)
        topology_data = self._get_topology_by_simulation(input_data.simulation_id)
        chat_history = self._get_chat_history(input_data.conversation_id, 5)

        # Pattern B: create_tool_calling_agent — agent may need to fetch specific logs
        prompt = ChatPromptTemplate.from_messages([
            ("system", LOG_QNA_AGENT),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=self.config.llm.retry_attempts,
            early_stopping_method="force",
        )

        try:
            agent_input = {
                "simulation_id": input_data.simulation_id,
                "topology_data": json.dumps(topology_data) if topology_data else "No topology available.",
                "conversation_id": input_data.conversation_id,
                "optional_instructions": input_data.optional_instructions
                or "None provided.",
                "user_question": input_data.user_query,
                "last_5_messages": chat_history,
                "input": f"Answer the following question about the logs of simulation {input_data.simulation_id}: {input_data.user_query}",
            }
            result = await agent_executor.ainvoke(agent_input)
            final_output_data = result.get("output")

            if isinstance(final_output_data, dict):
                parsed_output = LogQnAOutput.model_validate(final_output_data)
                return parsed_output
            elif isinstance(final_output_data, str):
                try:
                    parsed_output = LogQnAOutput.model_validate_json(final_output_data)
                    return parsed_output
                except Exception as e_parse:
                    self.logger.error(f"Failed to parse string output: {e_parse}")
            
            return None
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during agent execution!")
            raise LLMError(f"Error during agent execution: {e}")

    async def realtime_log_summary(
        self, input_data: Union[Dict[str, Any], RealtimeLogSummaryInput]
    ):
        """Generate realtime log summary using LCEL chain (all data pre-fetched)."""
        if isinstance(input_data, dict):
            input_data = RealtimeLogSummaryInput(**input_data)

        try:
            lite_llm = self.llm.use("lite")
        except LLMDoesNotExists as e:
            print(f"Failed to initialize LLM: {e}")
            lite_llm = self.llm

        if isinstance(lite_llm, ChatOllama):
            lite_llm.format = RealtimeLogSummaryOutput.model_json_schema()

        if not lite_llm:
            raise LLMError("LLM not available")

        topology = self._get_topology_by_simulation(input_data.simulation_id)
        if not topology:
            raise ValueError(
                f"No topology found for simulation ID: {input_data.simulation_id}"
            )

        # Pattern A: LCEL chain — all data pre-fetched
        prompt = ChatPromptTemplate.from_messages([
            ("system", REALTIME_LOG_SUMMARY_AGENT_PROMPT),
            ("human", "{input}"),
        ])

        chain = prompt | lite_llm.with_structured_output(RealtimeLogSummaryOutput)

        try:
            result = await chain.ainvoke({
                "previous_summary": input_data.previous_summary,
                "new_logs": input_data.new_logs,
                "simulation_id": input_data.simulation_id,
                "optional_instructions": input_data.optional_instructions,
                "input": "Summarize delta logs from the simulation and append delta summary to previous summary.",
            })

            if isinstance(result, RealtimeLogSummaryOutput):
                return result
            else:
                self.logger.error(f"Unexpected output type: {type(result)}")
                return None
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during realtime log summary!")
            raise LLMError(f"Error during realtime log summary: {e}")
