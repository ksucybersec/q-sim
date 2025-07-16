from abc import ABC, abstractmethod
import json
import logging
import pprint
from typing import Dict, Any, List, Optional, Union
from typing import Dict, Any, List, Optional, Union, Type
from pydantic import BaseModel, Field
import traceback
from langchain.tools import StructuredTool

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.consts.agent_type import AgentType
from data.embedding.embedding_util import EmbeddingUtil
from data.embedding.vector_log import VectorLogEntry
from data.models.conversation.conversation_model import HistoryItem
from data.models.conversation.conversation_ops import get_conversation_history
from data.models.simulation.simulation_model import get_simulation
from data.models.topology.world_model import get_topology_from_redis


class AgentInputSchema(BaseModel):
    """Base schema for agent inputs."""

    pass


class AgentOutputSchema(BaseModel):
    """Base schema for agent outputs."""

    pass


class AgentTask(BaseModel):
    """Definition of a task that an agent can perform."""

    task_id: AgentTaskType
    description: str
    input_schema: Union[Type[BaseModel], Dict[str, Any]]
    output_schema: Union[Type[BaseModel], Dict[str, Any]]
    examples: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    def get_model_description(self) -> str:
        """Generate a description of the input and output models."""
        return f"""
        Task: {self.task_id.value}
        Description: {self.description}
        Input: {self.input_schema.model_json_schema()}
        Output: {self.output_schema.model_json_schema()}
        
        Examples: {self.examples}
        """


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, agent_id: AgentType, description: str):
        self.logger = logging.getLogger(f"Agent {__class__.__name__}")
        self.agent_id = agent_id.value
        self.description = description
        self.tasks = self._register_tasks()

        self._get_relevant_logs_tool = StructuredTool.from_function(
            func=self._get_relevant_logs,
            name="_get_relevant_logs",
            description="Retrieve relevant logs for analysis",
        )

        self._get_topology_by_simulation_tool = StructuredTool.from_function(
            func=self._get_topology_by_simulation,
            name="_get_topology_by_simulation",
            description="Retrieves the detailed network topology configuration for a given simulation ID.",
        )

        self._get_topology_by_world_id_tool = StructuredTool.from_function(
            func=self._get_topology_by_world_id,
            name="_get_topology_by_world_id",
            description="Retrieves the detailed network topology configuration for a given world ID.",
        )
        self._get_chat_history_tool = StructuredTool.from_function(
            func=self._get_chat_history,
            name="_get_chat_history",
            description="Retrieves the chat history for a given conversation ID.",
        )
        self.tools = [
            self._get_relevant_logs_tool,
            self._get_topology_by_simulation_tool,
            self._get_topology_by_world_id_tool,
            self._get_chat_history_tool,
        ]

        self.embedding_util = EmbeddingUtil()

    @abstractmethod
    def _register_tasks(self) -> Dict[str, AgentTask]:
        """Register all tasks this agent can perform."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Return information about this agent's capabilities."""
        return {
            "agent_id": self.agent_id,
            "description": self.description,
            "tasks": [
                f"{task.get_model_description()}"
                for task_id, task in self.tasks.items()
            ],
        }

    def get_task_details(self, task_id: str) -> Optional[AgentTask]:
        """Get detailed information about a specific task."""
        return self.tasks.get(task_id)

    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message sent directly to this agent."""
        pass

    @abstractmethod
    async def run(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task with the given input data."""
        pass

    def validate_input(
        self, task_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate input data against the task's input schema."""
        task = self.get_task_details(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not supported by this agent")

        # Validate using Pydantic
        if isinstance(input_data, task.input_schema):
            validated = input_data
        elif isinstance(input_data, dict):
            validated = task.input_schema(**input_data)
        return validated.model_dump()

    def validate_output(
        self, task_id: str, output_data: Union[Dict[str, Any], BaseModel]
    ) -> Dict[str, Any]:
        """Validate output data against the task's output schema."""
        task = self.get_task_details(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not supported by this agent")

        if isinstance(output_data, BaseModel):
            if not isinstance(output_data, task.output_schema):
                raise Exception(
                    f"output_data is of type {type(output_data)}, expected type ({task.output_schema})"
                )
            else:
                return output_data.model_dump()
        elif isinstance(output_data, dict):
            # Validate using Pydantic
            validated = task.output_schema(**output_data)
            return validated.model_dump()
        elif isinstance(output_data, task.output_schema):
            return output_data.model_dump()
        else:
            print(f"Unsupported output data type: {type(output_data)}")
            print(
                f"""
            ===================
            Output Data:
            ===================
            {output_data}
            ===================
            """
            )
            traceback.print_exc()
            raise ValueError("Unsupported output data type")

    def save_agent_response(self, response):
        try:
            with open(f"{self.agent_id}_response.json", "w") as f:
                json.dump(response, f, indent=4, sort_keys=True)
        except Exception as e:
            logging.error(f"Error saving agent response: {e}")
            print(traceback.print_exc())

            try:
                pprint(response)
            except Exception:
                print(response)

    # =================== BASE TOOLS ======================
    def _get_relevant_logs(
        self, simulation_id: str, query: Optional[str] = "*", limit: int = 100
    ):
        """Retrieve logs relevant to a question using vector similarity"""
        if query == "*":
            return VectorLogEntry.get_by_simulation(simulation_id)

        # Generate embedding for query
        query_embedding = self.embedding_util.generate_embedding(query)

        # Search for relevant logs
        return VectorLogEntry.search_similar(
            query_embedding, top_k=limit, filters={"simulation_id": simulation_id}
        )

    def _get_topology_by_simulation(self, simulation_id: str):
        """Retrieve the topology of a simulation using vector similarity"""
        self.logger.debug(f"Retrieving topology for simulation {simulation_id}")
        simulation = get_simulation(simulation_id)
        if not simulation:
            return None

        world = get_topology_from_redis(simulation.world_id)
        if not world:
            return None
        return world.model_dump()

    def _get_topology_by_world_id(self, world_id: str):
        """Retrieve the topology of a world using vector similarity"""
        self.logger.debug(f"Retrieving topology for world {world_id}")
        world = get_topology_from_redis(world_id)
        if not world:
            self.logger.error(f"No topology found for world {world_id}")
            return None
        return world.model_dump()

    def _get_chat_history(
        self, conversation_id: str, limit: int = 10, skip: int = 0
    ) -> str:
        self.logger.debug(
            f"Retrieving {limit} chat history (after skipping {skip}) for conversation {conversation_id}"
        )
        paginated_history = get_conversation_history(
            conversation_id, limit=limit, skip=skip
        )

        message_history = "\n".join(
            map(lambda x: x.model_dump_json(), paginated_history)
        )

        return message_history
