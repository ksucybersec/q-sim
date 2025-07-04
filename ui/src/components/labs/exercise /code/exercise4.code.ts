export const CODE = `
# =============================================================================
# NETWORK SETUP (READ-ONLY - Auto-generated from GUI)
# =============================================================================
from qutip import *
import numpy as np
from lab.base_lab import QSimLab

class TeleportationLab(QSimLab):
    def __init__(self):
        self.alice = self.get_host("Alice")  # QuantumHost
        self.bob = self.get_host("Bob")      # QuantumHost
        self.ent_source = self.get_host("EntSource")  # ClassicalHost
        self.adapter = self.get_adapter("Adapter")    # QuantumAdapter

    # ===========================
    # STUDENT IMPLEMENTATION AREA
    # ===========================
    def prepare_unknown_state(self):
        \"\"\"Create random qubit state for Alice to teleport\"\"\"
        # TODO: Generate random single-qubit state
        pass
        
    def create_bell_pair(self):
        \"\"\"Generate entangled Bell pair between Alice and Bob\"\"\"
        # TODO: Create |Φ+⟩ state using entanglement source
        pass
        
    def alice_bell_measurement(self):
        \"\"\"Perform Bell basis measurement\"\"\"
        # TODO: Joint measurement of unknown state + entangled qubit
        pass
        
    def bob_correction(self, measurement_results):
        \"\"\"Apply Pauli corrections\"\"\"
        # TODO: Apply gates based on Alice's measurement
        pass
`