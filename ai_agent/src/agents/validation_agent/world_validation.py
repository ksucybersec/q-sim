
from typing import Dict, List, Set, Tuple
from data.models.topology.node_model import HostModal, NetworkModal
from data.models.topology.world_model import WorldModal


def _add_error(errors_list: List[str], context: str, item_identifier: str, issue: str):
    """Helper to format and add error messages."""
    errors_list.append(f"[{context}] '{item_identifier}': {issue}")


def _validate_uniqueness(world: WorldModal, errors: List[str]):
    """
    Validates uniqueness constraints for names and addresses.
    - Zone names unique globally.
    - Network names unique within a zone.
    - Adapter names unique within a zone.
    - Host names unique within a network.
    - Connection names unique within a network.
    - Addresses (Host, Adapter, Network) unique globally where defined.
    """
    zone_names: Set[str] = set()
    all_host_addresses: Set[str] = set()
    all_adapter_addresses: Set[str] = set()
    all_network_addresses: Set[str] = set()

    for zone in world.zones:
        # Zone name uniqueness
        if zone.name in zone_names:
            _add_error(errors, "Uniqueness-Zone", zone.name, "Duplicate zone name.")
        zone_names.add(zone.name)

        network_names_in_zone: Set[str] = set()
        adapter_names_in_zone: Set[str] = set()

        for network in zone.networks:
            # Network name uniqueness (within zone)
            if network.name in network_names_in_zone:
                _add_error(errors, f"Uniqueness-Network (Zone {zone.name})", network.name, "Duplicate network name within this zone.")
            network_names_in_zone.add(network.name)

            if network.address and network.address in all_network_addresses:
                _add_error(errors, f"Uniqueness-NetworkAddress (Zone {zone.name})", network.name, f"Address '{network.address}' is already in use.")
            if network.address:
                all_network_addresses.add(network.address)

            host_names_in_network: Set[str] = set()
            connection_names_in_network: Set[str] = set()
            for host in network.hosts:
                # Host name uniqueness (within network)
                if host.name in host_names_in_network:
                    _add_error(errors, f"Uniqueness-Host (Network {network.name}, Zone {zone.name})", host.name, "Duplicate host name within this network.")
                host_names_in_network.add(host.name)

                if host.address and host.address in all_host_addresses:
                    _add_error(errors, f"Uniqueness-HostAddress (Network {network.name}, Zone {zone.name})", host.name, f"Address '{host.address}' is already in use.")
                if host.address:
                    all_host_addresses.add(host.address)

            for connection in network.connections:
                # Connection name uniqueness (within network)
                if connection.name in connection_names_in_network:
                     _add_error(errors, f"Uniqueness-Connection (Network {network.name}, Zone {zone.name})", connection.name, "Duplicate connection name within this network.")
                connection_names_in_network.add(connection.name)


        for adapter in zone.adapters:
            # Adapter name uniqueness (within zone)
            if adapter.name in adapter_names_in_zone:
                _add_error(errors, f"Uniqueness-Adapter (Zone {zone.name})", adapter.name, "Duplicate adapter name within this zone.")
            adapter_names_in_zone.add(adapter.name)

            if adapter.address and adapter.address in all_adapter_addresses:
                 _add_error(errors, f"Uniqueness-AdapterAddress (Zone {zone.name})", adapter.name, f"Address '{adapter.address}' is already in use.")
            if adapter.address:
                all_adapter_addresses.add(adapter.address)


def _validate_referential_integrity(world: WorldModal, errors: List[str]):
    """
    Validates that all references between entities are valid.
    - Connection from/to_node must exist in the same network.
    - Adapter's classical/quantum hosts and networks must exist and be consistent.
    """
    for zone_idx, zone in enumerate(world.zones):
        zone_context = f"Zone '{zone.name}' (idx {zone_idx})"

        # Create a map of networks and their hosts within this zone for quick lookup
        networks_in_zone: Dict[str, NetworkModal] = {net.name: net for net in zone.networks}
        hosts_in_networks_in_zone: Dict[Tuple[str, str], HostModal] = {} # (network_name, host_name) -> HostModal
        for net_name, network_obj in networks_in_zone.items():
            for host in network_obj.hosts:
                hosts_in_networks_in_zone[(net_name, host.name)] = host

        for net_idx, network in enumerate(zone.networks):
            network_context = f"Network '{network.name}' (idx {net_idx}, {zone_context})"
            hosts_in_current_network: Set[str] = {host.name for host in network.hosts}

            for conn_idx, connection in enumerate(network.connections):
                conn_context = f"Connection '{connection.name}' (idx {conn_idx}, {network_context})"
                if connection.from_node not in hosts_in_current_network:
                    _add_error(errors, conn_context, connection.from_node, "from_node does not refer to a host in this network.")
                if connection.to_node not in hosts_in_current_network:
                    _add_error(errors, conn_context, connection.to_node, "to_node does not refer to a host in this network.")
                if connection.from_node == connection.to_node:
                    _add_error(errors, conn_context, connection.from_node, "Connection cannot connect a node to itself.")

        for adapter_idx, adapter in enumerate(zone.adapters):
            adapter_context = f"Adapter '{adapter.name}' (idx {adapter_idx}, {zone_context})"

            # Check classical network and host
            classical_net_name = adapter.classicalNetwork
            if classical_net_name not in networks_in_zone:
                _add_error(errors, adapter_context, classical_net_name, "Referenced classicalNetwork not found in this zone.")
            else:
                if (classical_net_name, adapter.classicalHost) not in hosts_in_networks_in_zone:
                    _add_error(errors, adapter_context, adapter.classicalHost, f"Referenced classicalHost not found in classicalNetwork '{classical_net_name}'.")

            # Check quantum network and host
            quantum_net_name = adapter.quantumNetwork
            if quantum_net_name not in networks_in_zone:
                _add_error(errors, adapter_context, quantum_net_name, "Referenced quantumNetwork not found in this zone.")
            else:
                if (quantum_net_name, adapter.quantumHost) not in hosts_in_networks_in_zone:
                    _add_error(errors, adapter_context, adapter.quantumHost, f"Referenced quantumHost not found in quantumNetwork '{quantum_net_name}'.")


def _validate_spatial_logic(world: WorldModal, errors: List[str]):
    """
    Validates spatial constraints and containment.
    - World size positive.
    - Zones fit within the world and have positive size.
    - Adapters and Hosts are located within their parent zone's boundaries.
    - Locations/positions are non-negative.
    """
    world_context = f"World '{world.name}'"
    if world.size[0] <= 0 or world.size[1] <= 0:
        _add_error(errors, world_context, "size", f"World size dimensions ({world.size}) must be positive.")

    for zone_idx, zone in enumerate(world.zones):
        zone_context = f"Zone '{zone.name}' (idx {zone_idx})"

        # Zone size and position
        if zone.size[0] <= 0 or zone.size[1] <= 0:
            _add_error(errors, zone_context, "size", f"Zone size dimensions ({zone.size}) must be positive.")
        if zone.position[0] < 0 or zone.position[1] < 0:
            _add_error(errors, zone_context, "position", f"Zone position coordinates ({zone.position}) must be non-negative.")

        # Zone containment in world
        if (zone.position[0] + zone.size[0] > world.size[0] or
            zone.position[1] + zone.size[1] > world.size[1]):
            _add_error(errors, zone_context, "boundaries", f"Zone (pos {zone.position}, size {zone.size}) exceeds world boundaries ({world.size}).")

        for net_idx, network in enumerate(zone.networks):
            network_context = f"Network '{network.name}' (idx {net_idx}, {zone_context})"
            if network.location[0] < 0 or network.location[1] < 0:
                 _add_error(errors, network_context, "location", f"Network location coordinates ({network.location}) must be non-negative.")
            # Network location within zone (conceptual, as network itself doesn't have a size)
            if (network.location[0] < zone.position[0] or
                network.location[1] < zone.position[1] or
                network.location[0] > zone.position[0] + zone.size[0] or
                network.location[1] > zone.position[1] + zone.size[1]):
                 _add_error(errors, network_context, "location", f"Network location ({network.location}) is outside its zone boundaries (pos {zone.position}, size {zone.size}).")


            for host_idx, host in enumerate(network.hosts):
                host_context = f"Host '{host.name}' (idx {host_idx}, {network_context})"
                if host.location[0] < 0 or host.location[1] < 0:
                    _add_error(errors, host_context, "location", f"Host location coordinates ({host.location}) must be non-negative.")
                if (host.location[0] < zone.position[0] or
                    host.location[1] < zone.position[1] or
                    host.location[0] > zone.position[0] + zone.size[0] or
                    host.location[1] > zone.position[1] + zone.size[1]):
                    _add_error(errors, host_context, "location", f"Host location ({host.location}) is outside its zone boundaries (pos {zone.position}, size {zone.size}).")

        for adapter_idx, adapter in enumerate(zone.adapters):
            adapter_context = f"Adapter '{adapter.name}' (idx {adapter_idx}, {zone_context})"
            if adapter.location[0] < 0 or adapter.location[1] < 0:
                _add_error(errors, adapter_context, "location", f"Adapter location coordinates ({adapter.location}) must be non-negative.")
            if (adapter.location[0] < zone.position[0] or
                adapter.location[1] < zone.position[1] or
                adapter.location[0] > zone.position[0] + zone.size[0] or
                adapter.location[1] > zone.position[1] + zone.size[1]):
                 _add_error(errors, adapter_context, "location", f"Adapter location ({adapter.location}) is outside its zone boundaries (pos {zone.position}, size {zone.size}).")
    
    # Zone overlap (optional, more complex to implement efficiently)
    # For N zones, this is O(N^2).
    # For each pair of zones (zone_i, zone_j where i < j):
    #   rect1 = (zone_i.position[0], zone_i.position[1], zone_i.size[0], zone_i.size[1])
    #   rect2 = (zone_j.position[0], zone_j.position[1], zone_j.size[0], zone_j.size[1])
    #   If rect1 overlaps rect2:
    #     _add_error(errors, f"Spatial-ZoneOverlap", f"{zone_i.name} and {zone_j.name}", "Zones spatially overlap.")


def _validate_type_consistency(world: WorldModal, errors: List[str]):
    """
    Validates type consistency between related entities.
    - Adapter's classicalNetwork is CLASSICAL_NETWORK, quantumNetwork is QUANTUM_NETWORK.
    - Adapter's classicalHost is classical type, quantumHost is quantum type.
    - Hosts in CLASSICAL_NETWORK are classical types, hosts in QUANTUM_NETWORK are quantum types.
    - HostModal.type should not be abstract types like 'ClassicalNetwork' or 'Zone'.
    """
    classical_host_types = {"ClassicalHost", "ClassicalRouter", "InternetExchange", "ClassicToQuantumConverter"} # Add others as needed
    quantum_host_types = {"QuantumHost", "QuantumRepeater", "QuantumToClassicConverter"} # Add others as needed
    # 'QuantumAdapter' is a type for HostModal in HOST_TYPES, but we have AdapterModal.
    # This suggests a HostModal should not typically be of type 'QuantumAdapter'.
    # It could represent the physical presence of an adapter *as a host node* in a network.
    # If so, then classical_host_types and quantum_host_types might include 'QuantumAdapter'
    # depending on which side of the adapter is being represented as a host.
    # For simplicity, let's assume 'QuantumAdapter' host type is for hosts that *are* adapters.

    problematic_host_types = {"ClassicalNetwork", "Zone"}

    for zone_idx, zone in enumerate(world.zones):
        zone_context = f"Zone '{zone.name}' (idx {zone_idx})"
        networks_in_zone: Dict[str, NetworkModal] = {net.name: net for net in zone.networks}
        hosts_in_networks_in_zone: Dict[Tuple[str, str], HostModal] = {
            (net.name, host.name): host
            for net in zone.networks
            for host in net.hosts
        }

        for net_idx, network in enumerate(zone.networks):
            network_context = f"Network '{network.name}' (idx {net_idx}, {zone_context})"
            for host_idx, host in enumerate(network.hosts):
                host_context = f"Host '{host.name}' (idx {host_idx}, {network_context})"

                if host.type in problematic_host_types:
                    _add_error(errors, host_context, "type", f"Host type '{host.type}' is not appropriate for a host entity (it's a container type).")

                if network.type == "CLASSICAL_NETWORK":
                    if host.type not in classical_host_types and host.type != "QuantumAdapter": # Allowing adapter endpoint
                        _add_error(errors, host_context, "type", f"Host type '{host.type}' is not a typical classical host type for a CLASSICAL_NETWORK. Expected one of {classical_host_types} or QuantumAdapter endpoint.")
                elif network.type == "QUANTUM_NETWORK":
                    if host.type not in quantum_host_types and host.type != "QuantumAdapter": # Allowing adapter endpoint
                        _add_error(errors, host_context, "type", f"Host type '{host.type}' is not a typical quantum host type for a QUANTUM_NETWORK. Expected one of {quantum_host_types} or QuantumAdapter endpoint.")

        for adapter_idx, adapter in enumerate(zone.adapters):
            adapter_context = f"Adapter '{adapter.name}' (idx {adapter_idx}, {zone_context})"

            # Adapter's classical network type
            classical_net_name = adapter.classicalNetwork
            if classical_net_name in networks_in_zone:
                classical_network = networks_in_zone[classical_net_name]
                if classical_network.type != "CLASSICAL_NETWORK":
                    _add_error(errors, adapter_context, classical_net_name, f"Referenced classicalNetwork is of type '{classical_network.type}', expected 'CLASSICAL_NETWORK'.")

                # Adapter's classical host type
                classical_host_key = (classical_net_name, adapter.classicalHost)
                if classical_host_key in hosts_in_networks_in_zone:
                    chost = hosts_in_networks_in_zone[classical_host_key]
                    if chost.type not in classical_host_types and chost.type != "QuantumAdapter":
                         _add_error(errors, adapter_context, adapter.classicalHost, f"Referenced classicalHost '{chost.name}' in network '{classical_net_name}' has type '{chost.type}', not a typical classical type for adapter connection.")

            # Adapter's quantum network type
            quantum_net_name = adapter.quantumNetwork
            if quantum_net_name in networks_in_zone:
                quantum_network = networks_in_zone[quantum_net_name]
                if quantum_network.type != "QUANTUM_NETWORK":
                    _add_error(errors, adapter_context, quantum_net_name, f"Referenced quantumNetwork is of type '{quantum_network.type}', expected 'QUANTUM_NETWORK'.")

                # Adapter's quantum host type
                quantum_host_key = (quantum_net_name, adapter.quantumHost)
                if quantum_host_key in hosts_in_networks_in_zone:
                    qhost = hosts_in_networks_in_zone[quantum_host_key]
                    if qhost.type not in quantum_host_types and qhost.type != "QuantumAdapter":
                         _add_error(errors, adapter_context, adapter.quantumHost, f"Referenced quantumHost '{qhost.name}' in network '{quantum_net_name}' has type '{qhost.type}', not a typical quantum type for adapter connection.")


def _validate_value_sanity(world: WorldModal, errors: List[str]):
    """
    Validates sanity of specific numeric values.
    - Connection parameters (bandwidth, latency, length, loss_per_km).
    - Locations/Sizes are positive (partially covered by spatial, but good for direct checks on values).
    """
    for zone_idx, zone in enumerate(world.zones):
        zone_context = f"Zone '{zone.name}' (idx {zone_idx})"
        # Zone size/pos already checked in spatial for non-negativity and positive size.

        for net_idx, network in enumerate(zone.networks):
            network_context = f"Network '{network.name}' (idx {net_idx}, {zone_context})"
            # Network location already checked in spatial for non-negativity.

            for host_idx, host in enumerate(network.hosts):
                host_context = f"Host '{host.name}' (idx {host_idx}, {network_context})"
                # Host location already checked in spatial for non-negativity.

            for conn_idx, connection in enumerate(network.connections):
                conn_context = f"Connection '{connection.name}' (idx {conn_idx}, {network_context})"
                # Allow -1 for infinite values for now.
                # TODO: Revisit this logic if we want to handle infinite bandwidth/latency differently.
                # if connection.bandwidth <= 0:
                #     _add_error(errors, conn_context, "bandwidth", f"Bandwidth ({connection.bandwidth} Mbps) must be positive.")
                # if connection.latency < 0:
                #     _add_error(errors, conn_context, "latency", f"Latency ({connection.latency} ms) must be non-negative.")
                # if connection.length <= 0: # Length usually implies physical existence
                #     _add_error(errors, conn_context, "length", f"Length ({connection.length} km) must be positive.")
                # if connection.loss_per_km < 0:
                #     _add_error(errors, conn_context, "loss_per_km", f"Loss per km ({connection.loss_per_km}) must be non-negative.")

        # Adapter location already checked in spatial for non-negativity.


def validate_world_topology_static_logic(world: WorldModal) -> List[str]:
    """
    Main function to perform logical validation on the entire WorldModal.
    Returns a list of error and warning messages. An empty list means no issues found.
    """
    errors_and_warnings: List[str] = []

    if not world:
        errors_and_warnings.append("World data is None or empty.")
        return errors_and_warnings
    if not world.zones:
        # This might be valid for an empty world, or a warning could be issued.
        # errors_and_warnings.append("World contains no zones.")
        pass # Assuming an empty world is valid.

    # Call sub-validators
    _validate_uniqueness(world, errors_and_warnings)
    _validate_referential_integrity(world, errors_and_warnings)
    _validate_spatial_logic(world, errors_and_warnings)
    _validate_type_consistency(world, errors_and_warnings)
    _validate_value_sanity(world, errors_and_warnings)

    return errors_and_warnings