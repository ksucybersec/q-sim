export const CODE5 = `
# =============================================================================
# NETWORK SETUP (READ-ONLY - Auto-generated from GUI)
# =============================================================================
from qutip import *
import numpy as np
import random
from lab.base_lab import QSimLab

class BB84DebuggingLab(QSimLab):
    # Define network topology
    classical_hosts = {
        "Classical": {"address": "classical_host", "location": (500, 300)}
    }
    
    quantum_hosts = {
        "Alice": {"address": "alice_host", "location": (200, 300)},
        "Bob": {"address": "bob_host", "location": (800, 300)}
    }
    
    connections = [
        {"from_host": "Alice", "to_host": "Classical"},
        {"from_host": "Bob", "to_host": "Classical"}
    ]
    
    def __init__(self):
        super().__init__()
        # Protocol data
        self.n_bits = 100
        self.alice_bits = []
        self.alice_bases = []
        self.bob_bases = []
        self.bob_measurements = []
        self.shared_key = []

    # =============================================================================
    # BUGGY IMPLEMENTATION AREA - DEBUG THESE FUNCTIONS
    # =============================================================================
    
    def basis_reconciliation(self):
        """Extract shared key from matching bases
        
        BUG: Currently keeps bits when bases DON'T match
        Should only keep bits where bases DO match
        """
        shared_key = []
        for i in range(len(self.alice_bases)):
            # LOGICAL BUG: Wrong condition - should be == not !=
            if self.alice_bases[i] != self.bob_bases[i]:
                shared_key.append(self.alice_bits[i])
        return shared_key
        
    def detect_eavesdropping(self):
        """Check quantum bit error rate for security
        
        BUG: Security threshold too high (25% vs theoretical 11%)
        Allows significant eavesdropping to go undetected
        """
        error_rate = self.calculate_qber()
        # LOGICAL BUG: Threshold should be ~0.11 for BB84
        if error_rate > 0.25:
            return "EAVESDROPPER DETECTED"
        return "SECURE"
        
    def bob_measure_qubit(self, qubit, basis):
        """Measure received qubit in chosen basis
        
        BUG: Missing Hadamard transformation for diagonal basis
        Diagonal basis measurements will be incorrect
        """
        if basis == 0:  # Computational basis {|0⟩, |1⟩}
            return qubit.measure()
        else:  # Diagonal basis {|+⟩, |-⟩}
            # LOGICAL BUG: Missing H gate before measurement
            # Should apply hadamard_transform(qubit) first
            return qubit.measure()
            
    def privacy_amplification(self, raw_key, error_estimate):
        """Extract secure key from raw key
        
        BUG: Wrong formula for secure key length
        Doesn't account for information leakage properly
        """
        # LOGICAL BUG: Should be len(raw_key) - 2*error_estimate - hash_bits
        secure_length = len(raw_key) - error_estimate
        return raw_key[:secure_length]

    # ===========================
    # STUDENT IMPLEMENTATION AREA
    # ===========================
    
    def run_protocol(self):
        """Main BB84 protocol execution"""
        # Get hosts using base class method
        alice = self.get_host("Alice")
        bob = self.get_host("Bob")
        classical = self.get_host("Classical")
        
        # Generate random bits and bases for Alice
        self.alice_bits = [random.randint(0, 1) for _ in range(self.n_bits)]
        self.alice_bases = [random.randint(0, 1) for _ in range(self.n_bits)]
        
        # Generate random bases for Bob
        self.bob_bases = [random.randint(0, 1) for _ in range(self.n_bits)]
        
        # Send qubits from Alice to Bob
        for i in range(self.n_bits):
            qubit = self.alice_prepare_qubit(self.alice_bits[i], self.alice_bases[i])
            # Use send_message for simulation
            self.send_message("Alice", "Bob", f"qubit_{i}")
            measurement = self.bob_measure_qubit(qubit, self.bob_bases[i])
            self.bob_measurements.append(measurement)
            
        # Extract shared key (BUGGY - needs debugging)
        self.shared_key = self.basis_reconciliation()
        
    def execute(self):
        """Execute method called by base class _run()"""
        print("Starting BB84 Debugging Lab...")
        self.run_protocol()
        return self.analyze_results()
        
    def alice_prepare_qubit(self, bit, basis):
        """Prepare qubit in specified basis"""
        if basis == 0:  # Computational basis
            if bit == 0:
                return basis(2, 0)  # |0⟩
            else:
                return basis(2, 1)  # |1⟩
        else:  # Diagonal basis
            if bit == 0:
                return (basis(2, 0) + basis(2, 1)).unit()  # |+⟩
            else:
                return (basis(2, 0) - basis(2, 1)).unit()  # |-⟩
                
    def calculate_qber(self):
        """Calculate Quantum Bit Error Rate"""
        if len(self.shared_key) == 0:
            return 0.0
            
        # Compare subset of shared bits to estimate error rate
        sample_size = min(20, len(self.shared_key))
        errors = 0
        
        for i in range(sample_size):
            if self.alice_bits[i] != self.bob_measurements[i]:
                errors += 1
                
        return errors / sample_size
        
    def analyze_results(self):
        """Analyze protocol performance and security"""
        print(f"Shared key length: {len(self.shared_key)} bits")
        print(f"Key generation rate: {len(self.shared_key) / self.n_bits:.2%}")
        print(f"QBER: {self.calculate_qber():.2%}")
        print(f"Security status: {self.detect_eavesdropping()}")
        
        # TODO: Add analysis of diagonal basis measurement statistics
        # TODO: Implement and test privacy amplification
        
        return {
            'shared_key_length': len(self.shared_key),
            'qber': self.calculate_qber(),
            'security_status': self.detect_eavesdropping(),
            'key_generation_rate': len(self.shared_key) / self.n_bits
        }
`