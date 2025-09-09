from logging import getLogger
import traceback
from typing import Any, Dict, Union

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.agents import create_structured_chat_agent, AgentExecutor

from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.topology_agent.examples import SYNTHESIZE_EXAMPLES, TOPOLOGY_OPTIMIZE_EXAMPLES
from ai_agent.src.agents.topology_agent.parser import convert_simplified_to_complex_with_layout
from ai_agent.src.agents.topology_agent.prompt import (
    TOPOLOGY_GENERATOR_AGENT,
    TOPOLOGY_OPTIMIZER_PROMPT,
    TOPOLOGY_QNA_PROMPT,
)
from ai_agent.src.agents.topology_agent.structure import (
    OptimizeTopologyOutput,
    OptimizeTopologyRequest,
    SimplifiedTopology,
    SynthesisTopologyOutput,
    SynthesisTopologyRequest,
    TopologyQnAOutput,
    TopologyQnARequest,
)
from ai_agent.src.agents.validation_agent.structures import TopologyValidationResult, ValidationStatus
from ai_agent.src.agents.validation_agent.validation_agent import ValidationAgent
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMError
from config.config import get_config
from data.models.conversation.conversation_model import AgentExecutionStatus
from data.models.conversation.conversation_ops import finish_agent_turn, start_agent_turn
from data.models.topology.world_model import WorldModal, save_world_to_redis


class TopologyAgent(BaseAgent):
    logger = getLogger(__name__)

    def __init__(self, llm=None):
        super().__init__(
            agent_id=AgentType.TOPOLOGY_DESIGNER,
            description=f"""
                A topology designer agent that helps in designing and optimizing network topologies.
                This can either synthesize a new topology or optimize an existing one.
            """,
        )

        self.llm: ChatOpenAI = llm
        self.validation_agent = ValidationAgent(llm)

    def _register_tasks(self):
        return {
            AgentTaskType.OPTIMIZE_TOPOLOGY: AgentTask(
                task_id=AgentTaskType.OPTIMIZE_TOPOLOGY,
                description="Optimize an existing network topology based on generic principles or optional instructions.",
                input_schema=OptimizeTopologyRequest,
                output_schema=OptimizeTopologyOutput,
                examples=TOPOLOGY_OPTIMIZE_EXAMPLES,
            ),
            AgentTaskType.SYNTHESIZE_TOPOLOGY: AgentTask(
                task_id=AgentTaskType.SYNTHESIZE_TOPOLOGY,
                description="Synthesize a new network topology based on specific requirements or instructions.",
                input_schema=SynthesisTopologyRequest,
                output_schema=SynthesisTopologyOutput,
                examples=SYNTHESIZE_EXAMPLES,
            ),
            AgentTaskType.TOPOLOGY_QNA: AgentTask(
                task_id=AgentTaskType.TOPOLOGY_QNA,
                description="Answer questions about the topology of a specific world.",
                input_schema=TopologyQnARequest,
                output_schema=TopologyQnAOutput,
                examples=[],
            ),
        }

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def run(
        self, task_id: AgentTaskType, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        validated_input = self.validate_input(task_id, input_data)
        turn = start_agent_turn(input_data['conversation_id'], self.agent_id, task_id, validated_input)
        if task_id == AgentTaskType.OPTIMIZE_TOPOLOGY:
            result = await self.update_topology(validated_input)
        elif task_id == AgentTaskType.SYNTHESIZE_TOPOLOGY:
            result = await self.synthesize_topology(validated_input)
            config = get_config()


            if config.agents.agent_validation.enabled:
                # validate the synthesis result with the validation agent
                errors = await self.validation_agent.run(AgentTaskType.VALIDATE_TOPOLOGY, {'generate_response': result})
                
                errors = TopologyValidationResult(**errors)
                # Handle validation errors
                if errors.validation_status == ValidationStatus.FAILED:
                    result.success = False
                    result.error =','.join(errors.static_errors)
                    result.overall_feedback = "Synthesis failed due to validation errors."
                elif errors.validation_status == ValidationStatus.FAILED_WITH_ERRORS:
                    result.success = False
                    result.error = [f"{i.issue_type}: {i.description}" for i in errors.issues_found]
                    result.overall_feedback = "Synthesis failed due to validation errors."
                elif errors.validation_status == ValidationStatus.PASSED_WITH_WARNINGS:
                    result.success = True
                    result.error = [f"{i.issue_type}: {i.description}" for i in errors.issues_found]
                elif errors.validation_status == ValidationStatus.FAILED_RETRY_RECOMMENDED:
                    # Recommend retry with specific feedback if enabled
                    if config.agents.agent_validation.regenerate_on_invalid:
                        validated_input['regeneration_feedback'] = errors.regeneration_feedback
                        result = await self.synthesize_topology(validated_input)
                    else:
                        result.success = False
                        result.error = [f"{i.issue_type}: {i.description}" for i in errors.issues_found]
                        result.overall_feedback = "Synthesis failed due to validation errors."
                
        elif task_id == AgentTaskType.TOPOLOGY_QNA:
            result = await self.topology_qna(validated_input)
        else:
            raise ValueError(f"Unsupported task ID: {task_id}")

        # Validate output
        validated_output =  self.validate_output(task_id, result)

        if turn:
            finish_agent_turn(turn.pk, AgentExecutionStatus.SUCCESS, validated_output.copy())
            validated_output['message_id'] = turn.pk

            if task_id == AgentTaskType.SYNTHESIZE_TOPOLOGY or task_id == AgentTaskType.OPTIMIZE_TOPOLOGY:
                print("================>", type(result), type(result.generated_topology))
                if isinstance(result.generated_topology, SimplifiedTopology):
                    print("Simplified topology found")
                    generated_topology = convert_simplified_to_complex_with_layout(result)
                elif isinstance(result.generated_topology, WorldModal):
                    print("WorldModal found")
                    generated_topology = result.generated_topology
                else:
                    raise ValueError("Unsupported generated topology type")
                generated_topology.temporary_world = True
                generated_topology = save_world_to_redis(generated_topology)
                result.generated_topology = generated_topology
                validated_output =  self.validate_output(task_id, result)
        return validated_output

    async def synthesize_topology(
        self, input_data: Union[Dict[str, Any], SynthesisTopologyRequest]
    ) -> Union[SynthesisTopologyOutput, None]:
        if isinstance(input_data, Dict):
            # Implement the logic to optimize the topology based on the provided instructions
            input_data = SynthesisTopologyRequest(**input_data)
        parser = PydanticOutputParser(pydantic_object=SynthesisTopologyOutput)
        format_instructions = parser.get_format_instructions()

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            TOPOLOGY_GENERATOR_AGENT
        )

        human_message_prompt = HumanMessagePromptTemplate.from_template(
            "{input}\n\n{agent_scratchpad}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        if self.llm:
            agent = create_structured_chat_agent(self.llm, [], prompt)

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
                agent_input = {
                    "user_instructions": input_data.user_query,
                    # "answer_instructions": format_instructions,
                    "input": input_data.user_query,
                    'regeneration_feedback_from_validation': input_data.regeneration_feedback,
                }
                result = agent_executor.invoke(agent_input)
                final_output_data = result.get("output")

                if isinstance(final_output_data, dict):
                    # Parse the dictionary into the Pydantic model for validation
                    parsed_output = SynthesisTopologyOutput.model_validate(
                        final_output_data
                    )
                    print("--- Synthesis Topology Proposal Generated ---")
                    return parsed_output
                else:
                    print(
                        f"ERROR: Agent returned unexpected final output format: {type(final_output_data)}"
                    )
                    print(f"Raw output: {final_output_data}")
                    # Attempt to parse if it's a string containing JSON (shouldn't happen with correct prompt)
                    if isinstance(final_output_data, str):
                        try:
                            parsed_output = SynthesisTopologyOutput.model_validate_json(
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

    async def update_topology(
        self, input_data: Union[Dict[str, Any], OptimizeTopologyRequest]
    ):
        if isinstance(input_data, Dict):
            # Implement the logic to optimize the topology based on the provided instructions
            input_data = OptimizeTopologyRequest(**input_data)
        parser = PydanticOutputParser(pydantic_object=OptimizeTopologyOutput)
        format_instructions = parser.get_format_instructions()

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            TOPOLOGY_OPTIMIZER_PROMPT
        )

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
                handle_parsing_errors=True,
                max_iterations=5,
                early_stopping_method="force",
            )

            try:
                agent_input = {
                    "world_id": input_data.world_id,
                    "optional_instructions": input_data.optional_instructions
                    or "None provided. Apply general optimization principles.",  # Provide default text if None
                    "format_instructions": format_instructions,
                    "world_instructions": WorldModal.schema_for_fields(),
                    "input": f"Optimize topology for world {input_data.world_id} with instructions: {input_data.optional_instructions or 'default principles'}",
                }
                result = agent_executor.invoke(agent_input)
                final_output_data = result.get("output")

                if isinstance(final_output_data, dict):
                    # Parse the dictionary into the Pydantic model for validation
                    parsed_output = OptimizeTopologyOutput.model_validate(
                        final_output_data
                    )
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
                            parsed_output = OptimizeTopologyOutput.model_validate_json(
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

    async def topology_qna(self, input_data: Union[Dict[str, Any], TopologyQnARequest]):
        if isinstance(input_data, Dict):
            # Implement the logic to optimize the topology based on the provided instructions
            input_data = TopologyQnARequest(**input_data)
        parser = PydanticOutputParser(pydantic_object=TopologyQnAOutput)
        format_instructions = parser.get_format_instructions()

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            TOPOLOGY_QNA_PROMPT
        )

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
                handle_parsing_errors=True,
                max_iterations=5,
                early_stopping_method="force",
            )

            try:
                agent_input = {
                    "world_id": input_data.world_id,
                    'topology_data': self._get_topology_by_world_id(input_data.world_id),
                    'conversation_id': input_data.conversation_id,
                    "optional_instructions": input_data.optional_instructions
                    or "None provided. Apply general optimization principles.",
                    "answer_instructions": format_instructions,
                    "world_instructions": WorldModal.schema_for_fields(),
                    'user_question': input_data.user_query,
                    'last_5_messages': self._get_chat_history(input_data.conversation_id, 5),
                    "input": f'Answer the following question about the topology of world {input_data.world_id}: {input_data.user_query}',
                }
                result = agent_executor.invoke(agent_input)
                final_output_data = result.get("output")

                if isinstance(final_output_data, dict):
                    # Parse the dictionary into the Pydantic model for validation
                    parsed_output = TopologyQnAOutput.model_validate(
                        final_output_data
                    )
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
                            parsed_output = TopologyQnAOutput.model_validate_json(
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
