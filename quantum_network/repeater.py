import random
from typing import Tuple, TYPE_CHECKING, Union
from core.base_classes import World, Zone
from core.enums import InfoEventType, NodeType, SimulationEventType
from core.network import Network
from quantum_network.channel import QuantumChannel
from quantum_network.node import QuantumNode
import qutip as qt

if TYPE_CHECKING:
    from quantum_network.host import QuantumHost

class QuantumRepeater(QuantumNode):
    def __init__(
        self,
        address: str,
        location: Tuple[int, int],
        network: 'Network',
        zone: 'Zone',
        protocol: str = "entanglement_swapping",
        num_memories: int = 2,
        memory_fidelity: float = 0.99,
        name="",
    ):
        super().__init__(NodeType.QUANTUM_REPEATER, location, network, address, zone, name=name)
        self.protocol = protocol
        self.num_memories = num_memories
        self.qmemory: dict[str, qt.Qobj] = {}
        self.quantum_channels: list['QuantumChannel'] = []

    def add_quantum_channel(self, channel: 'QuantumChannel'):
        self.quantum_channels.append(channel)

    def get_other_node(self, node_1: Union['QuantumHost', 'str']):
        """Returns the other node connected by a quantum channel."""

        if isinstance(node_1, str):
            # If node_1 is a string, find the host by name
            for node in self.network.nodes:
                if node.name == node_1:
                    node_1 = node
                    break

        for channel in self.quantum_channels:
            q_host = channel.get_other_node(self)
            if q_host != node_1:
                return q_host
        return None

    def channel_exists(self, host: 'QuantumNode', _visited: set = None):
        """Checks if a channel to a given host exists from this repeater (direct or via other repeaters)."""
        if _visited is None:
            _visited = set()
        if self in _visited:
            return None
        _visited.add(self)
        for channel in self.quantum_channels:
            other = channel.get_other_node(self)
            if other == host:
                return channel
            if isinstance(other, QuantumRepeater):
                if other.channel_exists(host, _visited) is not None:
                    return channel
        return None

    def get_other_end_host(self, from_node: 'QuantumNode', _visited: set = None):
        """
        For daisy chains: walk from this repeater away from from_node until we hit a QuantumHost.
        Returns that QuantumHost, or None if not found (e.g. cycle or no host).
        """
        if _visited is None:
            _visited = set()
        if self in _visited:
            return None
        _visited.add(self)
        for channel in self.quantum_channels:
            other = channel.get_other_node(self)
            if other is from_node:
                continue
            # End host: node that has request_entanglement (QuantumHost)
            if callable(getattr(other, "request_entanglement", None)):
                return other
            if isinstance(other, QuantumRepeater):
                end = other.get_other_end_host(self, _visited)
                if end is not None:
                    return end
        return None

    def receive_qubit(self, qubit: qt.Qobj, source_channel: 'QuantumChannel'):
        """This is the main trigger for the repeater's logic."""
        if len(self.qmemory) >= self.num_memories:
            print(f"REPEATER {self.name}: Memory full. Dropping qubit.")
            return

        sender = source_channel.get_other_node(self)
        print(f"REPEATER {self.name}: Received qubit from {sender.name}.")

        # Daisy chain: if we have no qubits yet and the sender is an end host, forward toward the other end
        # so both qubits can meet at one repeater for BSM. Only forward to another repeater (never to an
        # end host, and never back to sender — avoids loop and "received qubit in entanglement_swapping" error).
        if len(self.qmemory) == 0 and callable(getattr(sender, "request_entanglement", None)):
            other_channel = next((ch for ch in self.quantum_channels if ch is not source_channel), None)
            if other_channel is not None:
                other_node = other_channel.get_other_node(self)
                if other_node is not sender and isinstance(other_node, QuantumRepeater):
                    print(f"REPEATER {self.name}: Forwarding qubit from {sender.name} toward other end.")
                    other_channel.transmit_qubit(qubit, self)
                    return

        self.qmemory[sender.name] = qubit
        print(f"REPEATER {self.name}: Current memory size: {len(self.qmemory)}/{self.num_memories}.")
        
        if self.protocol == "entanglement_swapping":
            self.execute_entanglement_swapping()

    def forward(self):
        """Dispatcher for different repeater protocols."""
        if self.protocol == "entanglement_swapping":
            self.execute_entanglement_swapping()

    def execute_entanglement_swapping(self):
        """Performs entanglement swapping if two qubits are in memory."""
        if len(self.qmemory) < 2:
            print(f"REPEATER {self.name}: Waiting for another qubit. Memory has {len(self.qmemory)}/2 qubits.")
            return

        print(f"REPEATER {self.name}: Has 2 qubits. Attempting entanglement swap.")
        addresses = list(self.qmemory.keys())
        neighbor_1_addr, neighbor_2_addr = addresses[0], addresses[1]
        qubit_1 = self.qmemory[neighbor_1_addr]
        qubit_2 = self.qmemory[neighbor_2_addr]
        self._send_update(SimulationEventType.REPEATER_ENTANGLEMENT_INFO, 
            type=InfoEventType.ATTEMPTING_SWAP,
            sender=neighbor_1_addr,
            receiver=neighbor_2_addr,
            qubit=qubit_1,
            qubit2=qubit_2
        )

        measurement_result = self._perform_bell_measurement(qubit_1, qubit_2)
        print(f"REPEATER {self.name}: BSM result is {measurement_result}.")
        self._send_update(SimulationEventType.REPEATER_ENTANGLEMENT_INFO,
            type=InfoEventType.PERFORMED_BELL_MEASUREMENT,
            sender=neighbor_1_addr,
            receiver=neighbor_2_addr,
            qubit=qubit_1,
            qubit2=qubit_2,
            measurement_result=measurement_result
        )

        # Send correction to the end host on neighbor_2's side; message must identify the other end host by name (for daisy chain).
        neighbor_1_node = next((n for n in self.network.nodes if n.name == neighbor_1_addr), None)
        neighbor_2_node = next((n for n in self.network.nodes if n.name == neighbor_2_addr), None)
        if neighbor_1_node is None or neighbor_2_node is None:
            target_node = self.get_other_node(neighbor_1_addr)
            other_node_address = neighbor_1_addr
        else:
            # Resolve end hosts (supports daisy chain)
            if callable(getattr(neighbor_1_node, "request_entanglement", None)):
                end_host_1 = neighbor_1_node
            else:
                end_host_1 = self.get_other_end_host(neighbor_2_node) if isinstance(neighbor_2_node, QuantumRepeater) else None
            if callable(getattr(neighbor_2_node, "request_entanglement", None)):
                end_host_2 = neighbor_2_node
            else:
                end_host_2 = self.get_other_end_host(neighbor_1_node) if isinstance(neighbor_1_node, QuantumRepeater) else None
            target_node = end_host_2
            other_node_address = end_host_1.name if end_host_1 is not None else neighbor_1_addr
        classical_message = {
            "type": "entanglement_swap_correction",
            "measurement_result": measurement_result,
            "other_node_address": other_node_address,
        }
        if not target_node:
            print(f"REPEATER {self.name}: No end host to send correction to.")
            return
        target_node.receive_classical_data(classical_message)

        self.clear_qmemory()

    def _perform_bell_measurement(self, q1: qt.Qobj, q2: qt.Qobj) -> Tuple[int, int]:
        """Simulates a Bell State Measurement on two qubits using QuTiP."""
        # A BSM projects the two-qubit state onto one of the four Bell states.
        # This is equivalent to CNOT, then Hadamard on control, then measure.
        # For a simulation, we can project onto the Bell basis directly.
        bell_basis = [qt.bell_state(f'{i}{j}') for i in '01' for j in '01']
        
        # Combine the state of the two qubits in memory
        # if q1.isdm:
        #     # If qubits are density matrices (due to channel noise)
        #     combined_state = qt.tensor(q1, q2)
        # else:
        #     # if they are kets
        #     combined_state = qt.tensor(q1, q2) * qt.tensor(q1,q2).dag()
        combined_state = qt.tensor(q1, q2) * qt.tensor(q1,q2).dag()

        # Calculate probabilities of projecting onto each Bell state
        probabilities = [qt.expect(p * p.dag(), combined_state) for p in bell_basis]
        
        # Choose an outcome based on the probabilities
        outcome_index = random.choices(range(4), weights=probabilities, k=1)[0]
        
        # Map index to classical bits (m1, m2)
        # 0 -> |Φ+⟩ -> (0,0)
        # 1 -> |Ψ+⟩ -> (0,1)
        # 2 -> |Φ-⟩ -> (1,0)
        # 3 -> |Ψ-⟩ -> (1,1)
        return (outcome_index // 2, outcome_index % 2)

    def clear_qmemory(self):
        print(f"REPEATER {self.name}: Clearing memory.")
        self.qmemory.clear()

    def __repr__(self):
        return f"QuantumRepeater('{self.name}')"