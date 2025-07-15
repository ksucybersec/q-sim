import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_structured_chat_agent, AgentExecutor

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
        """Summarize log entries."""
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

        focus_components = input_data.get("focus_components")
        user_query = input_data.get("message")

        output_parser = PydanticOutputParser(pydantic_object=LogSummaryOutput)

        system_template = get_system_prompt()

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            "{input}\n\n{agent_scratchpad}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        prompt = prompt.partial(
            answer_instructions=output_parser.get_format_instructions()
        )

        if self.llm and self.tools:
            llm_with_tools = self.llm.bind_tools(self.tools)

            agent = create_structured_chat_agent(llm_with_tools, self.tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors="Strictly follow to 'RESPONSE FORMAT' given in prompt",
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
                    return response["output"]
                else:
                    return {"summary": "Failed to generate structured output."}
            except Exception as e:
                traceback.print_exc()
                self.logger.exception(f"Exception during agent execution!")
                raise LLMError(f"Error during agent execution: {e}")
        else:
            raise Exception("LLM not available, logs invalid, or no tools defined")

    async def _extract_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract recurring patterns from logs."""
        # Similar implementation to summarize but focused on patterns
        # This is a simplified version - expand as needed
        summary_result = await self._summarize_logs(input_data)

        # Add pattern-specific analysis here
        summary_result["summary_text"] = (
            "Pattern analysis: " + summary_result["summary_text"]
        )

        return summary_result

    async def log_qna(self, input_data: Union[Dict[str, Any], LogQnARequest]):
        if isinstance(input_data, Dict):
            # Implement the logic to optimize the topology based on the provided instructions
            input_data = LogQnARequest(**input_data)
        parser = PydanticOutputParser(pydantic_object=LogQnAOutput)
        format_instructions = parser.get_format_instructions()

        system_message_prompt = SystemMessagePromptTemplate.from_template(LOG_QNA_AGENT)

        human_message_prompt = HumanMessagePromptTemplate.from_template(
            "{input}\n\n{agent_scratchpad}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        if self.llm and self.tools:
            llm_with_tools = self.llm.bind_tools(self.tools)

            agent = create_structured_chat_agent(llm_with_tools, self.tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors="Strictly follow to 'RESPONSE FORMAT' given in prompt",
                max_iterations=5,
                early_stopping_method="force",
            )

            try:
                agent_input = {
                    "simulation_id": input_data.simulation_id,
                    "topology_data": self._get_topology_by_simulation(
                        input_data.simulation_id
                    ),
                    "conversation_id": input_data.conversation_id,
                    "optional_instructions": input_data.optional_instructions
                    or "None provided. Apply general optimization principles.",
                    "answer_instructions": format_instructions,
                    "user_question": input_data.user_query,
                    "last_5_messages": self._get_chat_history(
                        input_data.conversation_id, 5
                    ),
                    "input": f"Answer the following question about the logs of simulation {input_data.simulation_id}: {input_data.user_query}",
                }
                result = agent_executor.invoke(agent_input)
                final_output_data = result.get("output")

                if isinstance(final_output_data, dict):
                    # Parse the dictionary into the Pydantic model for validation
                    parsed_output = LogQnAOutput.model_validate(final_output_data)
                    print("--- Optimization Proposal Generated ---")
                    return parsed_output
                else:
                    print(
                        f"ERROR: Agent returned unexpected final output format: {type(final_output_data)}"
                    )
                    print(f"Raw output: {final_output_data}")
                    # Attempt to parse if it's a string containing JSON (shouldn't happen with correct prompt)
                    if isinstance(final_output_data, str):
                        try:
                            parsed_output = LogQnAOutput.model_validate_json(
                                final_output_data
                            )
                            print(
                                "--- Optimization Proposal Generated (Parsed from String) ---"
                            )
                            return parsed_output
                        except Exception as e_parse:
                            print(
                                f"ERROR: Failed to parse string output as JSON: {e_parse}"
                            )

                    return None  # Failed
            except Exception as e:
                traceback.print_exc()
                self.logger.exception(f"Exception during agent execution!")
                raise LLMError(f"Error during agent execution: {e}")
        else:
            raise Exception("LLM not available, logs invalid, or no tools defined")

    async def realtime_log_summary(
        self, input_data: Union[Dict[str, Any], RealtimeLogSummaryInput]
    ):
        if isinstance(input_data, dict):
            input_data = RealtimeLogSummaryInput(**input_data)
        try:
            lite_llm = self.llm.use("lite")
        except LLMDoesNotExists as e:
            print(f"Failed to initialize LLM: {e}")
            # Fallback to using the main model
            lite_llm = self.llm

        if isinstance(lite_llm, ChatOllama):
            lite_llm.format = RealtimeLogSummaryOutput.model_json_schema()

        parser = PydanticOutputParser(pydantic_object=RealtimeLogSummaryOutput)
        format_instructions = parser.get_format_instructions()

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            REALTIME_LOG_SUMMARY_AGENT_PROMPT
        )

        human_message_prompt = HumanMessagePromptTemplate.from_template(
            "{input}\n\n{agent_scratchpad}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        if lite_llm and self.tools:
            llm_with_tools = lite_llm.bind_tools([])

            agent = create_structured_chat_agent(llm_with_tools, self.tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors=True,
                max_iterations=5,
                early_stopping_method="force",
            )

            topology = self._get_topology_by_simulation(input_data.simulation_id)
            if not topology:
                raise ValueError(
                    f"No topology found for simulation ID: {input_data.simulation_id}"
                )

            try:
                agent_input = {
                    "previous_summary": input_data.previous_summary,
                    "new_logs": input_data.new_logs,
                    "simulation_id": input_data.simulation_id,
                    # 'topology_details': topology,
                    # 'topology_details_definition':WorldModal.model_json_schema(),
                    "optional_instructions": input_data.optional_instructions,
                    "answer_instructions": format_instructions,
                    "input": "Summarize delta logs from the simulation and append delta summary to previous summary.",
                }
                result = agent_executor.invoke(agent_input)
                final_output_data = result.get("output")

                if isinstance(final_output_data, dict):
                    # Parse the dictionary into the Pydantic model for validation
                    parsed_output = RealtimeLogSummaryOutput.model_validate(
                        final_output_data
                    )
                    return parsed_output
                else:
                    print(
                        f"ERROR: Agent returned unexpected final output format: {type(final_output_data)}"
                    )
                    # Attempt to parse if it's a string containing JSON (shouldn't happen with correct prompt)
                    if isinstance(final_output_data, str):
                        try:
                            parsed_output = (
                                RealtimeLogSummaryOutput.model_validate_json(
                                    final_output_data
                                )
                            )
                            return parsed_output
                        except Exception as e_parse:
                            print(
                                f"ERROR: Failed to parse string output as JSON: {e_parse}"
                            )

                    return None  # Failed
            except Exception as e:
                traceback.print_exc()
                self.logger.exception(f"Exception during agent execution!")
                raise LLMError(f"Error during agent execution: {e}")
        else:
            raise Exception("LLM not available, logs invalid, or no tools defined")
