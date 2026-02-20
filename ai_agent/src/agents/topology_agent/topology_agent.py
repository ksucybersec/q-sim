import json
from logging import getLogger
import traceback
from typing import Any, Dict, Union

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.topology_agent.examples import SYNTHESIZE_EXAMPLES, TOPOLOGY_OPTIMIZE_EXAMPLES
from ai_agent.src.agents.topology_agent.parser import convert_simplified_to_complex_with_layout
from ai_agent.src.agents.topology_agent.prompt import (
    TOPOLOGY_GENERATOR_AGENT,
    TOPOLOGY_OPTIMIZER_PROMPT,
    TOPOLOGY_QNA_PROMPT,
)
from ai_agent.src.agents.topology_agent.validator import validate_static_topology
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

            # First, validate using static validator (works on SimplifiedTopology)
            if result.success and isinstance(result.generated_topology, SimplifiedTopology):
                validated_response = validate_static_topology(result.generated_topology)

                if not validated_response['is_valid']:
                    if input_data['retry_count'] >= config.agents.agent_validation.max_retry:
                        result.success = False
                        result.error = "Max retry count reached."
                        result.overall_feedback = "Synthesis failed due to validation errors."
                        return result
                    input_data['regeneration_feedback'] = '\n'.join(validated_response['errors'])
                    input_data['retry_count'] += 1
                    return await self.run(task_id, input_data)

            # Then, if static validation passed, run validation agent (for LLM-based validation)
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

        with open('result.json', 'w') as f:
            json.dump({
                'input_data': input_data,
                'validated_output': validated_output,
            }, f, indent=4)

        if turn:
            finish_agent_turn(turn.pk, AgentExecutionStatus.SUCCESS, validated_output.copy())
            validated_output['message_id'] = turn.pk

            if task_id == AgentTaskType.SYNTHESIZE_TOPOLOGY:
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
            input_data = SynthesisTopologyRequest(**input_data)

        if self.config.dev.enable_mock_responses:
            with open("docs/sample_files/synthesis_topology_mock_response.json", "r") as f:
                json_str = f.read()
                json_obj = json.loads(json_str)
                return SynthesisTopologyOutput.model_validate(json_obj['action_input'])

        if not self.llm:
            raise LLMError("LLM not available")

        prompt = ChatPromptTemplate.from_messages([
            ("system", TOPOLOGY_GENERATOR_AGENT),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm.with_structured_output(SynthesisTopologyOutput)

        try:
            result = await chain.ainvoke({
                "user_instructions": input_data.user_query,
                "regeneration_feedback_from_validation": input_data.regeneration_feedback or "None — this is the first attempt.",
                "input": input_data.user_query,
            })

            if isinstance(result, SynthesisTopologyOutput):
                print("--- Synthesis Topology Proposal Generated ---")
                return result
            else:
                self.logger.error(f"Unexpected output type: {type(result)}")
                return None
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during synthesis!")
            raise LLMError(f"Error during synthesis: {e}")

    async def update_topology(
        self, input_data: Union[Dict[str, Any], OptimizeTopologyRequest]
    ):
        if isinstance(input_data, Dict):
            input_data = OptimizeTopologyRequest(**input_data)

        if self.config.dev.enable_mock_responses:
            with open("docs/sample_files/topology_optimizer_mock_response.json", "r") as f:
                json_str = f.read()
                json_obj = json.loads(json_str)
                return OptimizeTopologyOutput.model_validate(json_obj['action_input'])

        if not self.llm:
            raise LLMError("LLM not available")

        # Pre-fetch topology data instead of relying on agent tool call
        topology_data = self._get_topology_by_world_id(input_data.world_id)
        if not topology_data:
            raise ValueError(f"No topology found for world {input_data.world_id}")

        prompt = ChatPromptTemplate.from_messages([
            ("system", TOPOLOGY_OPTIMIZER_PROMPT),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm.with_structured_output(OptimizeTopologyOutput)

        try:
            result = await chain.ainvoke({
                "world_id": input_data.world_id,
                "optional_instructions": input_data.optional_instructions
                or "None provided. Apply general optimization principles.",
                "world_instructions": WorldModal.schema_for_fields(),
                "topology_data": json.dumps(topology_data),
                "input": f"Optimize topology for world {input_data.world_id} with instructions: {input_data.optional_instructions or 'default principles'}",
            })

            if isinstance(result, OptimizeTopologyOutput):
                print("--- Optimization Proposal Generated ---")
                return result
            else:
                self.logger.error(f"Unexpected output type: {type(result)}")
                return None
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during optimization!")
            raise LLMError(f"Error during optimization: {e}")

    async def topology_qna(self, input_data: Union[Dict[str, Any], TopologyQnARequest]):
        if isinstance(input_data, Dict):
            input_data = TopologyQnARequest(**input_data)
        
        if self.config.dev.enable_mock_responses:
            with open("docs/sample_files/topology_qna_mock_response.json", "r") as f:
                json_str = f.read()
                json_obj = json.loads(json_str)
                return TopologyQnAOutput.model_validate(json_obj['action_input'])

        if not self.llm:
            raise LLMError("LLM not available")

        # Pre-fetch all context
        topology_data = self._get_topology_by_world_id(input_data.world_id)
        chat_history = self._get_chat_history(input_data.conversation_id, 5)

        prompt = ChatPromptTemplate.from_messages([
            ("system", TOPOLOGY_QNA_PROMPT),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm.with_structured_output(TopologyQnAOutput)

        try:
            result = await chain.ainvoke({
                "world_id": input_data.world_id,
                "topology_data": json.dumps(topology_data) if topology_data else "No topology data available.",
                "world_instructions": WorldModal.schema_for_fields(),
                "user_question": input_data.user_query,
                "last_5_messages": chat_history,
                "input": f"Answer the following question about the topology of world {input_data.world_id}: {input_data.user_query}",
            })

            if isinstance(result, TopologyQnAOutput):
                print("--- Topology QnA Response Generated ---")
                return result
            else:
                self.logger.error(f"Unexpected output type: {type(result)}")
                return None
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during topology QnA!")
            raise LLMError(f"Error during topology QnA: {e}")
