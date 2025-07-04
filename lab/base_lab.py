from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
import itertools
import random
import threading
import time
from typing import Any, Dict, List, Optional
from classical_network.config.connection_config import ConnectionConfig
from classical_network.host import ClassicalHost
from classical_network.presets.connection_presets import DEFAULT_PRESET
from data.models.topology.node_model import HOST_TYPES, AdapterModal, ConnectionModal, HostModal, NetworkModal
from data.models.topology.world_model import WorldModal
from data.models.topology.zone_model import ZoneModal
from quantum_network.host import QuantumHost
from server.api.simulation.manager import SimulationManager

@dataclass
class LabConnection:
    from_host: str
    to_host: str
    connection_config: Optional[ConnectionConfig] = None

class QSimLab(ABC):
    _classical_hosts: Dict[str, Dict[str, Any]] = {}
    _classical_router: Dict[str, Dict[str, Any]] = {}
    _connections:List[Dict[str, Any]] = []
    _quantum_hosts: Dict[str, Dict[str, Any]] = {}
    _quantum_adapters: Dict[str, Dict[str, Any]] = {}

    def _setup_nodes(self):
        self._setup_world()
        self._setup_classical_hosts()
        self._setup_classical_router()
        self._setup_classical_connections()
        self._setup_quantum_hosts()
        self._setup_quantum_adapters()

        self.world.save()

    @property
    def _classical_nodes(self):
        """Returns a list of all classical nodes in the lab."""
        return self._classical_hosts.update(self._classical_router)

    def _setup_world(self):
        self.world = WorldModal(
            name="QSimLab__"+ self.__class__.__name__,
            size=(1000, 1000),
            zones=[],
            temporary_world=True,
            lab_world=True
        )

        self.zones = {
            'default': ZoneModal(
                name="Default Zone",
                type="SECURE",
                size=(1000, 1000),
                position=(0, 0),
                networks=[],
                adapters=[]
            )
        }

        self.networks = {
            'default_classical': NetworkModal(
                name="Default Classical Network",
                address="default_classical_network",
                type="CLASSICAL_NETWORK",
                location=(0, 0),
                hosts=[],
                connections=[],
            ),
            'default_quantum': NetworkModal(
                name="Default Quantum Network",
                address="default_quantum_network",
                type="QUANTUM_NETWORK",
                location=(0, 0),
                hosts=[],
                connections=[],
            )
        }

    def _setup_classical_hosts(self):
        for host_name, host_data in self._classical_hosts.items():
            preferred_network = host_data.get('preferred_network', 'default_classical')
            if preferred_network not in self.networks:
                raise ValueError(f"Preferred network '{preferred_network}' for host '{host_name}' does not exist in the lab configuration.")
            
            preferred_zone = host_data.get('preferred_zone', 'default')
            if preferred_zone not in self.zones:
                raise ValueError(f"Preferred zone '{preferred_zone}' for host '{host_name}' does not exist in the lab configuration.")
            
            host = HostModal(
                name=host_data.get('address', host_name),
                type='ClassicalHost',
                address=host_data.get('address', host_name),
                location=host_data.get('location', (random.randint(0, self.world.size[0]), random.randint(0, self.world.size[1]))),
            )

            if self.networks[preferred_network] not in self.zones[preferred_zone].networks:
                self.zones[preferred_zone].networks.append(self.networks[preferred_network])
                if self.zones[preferred_zone] not in self.world.zones:
                    self.world.zones.append(self.zones[preferred_zone])

            self.networks[preferred_network].hosts.append(host)
            
    def _setup_classical_router(self):
        for router_name, router_data in self._classical_router.items():
            preferred_network = router_data.get('preferred_network', 'default_classical')
            if preferred_network not in self.networks:
                raise ValueError(f"Preferred network '{preferred_network}' for router '{router_name}' does not exist in the lab configuration.")
            
            preferred_zone = router_data.get('preferred_zone', 'default')
            if preferred_zone not in self.zones:
                raise ValueError(f"Preferred zone '{preferred_zone}' for router '{router_name}' does not exist in the lab configuration.")
            
            router = HostModal(
                name=router_data.get('address', router_name),
                type='ClassicalRouter',
                address=router_data.get('address', router_name),
                location=router_data.get('location', (random.randint(0, self.world.size[0]), random.randint(0, self.world.size[1]))),
            )

            if self.networks[preferred_network] not in self.zones[preferred_zone].networks:
                self.zones[preferred_zone].networks.append(self.networks[preferred_network])
                if self.zones[preferred_zone] not in self.world.zones:
                    self.world.zones.append(self.zones[preferred_zone])

            self.networks[preferred_network].hosts.append(router)

    def _setup_classical_connections(self):
        for connection in self._connections:
            from_host = connection.get('from_host')
            to_host = connection.get('to_host')
            connection_config = connection.get('connection_config', {})

            if not(self.world.get_host_by_name(from_host) and self.world.get_host_by_name(to_host)):
                raise ValueError(f"Connection between '{from_host}' and '{to_host}' cannot be established because one of the hosts does not exist in the lab configuration.")
            
            if self.world.get_network_by_host(from_host) != self.world.get_network_by_host(to_host):
                raise ValueError(f"Hosts '{from_host}' and '{to_host}' are not in the same network. Connection cannot be established.")
            
            connection_config =  {**asdict(DEFAULT_PRESET), **connection_config}
            connection_instance = ConnectionModal(
                from_node=from_host,
                to_node=to_host,
                name=f"{from_host}_to_{to_host}",
                **connection_config,
                length=connection_config.get('length', 1000),
                loss_per_km= connection_config.get('loss_per_km', 0.0),
            )

            self.world.get_network_by_host(from_host).connections.append(connection_instance)

    def _setup_quantum_hosts(self):
        for host_name, host_data in self._quantum_hosts.items():
            preferred_network = host_data.get('preferred_network', 'default_quantum')
            if preferred_network not in self.networks:
                raise ValueError(f"Preferred network '{preferred_network}' for host '{host_name}' does not exist in the lab configuration.")
            
            preferred_zone = host_data.get('preferred_zone', 'default')
            if preferred_zone not in self.zones:
                raise ValueError(f"Preferred zone '{preferred_zone}' for host '{host_name}' does not exist in the lab configuration.")
            
            host = HostModal(
                name=host_data.get('address', host_name),
                type='QuantumHost',
                address=host_data.get('address', host_name),
                location=host_data.get('location', (random.randint(0, self.world.size[0]), random.randint(0, self.world.size[1]))),
            )

            if self.networks[preferred_network] not in self.zones[preferred_zone].networks:
                self.zones[preferred_zone].networks.append(self.networks[preferred_network])
                if self.zones[preferred_zone] not in self.world.zones:
                    self.world.zones.append(self.zones[preferred_zone])

            self.networks[preferred_network].hosts.append(host)

    def _setup_quantum_adapters(self):
        for adapter_name, adapter_data in self._quantum_adapters.items():
            q_host = adapter_data.get('quantumHost')
            if not q_host:
                raise ValueError(f"Quantum host for adapter '{adapter_name}' is not specified in the lab configuration.")
            if self.world.get_host_by_name(q_host) is None:
                raise ValueError(f"Quantum host '{q_host}' for adapter '{adapter_name}' does not exist in the lab configuration.")
            
            c_host = adapter_data.get('classicalHost')
            if not c_host:
                raise ValueError(f"Classical host for adapter '{adapter_name}' is not specified in the lab configuration.")
            if self.world.get_host_by_name(c_host) is None:
                raise ValueError(f"Classical host '{c_host}' for adapter '{adapter_name}' does not exist in the lab configuration.")
            
            preferred_classical_network = adapter_data.get('classicalNetwork', 'default_classical')
            if preferred_classical_network not in self.networks:
                raise ValueError(f"Preferred network '{preferred_classical_network}' for adapter '{adapter_name}' does not exist in the lab configuration.")
            
            preferred_quantum_network = adapter_data.get('quantumNetwork', 'default_quantum')
            if preferred_quantum_network not in self.networks:
                raise ValueError(f"Preferred quantum network '{preferred_quantum_network}' for adapter '{adapter_name}' does not exist in the lab configuration.")
            
            adapter = AdapterModal(
                name=adapter_name,
                type=adapter_data.get('type', 'QUMO'),
                address=adapter_data.get('address', adapter_name),
                location=adapter_data.get('location', (random.randint(0, self.world.size[0]), random.randint(0, self.world.size[1]))),
                quantumHost=q_host,
                classicalHost=c_host,
                classicalNetwork=self.networks[preferred_classical_network].name,
                quantumNetwork=self.networks[preferred_quantum_network].name,
            )

            preferred_zone = adapter_data.get('preferred_zone', 'default')
            if preferred_zone not in self.zones:
                raise ValueError(f"Preferred zone '{preferred_zone}' for adapter '{adapter_name}' does not exist in the lab configuration.")
            self.zones[preferred_zone].adapters.append(adapter)

    async def _run(self):
        self._setup_nodes()
        manager = SimulationManager.get_instance()
        if not manager.start_simulation(self.world):
            raise RuntimeError("Failed to start simulation. Ensure the world is properly configured and all nodes are connected.")
        print(f"Running started")
        time.sleep(2)
        self.execute()
        print("waiting for 30 seconds before stopping the simulation")
        time.sleep(30)
        print("Stopping simulation")
        manager.stop()

    def get_host(self, host_name: str):
        if not hasattr(self, 'world'):
            self._setup_world()
        return self.world.get_host_by_name(host_name)

    def send_message(self, from_host: str, to_host: str, message: str):
        """Send a message from one host to another."""
        sender = self.get_host(from_host)
        receiver = self.get_host(to_host)
        
        if not sender or not receiver:
            raise ValueError(f"Sender '{from_host}' or receiver '{to_host}' does not exist in the lab configuration.")
        
        manager = SimulationManager.get_instance()
        if not manager.is_running:
            raise RuntimeError("Simulation is not running. Please start the simulation before executing commands.")
        manager.send_message_command(sender.name, receiver.name, message)

    @abstractmethod
    def execute(self):
        raise NotImplementedError("Subclasses must implement the execute method.")
    
