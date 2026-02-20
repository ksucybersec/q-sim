from typing import List, Dict, Set, Tuple
from pydantic import BaseModel
from typing import TYPE_CHECKING

from ai_agent.src.agents.topology_agent.structure import SimplifiedTopology, SimplifiedNode

# --- 1. Helper Functions (Graph Utilities) ---

def build_adjacency_list(topology: SimplifiedTopology) -> Dict[str, List[str]]:
    """
    Converts connection list [["A", "B"], ...] into an adjacency dict {"A": ["B"], "B": ["A"]}.
    """
    adj = {n.name: [] for n in topology.nodes}
    for conn in topology.connections:
        if len(conn) == 2:
            u, v = conn[0], conn[1]
            if u in adj: adj[u].append(v)
            if v in adj: adj[v].append(u)
    return adj

def get_node_map(topology: SimplifiedTopology) -> Dict[str, SimplifiedNode]:
    """Creates a fast lookup dictionary for nodes by name."""
    return {n.name: n for n in topology.nodes}

def is_reachable(start_node_name: str, target_type: str, adj: Dict, node_map: Dict) -> bool:
    """
    Performs a DFS to see if 'start_node' can reach any node of 'target_type'.
    Used to check if a Quantum node eventually hits a ClassicalHost.
    """
    stack = [start_node_name]
    visited = set()
    
    while stack:
        curr = stack.pop()
        if curr in visited:
            continue
        visited.add(curr)
        
        if node_map[curr].type == target_type:
            return True
        
        for neighbor in adj.get(curr, []):
            if neighbor not in visited:
                stack.append(neighbor)
    return False

# --- 2. Rule Check Functions ---

def check_node_types(topology: 'SimplifiedTopology') -> List[str]:
    """
    Rule 1: Component Integrity.
    Verifies valid types and that Adapters have both network attributes defined.
    """
    valid_types = {"ClassicalHost", "ClassicalRouter", "QuantumHost", "QuantumRepeater", "Adapter"}
    errors = []
    
    for node in topology.nodes:
        if node.type not in valid_types:
            errors.append(f"Node '{node.name}' has invalid type '{node.type}'.")
        
        # Specific Check: Adapter must act as a bridge
        if node.type == "Adapter":
            if not node.classical_network or not node.quantum_network:
                errors.append(f"Adapter '{node.name}' is missing network config (needs classical_network & quantum_network).")
    return errors

def check_connection_physics(adj: Dict, node_map: Dict) -> List[str]:
    """
    Rule 3: Layer Separation.
    Ensures Classical nodes don't touch Quantum nodes directly, and Adapters don't touch Adapters.
    """
    errors = []
    classical_types = {"ClassicalHost", "ClassicalRouter"}
    quantum_types = {"QuantumHost", "QuantumRepeater"}
    
    for u_name, neighbors in adj.items():
        u_node = node_map.get(u_name)
        if not u_node: continue
        
        for v_name in neighbors:
            v_node = node_map.get(v_name)
            
            # 1. Classical <-> Quantum Violation
            if u_node.type in classical_types and v_node.type in quantum_types:
                errors.append(f"Physics Violation: Classical '{u_name}' connected directly to Quantum '{v_name}'.")
            
            # 2. Adapter <-> Adapter Violation
            if u_node.type == "Adapter" and v_node.type == "Adapter":
                errors.append(f"Logic Error: Direct Adapter-to-Adapter connection between '{u_name}' and '{v_name}'.")
                
    return errors

def check_port_constraints(adj: Dict, node_map: Dict) -> List[str]:
    """
    Rule 2 & 5: Hardware Port Limits.
    Enforces strict point-to-point logic for Quantum components.
    """
    errors = []
    
    for name, neighbors in adj.items():
        node = node_map[name]
        degree = len(neighbors)
        neighbor_types = [node_map[n].type for n in neighbors]

        # Case A: QuantumHost (Strictly 2 connections: 1 Adapter, 1 Link)
        if node.type == "QuantumHost":
            if degree != 2:
                errors.append(f"Port Error: QHost '{name}' has {degree} connections. Must be exactly 2.")
            else:
                adapter_count = neighbor_types.count("Adapter")
                quantum_link_count = sum(1 for t in neighbor_types if t in ["QuantumHost", "QuantumRepeater"])
                
                if adapter_count != 1:
                    errors.append(f"Wiring Error: QHost '{name}' must have exactly 1 Adapter connection, but has {adapter_count}.")
                if quantum_link_count != 1:
                    errors.append(f"Wiring Error: QHost '{name}' must have exactly 1 quantum link connection (to QuantumHost or QuantumRepeater), but has {quantum_link_count}.")

        # Case B: Adapter (Strictly 2 connections: 1 Classical, 1 Quantum)
        elif node.type == "Adapter":
            if degree != 2:
                errors.append(f"Port Error: Adapter '{name}' has {degree} connections. Must be exactly 2.")
            else:
                has_classical = any(t in ["ClassicalHost", "ClassicalRouter"] for t in neighbor_types)
                has_quantum = "QuantumHost" in neighbor_types
                if not (has_classical and has_quantum):
                    errors.append(f"Wiring Error: Adapter '{name}' must connect to 1 Classical and 1 Quantum node.")

        # Case C: QuantumRepeater (Strictly 2 connections: Daisy Chain)
        elif node.type == "QuantumRepeater":
            if degree != 2:
                errors.append(f"Port Error: QRepeater '{name}' has {degree} connections. Must be strictly 2.")
                
    return errors

def check_termination(topology: 'SimplifiedTopology', adj: Dict, node_map: Dict) -> List[str]:
    """
    Rule 4: Termination.
    Ensures no Quantum component is left dangling. It must eventually reach a ClassicalHost.
    """
    errors = []
    quantum_types = {"QuantumHost", "QuantumRepeater", "Adapter"}
    
    for node in topology.nodes:
        if node.type in quantum_types:
            # Check if this node can walk the graph to find a "ClassicalHost"
            if not is_reachable(node.name, "ClassicalHost", adj, node_map):
                errors.append(f"Termination Error: Node '{node.name}' is isolated. Cannot reach a Classical Host.")
    return errors

# --- 3. Main Validator Function ---

def validate_static_topology(topology: SimplifiedTopology) -> Dict:
    """
    Master function to validate a generated topology against QUINTET rules.
    Returns a dictionary with 'is_valid' (bool) and 'errors' (list of strings).
    """
    # 1. Setup Graph Data
    node_map = get_node_map(topology)
    adj = build_adjacency_list(topology)
    all_errors = []

    # 2. Run All Checks
    all_errors.extend(check_node_types(topology))
    
    # Only proceed with graph checks if basic types are valid
    if not all_errors: 
        all_errors.extend(check_connection_physics(adj, node_map))
        all_errors.extend(check_port_constraints(adj, node_map))
        all_errors.extend(check_termination(topology, adj, node_map))

    # 3. Compile Result
    # Deduplicate errors just in case
    unique_errors = list(dict.fromkeys(all_errors))
    
    return {
        "is_valid": len(unique_errors) == 0,
        "errors": unique_errors,
        "topology_name": topology.world_name
    }