import { SimulationNodeType } from "@/components/node/base/enums";
import { ExerciseI } from "./exercise";
import { CODE } from "./code/exercise4.code";

// Lab 4 Implementation
const teleportationNodes = [
    SimulationNodeType.QUANTUM_HOST, // Alice
    SimulationNodeType.QUANTUM_HOST, // Bob  
    SimulationNodeType.QUANTUM_ADAPTER, // For classical communication
    SimulationNodeType.CLASSICAL_HOST // For entanglement source role
];

const teleportationConnections = [
    [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.QUANTUM_HOST], // Source to Alice
    [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.QUANTUM_HOST], // Source to Bob
    [SimulationNodeType.QUANTUM_HOST, SimulationNodeType.QUANTUM_ADAPTER], // Alice to adapter
    [SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST]  // Adapter to Bob
];

export const EXERCISE4: ExerciseI = {
    id: "quantum-teleportation-protocol",
    title: "Quantum Teleportation Protocol Based Secure Communication",
    description: "Implement quantum teleportation using entanglement and classical communication",
    difficulty: "Intermediate",
    estimatedTime: "30 min",
    category: "quantum-protocols",
    steps: [
        "Place Alice (Quantum Host), Bob (Quantum Host), Classical Host (entanglement source), Quantum Adapter",
        "Connect Classical Host to both Alice and Bob for entanglement distribution",
        "Connect Alice to Bob via Quantum Adapter for classical communication",
        "Code: Implement prepare_unknown_state() method",
        "Code: Create Bell pair distribution in create_bell_pair()",
        "Code: Implement Alice's Bell measurement",
        "Code: Program Bob's corrections based on classical bits",
        "Verify teleportation fidelity"
    ],
    requirements: {
        "nodes": teleportationNodes,
        "connections": teleportationConnections,
        "simulation": true,
        "entanglement": true
    },
    tips: [
        "Use Classical Host as entanglement source",
        "Quantum Adapter handles classical bit transmission",
        "Perfect fidelity = 1.0 indicates successful teleportation"
    ],
    coding: {
        enabled: true,
        language: "python",
        scaffold: {
            code: CODE,
            sections: [
                {
                    id: "prepare-state",
                    name: "Prepare Unknown State",
                    // startLine: 18,
                    // endLine: 25,
                    functionName: "prepare_unknown_state",
                    type: "editable",
                    description: "Create random qubit state for Alice to teleport"
                },
                {
                    id: "bell-pair",
                    name: "Create Bell Pair",
                    // startLine: 26,
                    // endLine: 30,
                    functionName: "create_bell_pair",
                    type: "editable",
                    description: "Generate entangled Bell pair between Alice and Bob"
                },
                {
                    id: "alice-measurement",
                    name: "Alice Bell Measurement",
                    // startLine: 31,
                    // endLine: 35,
                    type: "editable",
                    functionName: "alice_bell_measurement",
                    description: "Perform Bell basis measurement"
                },
                {
                    id: "bob-correction",
                    name: "Bob Correction",
                    // startLine: 36,
                    // endLine: 40,
                    functionName: "bob_correction",
                    type: "editable",
                    description: "Apply Pauli corrections based on measurement"
                }
            ],
            imports: ["from qutip import *", "import numpy as np"],
            classStructure: {
                className: "TeleportationLab",
                readonlyMethods: ["__init__", "get_host", "get_adapter", "execute"],
                editableMethods: ["prepare_unknown_state", "create_bell_pair", "alice_bell_measurement", "bob_correction"],
                systemMethods: ["_validate_setup", "_collect_results"]
            }
        },
        aiPrompts: [
            "How do I create a random qubit state?",
            "Generate Bell pairs for teleportation",
            "Implement Bell basis measurement",
            "Apply Pauli corrections based on measurement"
        ],
        validation: {
            "maxQubits": 10,
            "allowedOperations": ["prepare_qubit", "apply_gate", "measure_qubit"],
            "blockedOperations": ["import", "exec", "eval"],
            "timeLimit": 30
        }
    }
}