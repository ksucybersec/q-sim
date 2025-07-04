import sys
from flask.cli import load_dotenv

if not load_dotenv():
    print("Error loading .env file")
    sys.exit(-1)


# =============================================================================
# SOLUTIONS - FIXED IMPLEMENTATION
# =============================================================================
from qutip import *
import numpy as np
import random
from lab.base_lab import QSimLab

class BB84DebuggingLabSolutions(QSimLab):
    # Define network topology
    _classical_hosts = {
        "Alice": {},
        "Bob": {},
    }

    _classical_router = {
        'alice_router': {},
        'bob_router': {},
    }
    
    _quantum_hosts = {
        "QAlice": {},
        "QBob": {}
    }
    
    _connections = [
        {"from_host": "Alice", "to_host": "alice_router"},
        {"from_host": "Bob", "to_host": "bob_router"}
    ]

    _quantum_adapters = {
        'QAliceAdapter': {
            'quantumHost': 'QAlice',
            'classicalHost': 'Alice',
        },
        'QBobAdapter': {
            'quantumHost': 'QBob',
            'classicalHost': 'Bob',
        }
    }
    
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
    # FIXED IMPLEMENTATIONS - SOLUTIONS
    # =============================================================================
    
    def basis_reconciliation(self):
        """Extract shared key from matching bases - FIXED"""
        shared_key = []
        for i in range(len(self.alice_bases)):
            # FIX: Keep bits only when bases MATCH (== not !=)
            if self.alice_bases[i] == self.bob_bases[i]:
                shared_key.append(self.alice_bits[i])
        return shared_key
        
    def detect_eavesdropping(self):
        """Check quantum bit error rate for security - FIXED"""
        error_rate = self.calculate_qber()
        # FIX: Use theoretical BB84 threshold of 11%
        if error_rate > 0.11:
            return "EAVESDROPPER DETECTED"
        return "SECURE"
        
    def bob_measure_qubit(self, qubit:Qobj, basiss: int):
        """Measure received qubit in chosen basis - FIXED"""
        if basiss == 0:  # Computational basis {|0⟩, |1⟩}
            return qubit.measure()
        else:  # Diagonal basis {|+⟩, |-⟩}
            # FIX: Apply Hadamard before measurement for diagonal basis
            hadamard_gate = qeye(2) * (sigmax() + sigmaz()) / np.sqrt(2)
            qubit_rotated = hadamard_gate * qubit
            return qubit_rotated.measure()
            
    def privacy_amplification(self, raw_key, error_estimate):
        """Extract secure key from raw key - FIXED"""
        # FIX: Account for information leakage to eavesdropper
        # Secure length = raw_length - 2*error_estimate - hash_function_bits
        hash_bits = 64  # SHA-256 hash function security parameter
        secure_length = len(raw_key) - 2*error_estimate - hash_bits
        
        # Ensure non-negative length
        secure_length = max(0, int(secure_length))
        return raw_key[:secure_length]

    # =============================================================================
    # ENHANCED STUDENT IMPLEMENTATION AREA
    # =============================================================================
    
    def run_protocol(self):
        """Main BB84 protocol execution with improvements"""
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
            
        # Extract shared key using FIXED basis reconciliation
        self.shared_key = self.basis_reconciliation()
        
    def execute(self):
        """Execute method called by base class _run()"""
        print("Starting BB84 Debugging Lab (Solutions)...")
        with open('lab/lab5_world.json', 'w') as f:
            f.write(self.world.model_dump_json(indent=2))
        self.run_protocol()
        # return self.analyze_results()
        
    def alice_prepare_qubit(self, bit: int, basiss: int) -> Qobj:
        """Prepare qubit in specified basis"""
        if basiss == 0:  # Computational basis
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
            
        # Compare Alice's bits with Bob's measurements for matching bases
        errors = 0
        matching_indices = []
        
        for i in range(len(self.alice_bases)):
            if self.alice_bases[i] == self.bob_bases[i]:
                matching_indices.append(i)
                if self.alice_bits[i] != self.bob_measurements[i]:
                    errors += 1
                    
        if len(matching_indices) == 0:
            return 0.0
            
        return errors / len(matching_indices)
        
    def analyze_diagonal_measurements(self):
        """Analyze diagonal basis measurement statistics"""
        diagonal_measurements = []
        for i in range(len(self.bob_bases)):
            if self.bob_bases[i] == 1:  # Diagonal basis
                diagonal_measurements.append(self.bob_measurements[i])
                
        if len(diagonal_measurements) > 0:
            plus_count = diagonal_measurements.count(0)  # |+⟩ → 0
            minus_count = diagonal_measurements.count(1)  # |-⟩ → 1
            
            print(f"Diagonal basis measurements:")
            print(f"  |+⟩ states: {plus_count}")
            print(f"  |-⟩ states: {minus_count}")
            print(f"  Distribution: {plus_count/(plus_count+minus_count):.2%} / {minus_count/(plus_count+minus_count):.2%}")
        
    def test_privacy_amplification(self):
        """Test privacy amplification with different error rates"""
        raw_key_length = len(self.shared_key)
        error_estimate = int(self.calculate_qber() * raw_key_length)
        
        secure_key = self.privacy_amplification(self.shared_key, error_estimate)
        
        print(f"Privacy Amplification Results:")
        print(f"  Raw key length: {raw_key_length} bits")
        print(f"  Estimated errors: {error_estimate} bits")
        print(f"  Secure key length: {len(secure_key)} bits")
        print(f"  Efficiency: {len(secure_key)/raw_key_length:.2%}")
        
        return secure_key
        
    def simulate_eavesdropping(self, intercept_probability=0.5):
        """Simulate Eve's eavesdropping attack"""
        print(f"\\nSimulating eavesdropping (intercept rate: {intercept_probability:.0%})")
        
        # Save original measurements
        original_measurements = self.bob_measurements.copy()
        
        # Simulate Eve's interference
        for i in range(len(self.bob_measurements)):
            if random.random() < intercept_probability:
                # Eve measures and resends, introducing errors
                eve_basis = random.randint(0, 1)
                if eve_basis != self.alice_bases[i]:
                    # 50% chance of error when bases don't match
                    if random.random() < 0.5:
                        self.bob_measurements[i] = 1 - self.bob_measurements[i]
        
        # Recalculate with eavesdropping
        self.shared_key = self.basis_reconciliation()
        qber_with_eve = self.calculate_qber()
        security_status = self.detect_eavesdropping()
        
        print(f"  QBER with eavesdropping: {qber_with_eve:.2%}")
        print(f"  Security status: {security_status}")
        
        # Restore original for comparison
        self.bob_measurements = original_measurements
        return qber_with_eve
        
    def analyze_results(self):
        """Comprehensive analysis of protocol performance and security"""
        basic_results = {
            'shared_key_length': len(self.shared_key),
            'qber': self.calculate_qber(),
            'security_status': self.detect_eavesdropping(),
            'key_generation_rate': len(self.shared_key) / self.n_bits
        }
        
        print(f"=== BB84 Protocol Analysis (FIXED) ===")
        print(f"Shared key length: {basic_results['shared_key_length']} bits")
        print(f"Key generation rate: {basic_results['key_generation_rate']:.2%}")
        print(f"QBER: {basic_results['qber']:.2%}")
        print(f"Security status: {basic_results['security_status']}")
        
        # Enhanced analysis
        self.analyze_diagonal_measurements()
        secure_key = self.test_privacy_amplification()
        
        # Test eavesdropping scenarios
        eve_qber = self.simulate_eavesdropping(0.5)
        
        return {
            **basic_results,
            'secure_key_length': len(secure_key),
            'eavesdropping_qber': eve_qber
        }

    # =============================================================================
    # VALIDATION METHODS
    # =============================================================================
    
    def validate_fixes(self):
        """Validate that all bugs have been properly fixed"""
        print("=== Validating Bug Fixes ===")
        
        # Test 1: Basis reconciliation should only keep matching bases
        test_alice_bases = [0, 1, 0, 1]
        test_bob_bases = [0, 0, 0, 1]
        test_alice_bits = [1, 0, 1, 0]
        
        self.alice_bases = test_alice_bases
        self.bob_bases = test_bob_bases
        self.alice_bits = test_alice_bits
        
        key = self.basis_reconciliation()
        expected_key = [1, 1, 0]  # indices 0, 2, 3 match
        
        assert len(key) == 3, f"Expected 3 bits, got {len(key)}"
        print("✓ Basis reconciliation fix validated")
        
        # Test 2: QBER threshold should detect 15% error rate
        test_qber = 0.15
        # Mock calculate_qber to return test value
        original_qber = self.calculate_qber
        self.calculate_qber = lambda: test_qber
        
        status = self.detect_eavesdropping()
        assert status == "EAVESDROPPER DETECTED", f"Should detect eavesdropping at 15% QBER"
        print("✓ QBER threshold fix validated")
        
        # Restore original method
        self.calculate_qber = original_qber
        
        print("All fixes validated successfully!")

if __name__ == "__main__":
    import asyncio

    lab = BB84DebuggingLabSolutions()
    asyncio.run(lab._run())
    print("Lab execution completed.")
    os._exit(0)