from logging import getLogger
import traceback
from typing import Any, Dict, Union

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.topology_agent.structure import SynthesisTopologyOutput, SimplifiedTopology
from ai_agent.src.agents.topology_agent.validator import validate_static_topology
from ai_agent.src.agents.validation_agent.prompt import TOPOLOGY_VALIDATION_AGENT_PROMPT
from ai_agent.src.agents.validation_agent.structures import TopologyValidationResult, ValidationStatus
from ai_agent.src.agents.validation_agent.world_validation import validate_world_topology_static_logic
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMError
from data.models.topology.world_model import WorldModal


class ValidationAgent(BaseAgent):
    logger = getLogger(__name__)

    def __init__(self, llm: ChatOpenAI = None):
        super().__init__(
            agent_id=AgentType.VALIDATION_AGENT,
            description=f"""
                A validation agent that helps in validating network topologies.
                This can check if a topology meets certain criteria or is valid.
                """,
        )
        self.llm = llm

    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        pass


    def _register_tasks(self):
        return {
            AgentTaskType.VALIDATE_TOPOLOGY: AgentTask(
                task_id=AgentTaskType.VALIDATE_TOPOLOGY,
                description="Validate an existing network topology based on specific criteria or instructions.",
                input_schema=SynthesisTopologyOutput,
                output_schema=TopologyValidationResult,
                examples=[],
            ),
        }

    async def run(
        self, task_id: AgentTaskType, input_data: Dict[str, Any]
    ):
        if task_id == AgentTaskType.VALIDATE_TOPOLOGY:
            result = await self.validate_generated_topology(input_data["generate_response"])
        else:
            raise ValueError(f"Unsupported task type: {task_id}")
        
        # Validate output
        validated_output = self.validate_output(task_id, result)

        return validated_output
        

    async def validate_generated_topology(self, generate_response: Union[SynthesisTopologyOutput, Dict[str, Any]]) -> TopologyValidationResult:
        if isinstance(generate_response, Dict):
            generate_response = SynthesisTopologyOutput(**generate_response)

        # Handle static validation based on topology type
        # Static validation should already be done in topology_agent, but we check here as a safety net
        static_errors = []
        if isinstance(generate_response.generated_topology, SimplifiedTopology):
            # Use SimplifiedTopology validator
            validated_response = validate_static_topology(generate_response.generated_topology)
            if not validated_response['is_valid']:
                static_errors = validated_response['errors']
        elif isinstance(generate_response.generated_topology, WorldModal):
            # Use WorldModal validator
            static_errors = validate_world_topology_static_logic(generate_response.generated_topology)
        
        if static_errors:
            return TopologyValidationResult(
                validation_status=ValidationStatus.FAILED,
                static_errors=static_errors,
                summary=f"Static validation failed with {len(static_errors)} error(s)."
            )
        
        if not self.llm:
            raise LLMError("LLM not available")

        prompt = ChatPromptTemplate.from_messages([
            ("system", TOPOLOGY_VALIDATION_AGENT_PROMPT),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm.with_structured_output(TopologyValidationResult)

        try:
            result = await chain.ainvoke({
                'world_instructions': WorldModal.schema_for_fields(),
                "original_user_query": generate_response.input_query,
                "generated_topology_json": generate_response.generated_topology.model_dump_json(),
                "generating_agent_thought_process": generate_response.thought_process,
                'input': 'Validate the topology and provide feedback for the generating agent.',
            })

            if isinstance(result, TopologyValidationResult):
                print("--- Validation Result Generated ---")
                return result
            else:
                self.logger.error(f"Unexpected output type: {type(result)}")
                return None
        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during validation!")
            raise LLMError(f"Error during validation: {e}")