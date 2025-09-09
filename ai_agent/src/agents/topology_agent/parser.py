import math
import networkx as nx
from typing import Dict, Tuple
from ai_agent.src.agents.topology_agent.structure import (
    SimplifiedTopology,
    SynthesisTopologyOutput,
)
from data.models.topology.node_model import (
    AdapterModal,
    ConnectionModal,
    HostModal,
    NetworkModal,
)
from data.models.topology.world_model import WorldModal
from data.models.topology.zone_model import ZoneModal


def _calculate_graph_layout(simplified_topo: 'SimplifiedTopology', world_size: Tuple[float, float]) -> Dict[str, Tuple[float, float]]:
    """
    Uses a force-directed algorithm to calculate node positions, then normalizes
    and scales them to guarantee they are within the positive world boundaries.
    """
    G = nx.Graph()
    for node in simplified_topo.nodes:
        G.add_node(node.name)
    for from_node, to_node in simplified_topo.connections:
        G.add_edge(from_node, to_node)

    # Handle edge case of an empty graph
    if not G.nodes:
        return {}

    # 1. Get raw positions from the layout algorithm (can be negative)
    # The 'k' parameter helps in adjusting node spacing for better visuals.
    k_val = 0.8 / math.sqrt(G.number_of_nodes()) if G.number_of_nodes() > 0 else 0.8
    raw_pos = nx.spring_layout(G, k=k_val, iterations=150, seed=42)

    # 2. Normalize the positions to a [0, 1] range.
    # First, find the bounding box of the raw layout.
    if len(raw_pos) == 1: # Handle single-node case
        min_x, max_x, min_y, max_y = 0, 1, 0, 1
        x_coords, y_coords = [0.5], [0.5] # Center it
    else:
        x_coords = [pos[0] for pos in raw_pos.values()]
        y_coords = [pos[1] for pos in raw_pos.values()]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

    # Calculate the span (width/height of the raw layout)
    span_x = max_x - min_x
    span_y = max_y - min_y

    # Avoid division by zero if all nodes are on a single line
    if span_x == 0: span_x = 1
    if span_y == 0: span_y = 1
    
    normalized_pos = {}
    for node, (x, y) in raw_pos.items():
        # Apply normalization formula: (value - min) / span
        norm_x = (x - min_x) / span_x
        norm_y = (y - min_y) / span_y
        normalized_pos[node] = (norm_x, norm_y)

    # 3. Scale the normalized [0, 1] positions to the final world size with a margin.
    margin = 50.0
    width, height = world_size
    scaled_pos = {}
    for node, (norm_x, norm_y) in normalized_pos.items():
        scaled_pos[node] = (
            margin + norm_x * (width - 2 * margin),
            margin + norm_y * (height - 2 * margin)
        )
        
    return scaled_pos


def convert_simplified_to_complex_with_layout(
    synthesis_output: "SynthesisTopologyOutput",
) -> WorldModal:
    """
    Converts the simplified topology into the final complex WorldModal,
    programmatically generating all spatial data (positions and sizes).
    """
    simplified_topo = synthesis_output.generated_topology
    WORLD_SIZE = (1000.0, 1000.0)

    # --- 1. Calculate All Node Positions ---
    node_locations = _calculate_graph_layout(simplified_topo, WORLD_SIZE)

    # --- 2. Instantiate All Individual Components ---
    host_map: dict[str, HostModal] = {}
    network_map: dict[str, NetworkModal] = {}

    # Placeholder instantiation (location/size will be calculated later)
    for net_name, net_type in simplified_topo.networks:
        network_map[net_name] = NetworkModal(
            name=net_name, type=net_type, location=(0, 0),
            address=net_name, # Provide a default address
            hosts=[],                             # Provide an empty list
            connections=[]                        # Provide an empty list
        )

    for s_node in simplified_topo.nodes:
        location = node_locations.get(s_node.name, (0, 0))
        if s_node.type == "Adapter":
            # Find the classical and quantum hosts this adapter connects to
            classical_host, quantum_host = None, None
            node_types = {n.name: n.type for n in simplified_topo.nodes}
            for from_n, to_n in simplified_topo.connections:
                if from_n == s_node.name and "Adapter" not in node_types.get(to_n, ""):
                    if "Classical" in node_types.get(to_n, ""):
                        classical_host = to_n
                    if "Quantum" in node_types.get(to_n, ""):
                        quantum_host = to_n
                elif to_n == s_node.name and "Adapter" not in node_types.get(
                    from_n, ""
                ):
                    if "Classical" in node_types.get(from_n, ""):
                        classical_host = from_n
                    if "Quantum" in node_types.get(from_n, ""):
                        quantum_host = from_n

            host_map[s_node.name] = AdapterModal(
                name=s_node.name,
                location=location,
                address=s_node.name,
                classicalNetwork=s_node.classical_network,
                quantumNetwork=s_node.quantum_network,
                classicalHost=classical_host or "",
                quantumHost=quantum_host or "",
                type='QuantumAdapter'
            )
        else:  # Regular host
            host_map[s_node.name] = HostModal(
                name=s_node.name,
                type=s_node.type,
                location=location,
                address=s_node.name,
            )

    # --- 3. Assemble Hierarchy and Calculate Derived Properties ---

    # Place hosts into network models
    for s_node in simplified_topo.nodes:
        if s_node.type != "Adapter" and s_node.network in network_map:
            network_map[s_node.network].hosts.append(host_map[s_node.name])

    # Calculate network bounds and locations based on their nodes' positions
    for net in network_map.values():
        if not net.hosts:
            continue
        min_x = min(h.location[0] for h in net.hosts)
        max_x = max(h.location[0] for h in net.hosts)
        min_y = min(h.location[1] for h in net.hosts)
        max_y = max(h.location[1] for h in net.hosts)
        net.location = ((min_x + max_x) / 2, (min_y + max_y) / 2)

    # Create ConnectionModals and assign them to networks
    for from_name, to_name in simplified_topo.connections:
        from_node, to_node = host_map[from_name], host_map[to_name]
        dist = math.hypot(
            from_node.location[0] - to_node.location[0],
            from_node.location[1] - to_node.location[1],
        )
        is_quantum = (
            "Quantum" in from_node.type
            or "Quantum" in to_node.type
            or "Adapter" in from_node.type
        )

        new_connection = ConnectionModal(
            from_node=from_name,
            to_node=to_name,
            name=f"{from_name}-{to_name}",
            length=dist / 1000.0,
            bandwidth=999999999,
            latency=0,
            noise_model="none",
            loss_per_km=0,
            packet_loss_rate=0,
            packet_error_rate=0,
            mtu=9999999999
        )

        # Assign connection to a network (logic can be improved, e.g., based on adapter links)
        from_s_node = next(
            (n for n in simplified_topo.nodes if n.name == from_name), None
        )
        if from_s_node and from_s_node.network in network_map:
            network_map[from_s_node.network].connections.append(new_connection)
        elif (
            from_s_node
            and from_s_node.type == "Adapter"
            and from_s_node.classical_network in network_map
        ):
            network_map[from_s_node.classical_network].connections.append(
                new_connection
            )

    # --- 4. Build Final Zone and World Models ---
    world_zones = []
    for s_zone in simplified_topo.zones:
        zone_networks = [
            network_map[net_name]
            for net_name in s_zone.networks
            if net_name in network_map
        ]
        zone_adapters = [
            host
            for host in host_map.values()
            if isinstance(host, AdapterModal)
            and (
                host.classicalNetwork in s_zone.networks
                or host.quantumNetwork in s_zone.networks
            )
        ]

        # Calculate zone bounds from the networks within it
        if not zone_networks:
            continue
        all_hosts_in_zone = [
            h for net in zone_networks for h in net.hosts
        ] + zone_adapters
        if not all_hosts_in_zone:
            continue

        min_x = min(h.location[0] for h in all_hosts_in_zone) - 20  # Add padding
        max_x = max(h.location[0] for h in all_hosts_in_zone) + 20
        min_y = min(h.location[1] for h in all_hosts_in_zone) - 20
        max_y = max(h.location[1] for h in all_hosts_in_zone) + 20

        world_zones.append(
            ZoneModal(
                name=s_zone.name,
                networks=zone_networks,
                adapters=zone_adapters,
                position=(min_x, min_y),
                size=(max_x - min_x, max_y - min_y),
                type='SECURE'
            )
        )

    return WorldModal(
        name=simplified_topo.world_name,
        size=WORLD_SIZE,
        owner=(
            synthesis_output.owner if hasattr(synthesis_output, "owner") else "Default"
        ),
        zones=world_zones,
    )
