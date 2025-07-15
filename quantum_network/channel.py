from __future__ import annotations
import random
import time
import qutip as qt
import numpy as np
from typing import TYPE_CHECKING, Union

# from core.base_classes import Node
from core.enums import SimulationEventType
from core.exceptions import QubitLossError
from core.s_object import Sobject

if TYPE_CHECKING:
    from quantum_network.node import QuantumNode

class QuantumChannel(Sobject):
    def __init__(
        self,
        node_1: QuantumNode,
        node_2: QuantumNode,
        length: float,
        loss_per_km: float,
        noise_model: str,
        noise_strength: float = 0.01,
        name: str = "",
        description: str = "",
        error_rate_threshold: float = 10.0,
        num_bits: int = 16
    ) -> None:
        super().__init__(name, description)
        self.node_1 = node_1
        self.node_2 = node_2
        self.length = length
        self.loss_per_km = loss_per_km
        self.noise_model = noise_model
        self.noise_strength = noise_strength
        self.error_rate_threshold = error_rate_threshold
        self.num_bits = num_bits

    def __name__(self) -> str:
        return f"{self.node_1.name} <~~~> {self.node_2.name}"

    def __repr__(self) -> str:
        return self.__name__()

    def transmit_qubit(self, qubit: qt.Qobj, from_node: QuantumNode, noise_strength: float = None) -> None:
        # Use provided noise strength or default to channel's setting
        if noise_strength is None:
            noise_strength = self.noise_strength
            
        if self.noise_model != 'none':
            # Simulate the loss based on length and loss_per_km
            length_km = self.length
            loss_prob = 1 - (1 - self.loss_per_km) ** length_km
            loss_prod_rand = random.random()
            if loss_prod_rand < loss_prob:
                reason = f"Qubit lost during transmission in connection {self.name} over {length_km} km. (Loss probability: {loss_prob:.2f})"
                self.logger.error(f"{reason} Loss probability: {loss_prob:.2f}. Random value: {loss_prod_rand:.2f}")
                self._send_update(
                    SimulationEventType.QUBIT_LOST,
                    reason=reason
                )
                raise QubitLossError(self, qubit)

            # Apply noise to the qubit (using QuTiP)
            noisy_qubit = self.apply_noise(qubit, noise_strength)
        else:
            noisy_qubit = qubit

        # Send the qubit to the destination node
        to_node = self.node_2 if self.node_1 == from_node else self.node_1
        
        to_node.receive_qubit(noisy_qubit, self)

    def log(self, message: str) -> None:
        """Simple logging function - to be updated later"""
        print(f"[QuantumChannel] {message}")

    def get_other_node(self, node):
        return self.node_2 if self.node_1 == node else self.node_1
    
    def apply_noise(self, qubit: qt.Qobj, noise_strength: float = None) -> qt.Qobj:
        """Apply noise based on the channel's noise model"""
        if noise_strength is None:
            noise_strength = self.noise_strength
            
        self.log(f"Applying {self.noise_model} noise to qubit (strength: {noise_strength})")
        
        if self.noise_model == "transmutation":
            return self._apply_transmutation_noise(qubit, noise_strength)
        elif self.noise_model == "depolarizing":
            return self._apply_depolarizing_noise(qubit, noise_strength)
        elif self.noise_model == "amplitude_damping":
            return self._apply_amplitude_damping(qubit, noise_strength)
        elif self.noise_model == "phase_damping":
            return self._apply_phase_damping(qubit, noise_strength)
        else:
            self.log("No noise model specified - returning original qubit")
            # Ensure we always return a qt.Qobj
            if isinstance(qubit, qt.Qobj):
                return qubit
            else:
                # Convert to qt.Qobj if it's not already
                return qt.Qobj(qubit)

    def _apply_transmutation_noise(self, qubit: qt.Qobj, p_flip: float) -> qt.Qobj:
        """Apply bit-flip (transmutation) noise"""
        # Ensure input is a qt.Qobj
        if not isinstance(qubit, qt.Qobj):
            qubit = qt.Qobj(qubit)
            
        if random.random() < p_flip:
            self.log(f"Bit-flip occurred with probability {p_flip}")
            # Apply Pauli-X (bit flip)
            return qt.sigmax() * qubit
        else:
            self.log(f"No bit-flip (probability was {p_flip})")
            return qubit

    def _apply_depolarizing_noise(self, qubit: qt.Qobj, p: float) -> qt.Qobj:
        """Apply depolarizing noise using Kraus operators"""
        self.log(f"Applying depolarizing noise with strength {p}")
        
        # Ensure input is a qt.Qobj
        if not isinstance(qubit, qt.Qobj):
            qubit = qt.Qobj(qubit)
        
        if qubit.isket:
            # Convert to density matrix
            rho = qubit * qubit.dag()
        else:
            rho = qubit
        
        # Depolarizing channel Kraus operators
        E0 = np.sqrt(1 - 3*p/4) * qt.qeye(2)
        E1 = np.sqrt(p/4) * qt.sigmax()
        E2 = np.sqrt(p/4) * qt.sigmay()
        E3 = np.sqrt(p/4) * qt.sigmaz()
        
        kraus_ops = [E0, E1, E2, E3]
        noisy_rho = sum(E * rho * E.dag() for E in kraus_ops)
        
        # Ensure we return a qt.Qobj even if sum resulted in scalar
        if not isinstance(noisy_rho, qt.Qobj):
            noisy_rho = qt.Qobj(noisy_rho)
        
        self.log("Depolarizing noise applied successfully")
        return noisy_rho

    def _apply_amplitude_damping(self, qubit: qt.Qobj, gamma: float) -> qt.Qobj:
        """Apply amplitude damping noise"""
        self.log(f"Applying amplitude damping with gamma={gamma}")
        
        # Ensure input is a qt.Qobj
        if not isinstance(qubit, qt.Qobj):
            qubit = qt.Qobj(qubit)
        
        if qubit.isket:
            rho = qubit * qubit.dag()
        else:
            rho = qubit
        
        # Amplitude damping Kraus operators
        E0 = qt.Qobj([[1, 0], [0, np.sqrt(1-gamma)]])
        E1 = qt.Qobj([[0, np.sqrt(gamma)], [0, 0]])
        
        kraus_ops = [E0, E1]
        noisy_rho = sum(E * rho * E.dag() for E in kraus_ops)
        
        # Ensure we return a qt.Qobj even if sum resulted in scalar
        if not isinstance(noisy_rho, qt.Qobj):
            noisy_rho = qt.Qobj(noisy_rho)
        
        self.log("Amplitude damping applied successfully")
        return noisy_rho

    def _apply_phase_damping(self, qubit: qt.Qobj, gamma: float) -> qt.Qobj:
        """Apply phase damping noise"""
        self.log(f"Applying phase damping with gamma={gamma}")
        
        # Ensure input is a qt.Qobj
        if not isinstance(qubit, qt.Qobj):
            qubit = qt.Qobj(qubit)
        
        if qubit.isket:
            rho = qubit * qubit.dag()
        else:
            rho = qubit
        
        # Phase damping Kraus operators
        E0 = qt.Qobj([[1, 0], [0, np.sqrt(1-gamma)]])
        E1 = qt.Qobj([[0, 0], [0, np.sqrt(gamma)]])
        
        kraus_ops = [E0, E1]
        noisy_rho = sum(E * rho * E.dag() for E in kraus_ops)
        
        # Ensure we return a qt.Qobj even if sum resulted in scalar
        if not isinstance(noisy_rho, qt.Qobj):
            noisy_rho = qt.Qobj(noisy_rho)
        
        self.log(f"Phase damping applied successfully. Before: {rho}, After: {noisy_rho}")
        return noisy_rho