import { SimulationNodeType } from "@/components/node/base/enums";
import { ExerciseI } from "./exercise";

const senderNodes = [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST];
const senderConnections = [[SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER], [SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER], [SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST]];

const receiverNodes = [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST];
const receiverConnections = [[SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER], [SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER], [SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST]];


export const EXERCISE2: ExerciseI = {
    "id": "quantum-key-distribution-eavesdropper",
    "title": "Quantum Key Distribution with Eavesdropper",
    "description": "Build a QKD setup between two quantum hosts and observe how an eavesdropper is detected through quantum measurement disturbance. This exercise demonstrates why quantum cryptography is fundamentally more secure than classical methods. Any attempt to intercept quantum information inevitably disturbs the quantum states, alerting the communicating parties to the presence of an eavesdropper.",
    "difficulty": "Intermediate",
    "estimatedTime": "20 min",
    "category": "quantum",
    "steps": [
        "Place two Quantum Hosts on opposite sides of the canvas",
        "Connect them with a Quantum Channel (with simple Classical Hosts on each end)",
        "Set up QKD protocol in properties panel by selecting the first Quantum Host and setting key length to 128 bits",
        "Add a third Quantum Host labeled 'Eavesdropper'",
        "Add the Eavesdropper to the Quantum Channel",
        "Run simulation and observe the key generation process, increased error rates when eavesdropper is active, and failed key verification"
    ],
    "requirements": {
        "nodes": [
            ...senderNodes,
            ...receiverNodes,
            SimulationNodeType.QUANTUM_HOST,
        ],
        "connections": [
            ...senderConnections,
            ...receiverConnections,
            [SimulationNodeType.QUANTUM_HOST, SimulationNodeType.QUANTUM_HOST],
            [SimulationNodeType.QUANTUM_HOST, SimulationNodeType.QUANTUM_HOST],
            [SimulationNodeType.QUANTUM_HOST, SimulationNodeType.QUANTUM_HOST],
        ],
        simulation: true,
        // "qkd": true,
        // "eavesdropper": true
    },
    "tips": [
        "Pay attention to the error rate display when the eavesdropper is active versus inactive",
        "Try different key lengths to see how it affects detection probability",
        "Experiment with different positions of the eavesdropper in the quantum channel",
        "Note how the security of quantum key distribution relies on the fundamental properties of quantum measurement"
    ]
}