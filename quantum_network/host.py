import random
import time
import traceback
from typing import Any, Callable, List, Tuple
import qutip as qt
from core.base_classes import World, Zone
from core.enums import NodeType, SimulationEventType
from core.exceptions import QuantumChannelDoesNotExists
from core.network import Network
from quantum_network.channel import QuantumChannel
from quantum_network.node import QuantumNode


class QuantumHost(QuantumNode):
    def __init__(
        self,
        address: str,
        location: Tuple[int, int],
        network: Network,
        zone: Zone | World = None,
        send_classical_fn: Callable[[Any], None] = None,
        qkd_completed_fn: Callable[[List[int]], None] = None,
        name="",
        description="",
    ):
        super().__init__(
            NodeType.QUANTUM_HOST, location, network, address, zone, name, description
        )
        self.quantum_channels: List[QuantumChannel] = []
        self.entangled_nodes = {}
        self.basis_choices = []
        self.measurement_outcomes = []
        self.shared_bases_indices = []
        
        if send_classical_fn:
            self.send_classical_data = send_classical_fn
        
        if qkd_completed_fn:
            self.qkd_completed_fn = qkd_completed_fn

    def add_quantum_channel(self, channel):
        self.quantum_channels.append(channel)

    def channel_exists(self, to_host: QuantumNode):
        for chan in self.quantum_channels:
            if (chan.node_1 == self and chan.node_2 == to_host) or \
               (chan.node_2 == self and chan.node_1 == to_host):
                return chan
        return None

    def forward(self):
        while not self.qmemeory_buffer.empty():
            try:
                qbit = self.qmemeory_buffer.get()
                self.process_received_qbit(qbit)
            except Exception as e:
                traceback.print_exc()
                self.logger.error(f"Error processing received qubit: {e}")

    def send_qubit(self, qubit, channel: QuantumChannel):
        channel.transmit_qubit(qubit, self)
        self.qmemory = None

    def generate_entanglement(self, with_node: QuantumNode, channel: QuantumChannel):
        bell_state = qt.bell_state("00")

        self.qmemory = qt.ptrace(bell_state, 0)
        with_node.qmemory = qt.ptrace(bell_state, 1)

        self.entangled_nodes[with_node.address] = channel
        with_node.entangled_nodes[self.address] = channel

        self.send_qubit(with_node.qmemory, channel)

    def prepare_qubit(self, basis, bit):
        """Prepares a qubit in the given basis and bit value using QuTiP."""
        if basis == "Z":
            return qt.basis(2, bit)
        else:  # basis == "X"
            if bit == 0:
                return (qt.basis(2, 0) + qt.basis(2, 1)).unit()  # |+>
            else:
                return (qt.basis(2, 0) - qt.basis(2, 1)).unit()  # |->

    def measure_qubit(self, qubit, basis):
        """Measures the qubit in the given basis using QuTiP."""
        if basis == "Z":
            projector0 = qt.ket2dm(qt.basis(2, 0))
            projector1 = qt.ket2dm(qt.basis(2, 1))
        else:  # basis == "X"
            projector0 = qt.ket2dm((qt.basis(2, 0) + qt.basis(2, 1)).unit())
            projector1 = qt.ket2dm((qt.basis(2, 0) - qt.basis(2, 1)).unit())

        prob0 = qt.expect(projector0, qubit)
        return 0 if random.random() < prob0 else 1

    def process_received_qbit(self, qbit):
        self.set_qmemory(qbit)
        
        channel = self.get_channel()
        basis = random.choice(["Z", "X"])
        outcome = self.measure_qubit(qbit, basis)
        
        self.basis_choices.append(basis)
        self.measurement_outcomes.append(outcome)
        
        if len(self.measurement_outcomes) == channel.num_bits:
            self.send_bases_for_reconsile()

    def send_bases_for_reconsile(self):
        self.send_classical_data({
            'type': 'reconcile_bases',
            'data': self.basis_choices
        })
        
    def receive_classical_data(self, message):
        self.logger.debug(f"Received Classical Data at host {self}. Data => {message}")
        
        message_type = message["type"]
        if message_type == "reconcile_bases":
            self.bb84_reconcile_bases(message["data"])
        elif message_type == "estimate_error_rate":
            self.bb84_estimate_error_rate(message["data"])
        elif message_type == "complete":
            raw_key = self.bb84_extract_key()
            if self.qkd_completed_fn:
                self.qkd_completed_fn(raw_key)
        elif message_type == 'shared_bases_indices':
            self.update_shared_bases_indices(message['data'])
            
        self._send_update(SimulationEventType.DATA_RECEIVED, message=message)
            
    def update_shared_bases_indices(self, shared_base_indices):
        channel = self.get_channel()
        self.shared_bases_indices = shared_base_indices
        
        # Sample bits for error estimation (up to 25% of total bits)
        sample_size = random.randrange(2, channel.num_bits // 4)
        random_indices = random.sample(range(len(self.measurement_outcomes)), 
                                     min(sample_size, len(self.shared_bases_indices)))
        
        error_sample = [(self.measurement_outcomes[i], i) for i in random_indices]
        
        self.send_classical_data({
            'type': 'estimate_error_rate',
            'data': error_sample
        })

    def get_channel(self, to_host: QuantumNode = None):
        """Returns the quantum channel to the specified host."""

        if to_host is None:
            # TODO: Handle case where no specific host is provided
            return self.quantum_channels[0] if self.quantum_channels else None

        for chan in self.quantum_channels:
            if (chan.node_1 == self and chan.node_2 == to_host) or \
               (chan.node_2 == self and chan.node_1 == to_host):
                return chan
        return None
        
    def bb84_send_qubits(self):
        """Sends a sequence of qubits for the BB84 protocol."""
        self.basis_choices = []
        self.measurement_outcomes = []
        
        if not self.quantum_channels:
            raise QuantumChannelDoesNotExists(self)
        
        channel = self.get_channel()
        generated_qubits = []
        for _ in range(channel.num_bits):
            basis = random.choice(["Z", "X"])
            bit = random.choice([0, 1])
            
            self.basis_choices.append(basis)
            self.measurement_outcomes.append(bit)
            
            qubit = self.prepare_qubit(basis, bit)
            generated_qubits.append(qubit)

        print(f"Host {self.name} generated {len(generated_qubits)} qubits for BB84 protocol.")
        
        for qubit in generated_qubits:
            self.send_qubit(qubit, channel)

    def bb84_reconcile_bases(self, their_bases):
        """Performs basis reconciliation."""
        self.shared_bases_indices = [
            i for i, (b1, b2) in enumerate(zip(self.basis_choices, their_bases))
            if b1 == b2
        ]

        self.send_classical_data({
            "type": "shared_bases_indices",
            "data": self.shared_bases_indices,
            "sender": self,
        })

    def bb84_estimate_error_rate(self, their_bits_sample):
        """Estimates the error rate by comparing a sample of bits."""
        if not their_bits_sample:
            error_rate = 0
        else:
            num_errors = sum(1 for their_bit, i in their_bits_sample 
                           if self.measurement_outcomes[i] != their_bit)
            error_rate = num_errors / len(their_bits_sample)

        channel = self.get_channel()

        if error_rate > channel.error_rate_threshold:
            self.send_classical_data({"type": "error_rate", "data": error_rate})
            self.logger.warning(f"Error rate {error_rate} exceeds threshold {channel.error_rate_threshold}. Retrying QKD.")
        else:            
            self.send_classical_data({'type': 'complete'})
            
            raw_key = self.bb84_extract_key()
            print(f"=====================> QKD Completed with key: {raw_key} <=====================")
            if self.qkd_completed_fn:
                self.qkd_completed_fn(raw_key)

    def bb84_extract_key(self):
        """Extracts a shared key based on the reconciliation information."""
        return [self.measurement_outcomes[i] for i in self.shared_bases_indices]
    
    def perform_qkd(self):
        self.bb84_send_qubits()

    def __name__(self):
        return f"QuantumHost - '{self.name}'"

    def __repr__(self):
        return self.__name__()