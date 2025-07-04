SOLUTION_CODE_LAB_4 = '''
# =============================================================================
# NETWORK SETUP (READ-ONLY - Auto-generated from GUI)
# =============================================================================
from qutip import *
import numpy as np
import random

class TeleportationLab:
   def __init__(self):
       self.alice = self.get_host("Alice")  # QuantumHost
       self.bob = self.get_host("Bob")      # QuantumHost
       self.ent_source = self.get_host("EntSource")  # ClassicalHost
       self.adapter = self.get_adapter("Adapter")    # QuantumAdapter
       
       # Store states for verification
       self.original_state = None
       self.teleported_state = None
       self.measurement_results = None
   
   def get_host(self, name): pass
   def get_adapter(self, name): pass
   
   def execute(self):
       """Execute complete teleportation protocol"""
       self.original_state = self.prepare_unknown_state()
       self.create_bell_pair()
       self.measurement_results = self.alice_bell_measurement()
       self.send_classical_bits(self.measurement_results)
       self.bob_correction(self.measurement_results)
       return self.verify_teleportation()

# =============================================================================
# STUDENT IMPLEMENTATION AREA - SOLUTION
# =============================================================================
   def prepare_unknown_state(self):
       """Create random qubit state for Alice to teleport"""
       # Generate random normalized coefficients
       theta = random.uniform(0, np.pi)
       phi = random.uniform(0, 2*np.pi)
       
       alpha = np.cos(theta/2)
       beta = np.exp(1j*phi) * np.sin(theta/2)
       
       # Create state |ψ⟩ = α|0⟩ + β|1⟩
       psi = alpha * basis(2, 0) + beta * basis(2, 1)
       
       print(f"Original state: α={alpha:.3f}, β={beta:.3f}")
       return psi
       
   def create_bell_pair(self):
       """Generate entangled Bell pair between Alice and Bob"""
       # Create |Φ+⟩ = (|00⟩ + |11⟩)/√2
       bell_state = (tensor(basis(2,0), basis(2,0)) + 
                    tensor(basis(2,1), basis(2,1))) / np.sqrt(2)
       
       # Alice gets first qubit, Bob gets second
       self.alice_entangled = ptrace(bell_state, 0)
       self.bob_entangled = ptrace(bell_state, 1)
       
       print("Bell pair created: |Φ+⟩ = (|00⟩ + |11⟩)/√2")
       return bell_state
       
   def alice_bell_measurement(self):
       """Perform Bell basis measurement on Alice's qubits"""
       # Create 3-qubit system: |unknown⟩ ⊗ |Alice_entangled⟩ ⊗ |Bob_entangled⟩
       system = tensor(self.original_state, self.alice_entangled, self.bob_entangled)
       
       # Bell basis measurement on first two qubits
       # Simulate measurement by projecting onto Bell basis states
       bell_basis = [
           (tensor(basis(2,0), basis(2,0)) + tensor(basis(2,1), basis(2,1)))/np.sqrt(2),  # |Φ+⟩
           (tensor(basis(2,0), basis(2,0)) - tensor(basis(2,1), basis(2,1)))/np.sqrt(2),  # |Φ-⟩
           (tensor(basis(2,0), basis(2,1)) + tensor(basis(2,1), basis(2,0)))/np.sqrt(2),  # |Ψ+⟩
           (tensor(basis(2,0), basis(2,1)) - tensor(basis(2,1), basis(2,0)))/np.sqrt(2)   # |Ψ-⟩
       ]
       
       # Randomly select measurement outcome (in practice, determined by quantum mechanics)
       outcome = random.randint(0, 3)
       
       # Convert to classical bits
       bit1 = outcome // 2
       bit2 = outcome % 2
       
       print(f"Alice measures: ({bit1}, {bit2})")
       return (bit1, bit2)
       
   def send_classical_bits(self, measurement_results):
       """Send Alice's measurement results to Bob"""
       # Use quantum adapter for classical communication
       self.adapter.send_classical_message(measurement_results)
       print(f"Classical bits sent: {measurement_results}")
       
   def bob_correction(self, measurement_results):
       """Apply Pauli corrections based on Alice's results"""
       bit1, bit2 = measurement_results
       
       # Start with Bob's entangled qubit state
       corrected_state = self.bob_entangled
       
       # Apply corrections based on measurement outcomes
       if bit2 == 1:  # Apply X gate
           corrected_state = sigmax() * corrected_state
           print("Applied X correction")
           
       if bit1 == 1:  # Apply Z gate  
           corrected_state = sigmaz() * corrected_state
           print("Applied Z correction")
           
       self.teleported_state = corrected_state
       return corrected_state
       
   def verify_teleportation(self):
       """Compare original and teleported states"""
       # Calculate fidelity F = |⟨ψ_original|ψ_teleported⟩|²
       overlap = self.original_state.dag() * self.teleported_state
       fidelity = abs(overlap[0,0])**2
       
       print(f"Teleportation fidelity: {fidelity:.6f}")
       
       if fidelity > 0.99:
           print("✓ TELEPORTATION SUCCESSFUL")
           return True
       else:
           print("✗ Teleportation failed")
           return False

# Example execution
lab = TeleportationLab()
success = lab.execute()
'''