import random
import time
import traceback
from typing import Any, Callable, List, Tuple
import qutip as qt
from core.base_classes import World, Zone
from core.enums import InfoEventType, NodeType, SimulationEventType
from core.exceptions import QuantumChannelDoesNotExists
from core.network import Network
from quantum_network.channel import QuantumChannel
from quantum_network.node import QuantumNode
from quantum_network.repeater import QuantumRepeater


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
        protocol: str = "bb84"
    ):
        super().__init__(
            NodeType.QUANTUM_HOST, location, network, address, zone, name, description
        )
        
        self.protocol = protocol

        self.quantum_channels: List[QuantumChannel] = []
        self.entangled_nodes = {}
        self.basis_choices = []
        self.measurement_outcomes = []
        self.shared_bases_indices = []

        
        # --- Entanglement Swapping Attributes ---
        self.entangled_qubit: qt.Qobj | None = None
        self.entanglement_partner_address: str | None = None
        self.entangled_channel: QuantumChannel | None = None
        
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
        return self.proxy_channel_exists(to_host)

    def proxy_channel_exists(self, to_host: QuantumNode):
        """Checks if a proxy channel exists to the specified host."""
        for chan in self.quantum_channels:
            if chan.node_1 == self:
                if isinstance(chan.node_2, QuantumRepeater) and chan.node_2.channel_exists(to_host):
                    return chan
                elif chan.node_2.is_eavesdropper and chan.node_2.get_outgoing_victim_channel(to_host):
                    return chan
            elif chan.node_2 == self:
                if isinstance(chan.node_1, QuantumRepeater) and chan.node_1.channel_exists(to_host):
                    return chan
                elif chan.node_1.is_eavesdropper and chan.node_1.get_outgoing_victim_channel(to_host):
                    return chan
        return None

    def forward(self):
        while not self.qmemeory_buffer.empty():
            try:
                if self.protocol == "bb84" or self.entangled_channel:
                    qbit, from_channel = self.qmemeory_buffer.get()
                    self.process_received_qbit(qbit, from_channel)
                elif self.protocol == "entanglement_swapping":
                    print(f"ERROR: Host {self.name} received a qubit while in entanglement_swapping mode. This should not happen in this protocol.")
                else:
                    print(f"Host {self.name} received qubit but has no   protocol handler for '{self.protocol}'.")
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

    @property
    def is_eavesdropper(self):
        return len(self.quantum_channels) == 2
    
    def get_outgoing_victim_channel(self, incoming_channel:QuantumChannel):
        outgoing_channel = None
        for channel in self.quantum_channels:
            if channel != incoming_channel:
                outgoing_channel = channel
                break
        return outgoing_channel

    def process_received_qbit(self, qbit: qt.Qobj, from_channel: QuantumChannel):
        self.set_qmemory(qbit)
        
        channel = self.get_channel()
        basis = random.choice(["Z", "X"])
        outcome = self.measure_qubit(qbit, basis)
        
        self.basis_choices.append(basis)
        self.measurement_outcomes.append(outcome)
        if self.is_eavesdropper:
            new_qubit_to_send = self.prepare_qubit(basis, outcome)

            outgoing_channel = self.get_outgoing_victim_channel(from_channel)
            print(f"Host {self.name} is eavesdropping. Forwarding qubit to {outgoing_channel.node_2.name if outgoing_channel else 'unknown channel'}")
            
            if outgoing_channel:
                self.send_qubit(new_qubit_to_send, outgoing_channel)
            else:
                self.logger.warning(f"Eavesdropper {self.name} has no channel to forward to!")       
        else:
            if len(self.measurement_outcomes) == channel.num_bits:
                self.send_bases_for_reconsile()

    def send_bases_for_reconsile(self):
        self.send_classical_data({
            'type': 'reconcile_bases',
            'data': self.basis_choices
        })
        
    def receive_classical_data(self, message):
        # self.logger.debug(f"Received Classical Data at host {self}. Data => {message}")
        message_type = message.get("type")
        
        # --- NEW: Route to entanglement swapping logic ---
        if message_type == "entanglement_swap_correction":
            if self.protocol == "entanglement_swapping":
                self.apply_entanglement_correction(message)
            else:
                print(f"WARNING: Host {self.name} received entanglement message but is in '{self.protocol}' mode.")
            return
        
        if self.protocol == "bb84" or self.entangled_channel:
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
        
        channel = self.entangled_channel or  self.get_channel()
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

        print("=====================> Error Rate Estimation <=====================")
        print(f"Host: {self.name}, Error Rate: {error_rate:.2f}, "
              f"Sample Size: {len(their_bits_sample)}, "
              f"Total Bits: {channel.num_bits}")

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
        if self.protocol == 'entanglement_swapping':
            channel = self.get_channel()
            repeater = channel.get_other_node(self)
            if not isinstance(repeater, QuantumRepeater):
                print(f"ERROR: Host {self.name} is in 'entanglement_swapping' mode but no repeater found on channel.")
                return
            target = repeater.get_other_node(self)
            self.request_entanglement(target)
            target.request_entanglement(self)
        else:
            self.bb84_send_qubits()

    def request_entanglement(self, target_host: 'QuantumHost'):
        """
        Initiates an entanglement generation request with a target host,
        sending one half of a Bell pair to the first node in the chain.
        """
        if self.protocol != "entanglement_swapping":
            print(f"ERROR: Host {self.name} is not in 'entanglement_swapping' mode.")
            return

        print(f"HOST {self.name}: Requesting entanglement with {target_host.name}.")
        self._send_update(SimulationEventType.REPEATER_ENTANGLEMENT_INITIALIZED, host= self.name,target= target_host.name)
        channel = self.channel_exists(target_host)
        if not channel:
            print(f"ERROR: No direct or indirect channel found to {target_host.name}.")
            return
            
        # 1. Create a Bell State
        bell_state = qt.bell_state("00")  # Creates |Φ+⟩ = (|00⟩ + |11⟩)/√2
        self._send_update(SimulationEventType.REPEATER_ENTANGLEMENT_INFO, type=InfoEventType.BELL_STATE_GENERATED, state=bell_state)

        # 2. Split the pair into two qubits
        qubit_to_keep = qt.ptrace(bell_state, 0)
        qubit_to_send = qt.ptrace(bell_state, 1)

        # 3. Store the local qubit and partner info
        self.entangled_qubit = qubit_to_keep
        self.entanglement_partner_address = target_host.name
        print(f"HOST {self.name}: Storing my half of the pair. State:\n{self.entangled_qubit}")

        # 4. Send the other qubit down the channel towards the repeater/target
        print(f"HOST {self.name}: Sending other half to the network.")
        channel.transmit_qubit(qubit_to_send, self)
        self._send_update(SimulationEventType.REPEATER_ENTANGLEMENT_INFO, type=InfoEventType.BELL_STATE_TRANSFERRED, state_kept=qubit_to_keep, state_sent=qubit_to_send, target=channel.get_other_node(self).name)

    def apply_entanglement_correction(self, message: dict):
        """Applies a Pauli correction based on the BSM result from a repeater."""
        if self.entangled_qubit is None:
            print(f"ERROR: Host {self.name} received correction but has no stored qubit.")
            return

        measurement_result = message["measurement_result"]
        other_node_addr = message["other_node_address"]

        # Verify the correction is for the right entanglement attempt
        if self.entanglement_partner_address != other_node_addr:
            print(f"WARNING: Received correction for a different partner.")
            return

        message = f"HOST {self.name}: Received correction message {measurement_result} for entanglement with {other_node_addr}."
        print(message)
        self._send_update(SimulationEventType.REPEATER_ENTANGLEMENT_INFO, **{
                'type':InfoEventType.APPLY_ENTANGLEMENT_CORRELATION,
                'message': message,
                'measurement_result': measurement_result,
                'other_node_address': other_node_addr,
            }
        )
        qubit_to_correct = self.entangled_qubit
        
        # Apply correction based on the classical bits (m1, m2)
        if measurement_result == (0, 0): # BSM outcome |Φ+⟩
            # No correction needed (Identity)
            print(f"HOST {self.name}: Applying I (no change).")
            pass
        elif measurement_result == (0, 1): # BSM outcome |Ψ+⟩
            # Apply Pauli-X
            print(f"HOST {self.name}: Applying Pauli-X correction.")
            self.entangled_qubit = qt.sigmax() * qubit_to_correct
        elif measurement_result == (1, 0): # BSM outcome |Φ-⟩
            # Apply Pauli-Z
            print(f"HOST {self.name}: Applying Pauli-Z correction.")
            self.entangled_qubit = qt.sigmaz() * qubit_to_correct
        elif measurement_result == (1, 1): # BSM outcome |Ψ-⟩
            # Apply Pauli-Y (Z followed by X)
            print(f"HOST {self.name}: Applying Pauli-Y (Z*X) correction.")
            self.entangled_qubit = qt.sigmax() * qt.sigmaz() * qubit_to_correct

        print(f"HOST {self.name}: Correction complete. Entanglement with {other_node_addr} established.")
        original_channel = self.get_channel()
        repeater = original_channel.get_other_node(self)
        if not isinstance(repeater, QuantumRepeater):
            print(f"ERROR: Host {self.name} is in 'entanglement_swapping' mode but no repeater found on channel.")
            return
        target = repeater.get_other_node(self)
        self.entangled_channel = QuantumChannel(
            self, 
            target,
            length=1.0,
            noise_model="none",
            noise_strength=0.0,
            loss_per_km=0,
            name=f"Entangled Channel {self.name} <-> {target.name}",
            num_bits=original_channel.num_bits
        )
        target.entangled_channel = self.entangled_channel   
        print(f"HOST {self.name}: Final local state:\n{self.entangled_qubit}")
        self._send_update(SimulationEventType.REPEATER_ENTANGLED, **{
            'entangled_qubit': self.entangled_qubit,
            'other_node_addr': other_node_addr,
            'measurement_result': measurement_result,
        })

        self.bb84_send_qubits()
        # Reset partner address for next round
        self.entanglement_partner_address = None

    def __name__(self):
        return f"QuantumHost - '{self.name}'"

    def __repr__(self):
        return self.__name__()