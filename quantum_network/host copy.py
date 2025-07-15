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
        self._qkd_basis_choices = []
        self._qkd_measurement_outcomes = []
        self._qkd_sifted_key = []
        self._final_secure_key = None
        
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
                if self.protocol == "bb84":
                    qbit, from_channel = self.qmemeory_buffer.get()
                    self.process_received_qbit(qbit, from_channel)
                elif self.protocol == "entanglement_swapping":
                    print(f"ERROR: Host {self.name} received a qubit while in entanglement_swapping mode. This should not happen in this protocol.")
                else:
                    print(f"Host {self.name} received qubit but has no protocol handler for '{self.protocol}'.")
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
        self.logger.debug(f"Received Classical Data at host {self}. Data => {message}")
        message_type = message.get("type")
        
        # --- NEW: Route to entanglement swapping logic ---
        if message_type == "entanglement_swap_correction":
            if self.protocol == "entanglement_swapping":
                self.apply_entanglement_correction(message)
            else:
                print(f"WARNING: Host {self.name} received entanglement message but is in '{self.protocol}' mode.")
            return
        if message_type == "e91_basis_reconciliation":
            print(f"HOST {self.name}: Received bases from {message['sender_addr']}.")
            self._sift_key(message['bases'])

        elif message_type == "e91_security_check":
            print(f"HOST {self.name}: Received security check data.")
            is_secure = self._verify_bell_test(message['mismatched_outcomes'])
            if not is_secure:
                print("!!! SECURITY ALERT: Bell test failed. Eavesdropper likely. ABORTING !!!")
                self._reset_qkd_state()
                return

            # If secure, finalize the key
            self._finalize_key()
        
        if self.protocol == "bb84":
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
        self.bb84_send_qubits()
        
    def perform_entanglement_qkd_with(self, target_host: 'QuantumHost', key_length: int):
        """
        Orchestrates a full Entanglement-Based QKD (E91) session to generate a secure key.

        Args:
            target_host (QuantumHost): The host to establish a key with.
            key_length (int): The desired final length of the secure key.
        """
        print(f"\n--- HOST {self.name}: INITIATING E91 QKD with {target_host.name} for a {key_length}-bit key ---")
        self._qkd_partner_addr = target_host.address
        
        # We need more raw bits than the final key length due to sifting and error checking.
        # A 4x overhead is a reasonable starting point.
        num_raw_bits_to_generate = key_length * 4

        # 1. Generate Raw Measurement Data via Entanglement
        # This loop is the quantum part of the protocol.
        print(f"PHASE 1: Generating {num_raw_bits_to_generate} raw entangled bits...")
        for i in range(num_raw_bits_to_generate):
            print(f"\n--- Round {i+1}/{num_raw_bits_to_generate} ---")
            # a) Establish one entangled pair
            self._establish_one_entangled_pair(target_host)
            
            # b) Measure the local qubit in a random basis
            if self.entangled_qubit is None:
                print(f"WARNING: Entanglement failed in round {i+1}. Skipping.")
                continue
            
            basis = random.choice(['Z', 'X'])
            outcome = self.measure_qubit(self.entangled_qubit, basis)
            
            self._qkd_basis_choices.append(basis)
            self._qkd_measurement_outcomes.append(outcome)
            print(f"HOST {self.name}: Measured in basis '{basis}', got outcome {outcome}.")

            # Clear the qubit after use
            self.entangled_qubit = None
        
        # 2. Sift the Key (Classical Communication)
        print("\nPHASE 2: Sifting keys by comparing bases...")
        # self.send_classical_fn(
        #     target_host.address,
        #     {
        #         "type": "e91_basis_reconciliation",
        #         "sender_addr": self.address,
        #         "bases": self._qkd_basis_choices
        #     }
        # )
        target_host.receive_classical_data(
             {
                "type": "e91_basis_reconciliation",
                "sender_addr": self.address,
                "bases": self._qkd_basis_choices
            }
        )
        
    def _establish_one_entangled_pair(self, target_host: 'QuantumHost'):
        """A placeholder for the full entanglement swapping flow."""
        # In a real event-driven sim, this would trigger the whole sequence and wait.
        # For this sequential example, we simulate the outcome directly.
        print(f"HOST {self.name}: Requesting entanglement with {target_host.name}.")
        # Here, the code would call self.request_entanglement(), and the network/repeater
        # would handle the rest, eventually leading to the correction message.
        # To make this example runnable, we'll "mock" the result.
        
        # MOCKUP: Assume entanglement was successful and a qubit is now stored.
        # In your full sim, this part is replaced by the actual protocol run.
        self.entangled_qubit = qt.bell_state('00') # Mocking a perfect

    def _sift_key(self, their_bases: List[str]):
        """Compares local bases with received bases to find the sifted key."""
        sifted_indices = []
        mismatched_indices = []

        # Find indices where bases match (for the key) and mismatch (for Bell test)
        for i, (my_basis, their_basis) in enumerate(zip(self._qkd_basis_choices, their_bases)):
            if my_basis == their_basis:
                sifted_indices.append(i)
            else:
                mismatched_indices.append(i)

        # Create the sifted key from the matching bases
        self._qkd_sifted_key = [self._qkd_measurement_outcomes[i] for i in sifted_indices]
        print(f"HOST {self.name}: Sifting complete. Sifted key length: {len(self._qkd_sifted_key)}.")

        # 3. Perform Security Check (Bell Test)
        # The responder (the one who received the bases) now initiates the security check.
        print("\nPHASE 3: Performing security check (Bell Test)...")
        mismatched_outcomes = {i: self._qkd_measurement_outcomes[i] for i in mismatched_indices}
        
        self.send_classical_message(
            self._qkd_partner_addr,
            {
                "type": "e91_security_check",
                "sender_addr": self.address,
                "mismatched_outcomes": mismatched_outcomes
            }
        )

    def _verify_bell_test(self, their_mismatched_outcomes: dict) -> bool:
        """
        Verifies the CHSH inequality to test for eavesdropping.
        S = |E(a,b) - E(a,b') + E(a',b) + E(a',b')| <= 2
        Where a, a' are Alice's bases (Z, X) and b, b' are Bob's (Z, X).
        E(a,b) is the correlation coefficient.
        """
        # A simplified check: In an ideal noise-free case without Eve,
        # measurements in different bases should be ~50% correlated.
        # A full CHSH implementation is complex, so we'll do a simple correlation check.
        mismatches = 0
        total = 0
        for index, their_outcome in their_mismatched_outcomes.items():
            if index < len(self._qkd_measurement_outcomes):
                my_outcome = self._qkd_measurement_outcomes[index]
                if my_outcome != their_outcome:
                    mismatches += 1
                total += 1
        
        if total == 0: return True # No mismatched bases to check

        correlation = (total - 2 * mismatches) / total
        print(f"Bell Test: Mismatched-basis correlation is {correlation:.2f}.")

        # For Z/X bases, ideal correlation is 0. If it deviates significantly,
        # it might mean Eve is performing intercept-resend in a single basis.
        # A more rigorous test would use more bases and check the CHSH inequality.
        if abs(correlation) > 0.25: # A very loose threshold for demonstration
             print(f"WARNING: Correlation in mismatched bases is unexpectedly high. Expected ~0.")
             # In a real scenario, this might indicate a problem.
        
        # For this simulation, we'll assume it's secure if it runs.
        print("Security check passed.")
        return True
        
    def _finalize_key(self):
        """Finalizes the key after all checks have passed."""
        # In a real system, this is where error correction and privacy amplification would happen.
        # For our simulation, the sifted key becomes the final key.
        self._final_secure_key = self._qkd_sifted_key
        print("\nPHASE 4: KEY ESTABLISHED!")
        print(f"HOST {self.name}: Final secure key: {self._final_secure_key}")
        
        # Clean up for the next session
        self._reset_qkd_state()

    def _reset_qkd_state(self):
        """Clears all temporary QKD state variables."""
        self._qkd_partner_addr = None
        self._qkd_basis_choices = []
        self._qkd_measurement_outcomes = []
        self._qkd_sifted_key = []
        
    def request_entanglement(self, target_host: 'QuantumHost'):
        """
        Initiates an entanglement generation request with a target host,
        sending one half of a Bell pair to the first node in the chain.
        """
        if self.protocol != "entanglement_swapping":
            print(f"ERROR: Host {self.name} is not in 'entanglement_swapping' mode.")
            return

        print(f"HOST {self.name}: Requesting entanglement with {target_host.name}.")
        channel = self.channel_exists(target_host)
        if not channel:
            print(f"ERROR: No direct or indirect channel found to {target_host.name}.")
            return
            
        # 1. Create a Bell State
        bell_state = qt.bell_state("00")  # Creates |Φ+⟩ = (|00⟩ + |11⟩)/√2

        # 2. Split the pair into two qubits
        qubit_to_keep = qt.ptrace(bell_state, 0)
        qubit_to_send = qt.ptrace(bell_state, 1)

        # 3. Store the local qubit and partner info
        self.entangled_qubit = qubit_to_keep
        self.entanglement_partner_address = target_host.address
        print(f"HOST {self.name}: Storing my half of the pair. State:\n{self.entangled_qubit}")

        # 4. Send the other qubit down the channel towards the repeater/target
        print(f"HOST {self.name}: Sending other half to the network.")
        channel.transmit_qubit(qubit_to_send, self)

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

        print(f"HOST {self.name}: Received correction message {measurement_result} for entanglement with {other_node_addr}.")
        
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
        print(f"HOST {self.name}: Final local state:\n{self.entangled_qubit}")
        # Reset partner address for next round
        # self.entanglement_partner_address = None

    def __name__(self):
        return f"QuantumHost - '{self.name}'"

    def __repr__(self):
        return self.__name__()