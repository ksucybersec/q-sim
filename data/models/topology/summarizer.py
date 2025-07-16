
from typing import Any, Dict, Union
from data.models.topology.world_model import WorldModal


def generate_topology_summary(world: Union[WorldModal, Dict[str, Any]]) -> str:
    """
    Converts a WorldModal object into a concise natural language summary for an LLM.

    Args:
        world: The WorldModal instance representing the network topology.

    Returns:
        A string containing the human-readable summary.
    """

    if isinstance(world, dict):
        world = WorldModal(**world)

    summary_parts = []
    
    # 1. World-level summary
    summary_parts.append(
        f"The simulation world, named '{world.name}', contains {len(world.zones)} zone(s)."
    )

    # 2. Zone-level summary
    for zone in world.zones:
        summary_parts.append(
            f"\nWithin the '{zone.type}' zone named '{zone.name}':"
        )

        # 3. Network-level summary
        if not zone.networks:
            summary_parts.append("  - It contains no networks.")
        else:
            for network in zone.networks:
                network_type_str = "a Quantum Network" if network.type == "QUANTUM_NETWORK" else "a Classical Network"
                summary_parts.append(
                    f"  - It contains {network_type_str} named '{network.name}'."
                )

                # Summarize hosts by grouping them by type
                if network.hosts:
                    host_counts = {}
                    for host in network.hosts:
                        host_counts[host.type] = host_counts.get(host.type, 0) + 1
                    
                    host_summaries = []
                    for host_type, count in host_counts.items():
                        # Get names for this type
                        names = [h.name for h in network.hosts if h.type == host_type]
                        host_summaries.append(f"{count} {host_type}(s) (e.g., {', '.join(names[:3])})")

                    summary_parts.append(f"    - Hosts: {'; '.join(host_summaries)}.")
                else:
                    summary_parts.append("    - Hosts: This network has no hosts.")

                # Summarize connections
                if network.connections:
                    connection_descs = [
                        f"{c.from_node} to {c.to_node}" for c in network.connections
                    ]
                    summary_parts.append(
                        f"    - Connections: Links exist between {', '.join(connection_descs)}."
                    )
                else:
                    summary_parts.append("    - Connections: This network has no connections.")
    
        # 4. Adapter-level summary
        if zone.adapters:
            adapter_descs = [
                f"'{a.name}' which bridges the classical host '{a.classicalHost}' with the quantum host '{a.quantumHost}'"
                for a in zone.adapters
            ]
            summary_parts.append(
                f"  - Adapters: The zone includes {len(zone.adapters)} adapter(s): {'; '.join(adapter_descs)}."
            )
            
    return " ".join(summary_parts)
