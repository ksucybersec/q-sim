from typing import Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field

from ai_agent.src.agents.base.base_structures import BaseAgentInput, BaseAgentOutput
from data.models.topology.world_model import WorldModal


class OptimizeTopologyRequest(BaseAgentInput):
    world_id: str = Field(description="The ID of the world to optimize.")
    optional_instructions: Optional[str] = Field(
        description="Optional instructions for the optimization process."
    )


class OptimizeStep(BaseModel):
    change_path: List[str] = Field(description="JSON path(s) changed in the network.")
    change: str = Field(description="Change made to the topology.")
    reason: str = Field(description="Reason for the change.")
    citation: Optional[List[str]] = Field(
        description="External/Internal citation supporting the reason."
    )
    comments: Optional[str] = Field(
        description="Additional comments about the optimization process."
    )


class OptimizeTopologyOutput(BaseAgentOutput):
    error: Optional[str] = Field(description="Error message if any occurred during the optimization.")
    success: bool = Field(description="Indicates whether the optimization was successful.", default=True)
    original_topology: WorldModal = Field(
        description="The original network topology before optimization."
    )
    optimized_topology: WorldModal = Field(
        description="The optimized network topology."
    )
    overall_feedback: str = Field(
        description="Overall feedback on the current topology."
    )
    cost: float = Field(description="The cost of the optimized topology.")
    optimization_steps: List[OptimizeStep] = Field(
        description="Steps taken during the optimization process."
    )

class SynthesisTopologyRequest(BaseAgentInput):
    user_query: str = Field(description="Instructions for optimizing the topology.")
    regeneration_feedback: Optional[str] = Field(
        None,
        description=(
            "Optional consolidated feedback and specific instructions from a prior validation step, "
            "to be used by the Topology Generator Agent if this is a retry attempt. "
            "This feedback aims to guide the agent towards correcting previously identified issues "
            "or clarifying ambiguities from the original user_query."
        )
    )

class SynthesisTopologyOutput(BaseAgentOutput):
    error: Optional[str] = Field(description="Error message if any occurred during the synthesis.")
    success: bool = Field(description="Indicates whether the synthesis was successful.", default=True)
    # generated_topology: WorldModal = Field(
    #     description="The synthesized network topology."
    # )
    generated_topology: Union['SimplifiedTopology', 'WorldModal'] = Field(
        description="The synthesized network topology."
    )
    overall_feedback: str = Field(description="Overall feedback on the current topology.")
    cost: float = Field(description="The cost of the synthesized topology.")
    thought_process: List[str] = Field(
        description="Thought process leading to the synthesis.",
        default=[]
    )
    input_query: str = Field(description="The original user query.")

    
SimplifiedConnectionArray = Tuple[
    str,  # from_node
    str   # to_node
]
"""
A compact array representing a connection between two nodes.
The connection type (classical/quantum) is inferred by the application based on the types of the connected nodes.
- Element 0: The 'name' of the starting node.
- Element 1: The 'name' of the ending node.
"""

SimplifiedNetworkArray = Tuple[
    str,                                       # name
    Literal["CLASSICAL_NETWORK", "QUANTUM_NETWORK"] # type
]
"""
A compact array representing a logical network.
- Element 0: The unique 'name' of the network.
- Element 1: The fundamental 'type' of the network.
"""


# --- Core Pydantic Models ---

class SimplifiedNode(BaseModel):
    """
    A single, simplified representation for any node in the topology (e.g., a host, router, or adapter).
    This model uses an object structure because its fields are conditional.
    """
    name: str = Field(
        description="The unique name for this node, used as a reference by connections."
    )
    type: Literal["ClassicalHost", "ClassicalRouter", "QuantumHost", "QuantumRepeater", "Adapter"] = Field(
        description="The fundamental type of the node, which dictates its behavior and connectivity rules."
    )
    
    network: Optional[str] = Field(
        default=None,
        description="For standard nodes (hosts, repeaters, routers), this is the name of the network they belong to."
    )
    
    classical_network: Optional[str] = Field(
        default=None,
        description="For 'Adapter' nodes only. The name of the classical network this adapter connects to."
    )
    quantum_network: Optional[str] = Field(
        default=None,
        description="For 'Adapter' nodes only. The name of the quantum network this adapter connects to."
    )


class SimplifiedZone(BaseModel):
    """
    A high-level container for grouping networks. Its properties define a bounding box for layout purposes.
    """
    name: str = Field(
        description="The unique name of the zone."
    )
    # size: Tuple[float, float] = Field(
    #     description="The (width, height) dimensions of the zone's bounding box."
    # )
    # position: Tuple[float, float] = Field(
    #     description="The (x, y) coordinates of the top-left corner of the zone's bounding box within the world."
    # )
    networks: List[str] = Field(
        description="A list of network names that are contained within this zone."
    )


class SimplifiedTopology(BaseModel):
    """
    The root model for the simplified topology that the LLM will generate.
    It uses a flat, token-efficient structure that is easy for an application to parse and expand into a detailed final model.
    """
    world_name: str = Field(
        description="The name of the entire simulation world."
    )
    # world_size: Tuple[float, float] = Field(
    #     description="The total (width, height) of the simulation canvas."
    # )
    
    nodes: List[SimplifiedNode] = Field(
        description="A flat list of all nodes (hosts, adapters, etc.) in the topology."
    )
    connections: List[SimplifiedConnectionArray] = Field(
        description="A list of all connections in the topology, represented as compact [from, to] arrays."
    )
    networks: List[SimplifiedNetworkArray] = Field(
        description="A list of all logical networks in the topology, represented as compact [name, type] arrays."
    )
    zones: List[SimplifiedZone] = Field(
        description="A list of all zones used to group networks and define high-level layout."
    )


# ----------------------------------------------------------------------------




class TopologyQnARequest(BaseAgentInput):
    user_query: str = Field(description="Instructions for optimizing the topology.")
    world_id: str = Field(description="The ID of the world to optimize.")
    optional_instructions: Optional[str] = Field(
        description="Optional instructions for the optimization process."
    )

class RelevantTopologyPart(BaseModel):
    path: str
    snippet: Optional[Union[str, Dict, List]]


class TopologyQnAOutput(BaseModel):
    status: Literal["answered", "clarification_needed", "error", "unanswerable"] = Field(description="The outcome status of the QnA attempt.")
    answer: str = Field(description="The natural language answer if status is 'answered'; the clarifying question if status is 'clarification_needed'; or an error/unanswerable message if status is 'error' or 'unanswerable'.")
    relevant_topology_parts: Optional[List[RelevantTopologyPart]] = Field(None, description="List of references to specific parts of the topology data that support the answer, only if status is 'answered'.")
    error_message: Optional[str] = Field(None, description="Specific error details if status is 'error'.")