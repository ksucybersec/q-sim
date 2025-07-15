import json
from typing import Dict, Union
from classical_network.config.connection_config import ConnectionConfig
from classical_network.connection import ClassicConnection
from classical_network.host import ClassicalHost
from classical_network.presets.connection_presets import DEFAULT_PRESET
from classical_network.router import ClassicalRouter
from core.base_classes import Node, World, Zone
from core.enums import NetworkType, ZoneType
from core.network import Network
from quantum_network.adapter import QuantumAdapter
from quantum_network.channel import QuantumChannel
from quantum_network.host import QuantumHost
from quantum_network.node import QuantumNode
from quantum_network.repeater import QuantumRepeater
from utils.visualize import visualize_network

def parse_json_and_build_network(json_data:Union[str, Dict], on_update_func=None):

    if isinstance(json_data, str):
        with open(json_data, 'r') as f:
            world_data = json.load(f)
    else:
        world_data = json_data

    world = World(size=tuple(world_data['size']), name=world_data['name'], on_update_func=on_update_func)
    # Store created objects for later reference (connections, etc.)
    zones = {}
    networks = {}
    hosts: Dict[str, Node] = {}
    classical_connections: Dict[str, ClassicConnection] = {}
    quantum_connections: Dict[str, QuantumChannel] = {}
    adapters: Dict[str, QuantumAdapter] = {}
    default_protocol = "bb84"  # Default protocol for quantum hosts


    # First pass: Create zones, networks, and hosts
    for zone_data in world_data['zones']:
        zone = Zone(
            size=tuple(zone_data['size']),
            position=tuple(zone_data['position']),
            zone_type=ZoneType[zone_data['type']],  # Convert string to enum
            parent_zone=world,
            name=zone_data['name']
        )
        world.add_zone(zone)
        zones[zone.name] = zone
        classical_connections[zone.name] = {}
        quantum_connections[zone.name] = {}

        for network_data in zone_data.get('networks', []):  # Use .get() for safety
            network_type = NetworkType[network_data['type']]
            network = Network(
                network_type=network_type,
                location=tuple(network_data['location']),
                zone=zone,
                name=network_data['name']
            )
            zone.add_network(network)
            networks[network.name] = network
            classical_connections[zone.name][network.name] = {}
            quantum_connections[zone.name][network.name] = {}


            for host_data in network_data.get('hosts', []):
                if host_data['type'] == "ClassicalHost":
                    host = ClassicalHost(
                        address=host_data['address'],
                        location=tuple(host_data['location']),
                        network=network,
                        zone=zone,
                        name=host_data['name']
                    )

                elif host_data['type'] == "ClassicalRouter":
                    host = ClassicalRouter(
                        address=host_data['address'],
                        location=tuple(host_data['location']),
                        network=network,
                        zone=zone,
                        name=host_data['name']
                    )
                elif host_data['type'] == "QuantumHost":
                    host = QuantumHost(
                        address=host_data['address'],
                        location=tuple(host_data['location']),
                        network=network,
                        zone=zone,
                        name=host_data['name'],
                        send_classical_fn=None,  # Will be set later
                        protocol=host_data.get('protocol',  default_protocol),
                    )
                elif host_data['type'] == "QuantumAdapter":
                    host = QuantumAdapter(
                        address= host_data['address'],
                        location=tuple(host_data['location']),
                        network=network,
                        zone=zone,
                        name=host_data['name'],
                    )
                elif host_data['type'] == "QuantumRepeater":
                    host = QuantumRepeater(
                        address=host_data['address'],
                        location=tuple(host_data['location']),
                        network=network,
                        zone=zone,
                        name=host_data['name'],
                        protocol=host_data.get('protocol', 'entanglement_swapping'),
                        num_memories=host_data.get('num_memories', 2),
                        memory_fidelity=host_data.get('memory_fidelity', 0.99),
                    )

                    if default_protocol == "bb84":
                        default_protocol = host_data.get('protocol', 'entanglement_swapping')
                        print(f"Default protocol set to {default_protocol} based on repeater {host.name}. Updating protocol for other QHosts as well")
                        for other_host in hosts.values():
                            if isinstance(other_host, QuantumHost) and other_host.protocol == "bb84":
                                other_host.protocol = default_protocol
                                print(f"Updated protocol for {other_host.name} to {default_protocol}")


                else:
                    raise ValueError(f"Unknown host type: {host_data['type']}")
                network.add_hosts(host)
                hosts[host.name] = host
                classical_connections[zone.name][network.name][host.name] = []
                quantum_connections[zone.name][network.name][host.name] = []

    # Second Pass: Create connections and set references
    for zone_data in world_data['zones']:
        zone = zones[zone_data['name']]

        for network_data in zone_data.get('networks', []):
            network = networks[network_data['name']]
            if network.network_type == NetworkType.CLASSICAL_NETWORK:
                for connection_data in network_data.get('connections', []):
                    conn_config = ConnectionConfig(
                        bandwidth=connection_data['bandwidth'],
                        latency=connection_data['latency'],
                        packet_loss_rate=connection_data.get('packet_loss_rate', 0.0),
                        packet_error_rate=connection_data.get('packet_error_rate', 0.0),
                        mtu=connection_data.get('mtu', 1500),
                    )

                    connection = ClassicConnection(
                        node_1=hosts[connection_data['from_node']],
                        node_2=hosts[connection_data['to_node']],
                        config=conn_config,
                        name=connection_data['name']
                    )
                    hosts[connection_data['from_node']].add_connection(connection)
                    hosts[connection_data['to_node']].add_connection(connection)

            elif network.network_type == NetworkType.QUANTUM_NETWORK:
                for connection_data in network_data.get('connections', []):
                    node_1: QuantumNode = hosts[connection_data['from_node']]
                    node_2: QuantumNode = hosts[connection_data['to_node']]
                    connection = QuantumChannel(
                        node_1=node_1,
                        node_2=node_2,
                        length=connection_data['length'],
                        loss_per_km=connection_data['loss_per_km'],
                        noise_model= connection_data.get('noise_model', 'none'),
                        name=connection_data['name'],
                        noise_strength=connection_data.get('noise_strength', 0.01),
                        error_rate_threshold=connection_data.get('error_rate_threshold', 10.0),
                        num_bits=connection_data.get('qbits', 16)
                    )
                    node_1.add_quantum_channel(connection)
                    node_2.add_quantum_channel(connection)

    # Third Pass: Create adapters and set references
    for zone_data in world_data['zones']:
        zone = zones[zone_data['name']]
        for adapter_data in zone_data['adapters']:
            q_host: QuantumHost = hosts[adapter_data['quantumHost']]
            c_host:ClassicalHost = hosts[adapter_data['classicalHost']]

            c_network = networks[adapter_data['classicalNetwork']]
            q_network = networks[adapter_data['quantumNetwork']]

            paired_adapter = None
            # Look for paired adapter
            for other_adapter in adapters.values():
                if other_adapter.local_quantum_host.channel_exists(q_host):
                    paired_adapter = other_adapter
                    # print("Paired adapter found:", paired_adapter)
                    break

            adapter = QuantumAdapter(
                adapter_data['name'],
                c_network,
                q_network,
                tuple(adapter_data['location']),
                paired_adapter,
                q_host,
                None,
                adapter_data['name'],
            )

            if paired_adapter:
                paired_adapter.add_paired_adapter(adapter)
            # else:
            #     print(f"Error: No paired adapter found for {adapter_data['name']}. This may lead to issues in communication.")
            #     raise Exception(f"Paired adapter not found for {adapter_data['name']}")
                
            adapter_network1_connection = ClassicConnection(
                c_host,
                adapter.local_classical_router,
                DEFAULT_PRESET,
                name=f"{c_host} {adapter} Connection",
            )
            adapter.local_classical_router.add_connection(adapter_network1_connection)
            c_host.add_connection(adapter_network1_connection)
            q_network.add_hosts(adapter)
            for n in c_network.nodes:
                if isinstance(n, ClassicalHost):
                    n.add_quantum_adapter(adapter)

            adapters[adapter_data['name']] = adapter

    for host_name, host in hosts.items():
        if isinstance(host, QuantumHost):
            for other_host_name, other_host in hosts.items():
                if isinstance(other_host, QuantumHost) and host.name != other_host.name:
                    # Create a simple lambda function for communication
                    host.send_classical_fn = lambda msg, other_host=other_host: other_host.receive_classical_data(msg)

        if isinstance(host, QuantumAdapter):
            if host.name in hosts:
                if "paired_adapter" in  host_data and host_data['paired_adapter'] != None:
                    host.add_paired_adapter(hosts[host_data['paired_adapter']])

        if isinstance(host, ClassicalHost):
            if "quantum_adapter" in host_data and host_data['quantum_adapter'] != None:
             host.add_quantum_adapter(hosts[host_data['quantum_adapter']])


    return world

def simulate_from_json(json_file: Union[str, Dict], on_update_func=None):
    with open('log.txt', 'w') as f:
        f.write("Start")
    world = parse_json_and_build_network(json_file, on_update_func)
    visualize_network(world, "out_parsed.png")
    world.start_sequential()
    return world


if __name__ == "__main__":
    simulate_from_json("network.json")