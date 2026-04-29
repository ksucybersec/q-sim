import { SimulationNodeType } from "@/components/node/base/enums";
import { ExerciseI } from "./exercise";

const senderNodes = [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST];
const senderConnections = [[SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER], [SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER], [SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST]];

const receiverNodes = [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST];
const receiverConnections = [[SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER], [SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER], [SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST]];

export const EXERCISE3: ExerciseI = {
    "id": "quantum-repeater-range-analysis",
    "title": "Quantum Repeater Range Analysis",
    "description": "Analyze the impact of distance on quantum communication and optimize repeater placement to improve quantum link quality. This exercise demonstrates why quantum communication faces fundamental distance limitations due to photon loss and decoherence, and how quantum repeaters enable long-distance quantum networks by creating intermediate entanglement points.",
    "difficulty": "Intermediate",
    "estimatedTime": "25 min",
    "category": "quantum",
    "steps": [
        "Place two Classical Hosts that will serve as message sender and receiver",
        "Add a Quantum Adapter connected to each Classical Host",
        "Place two Quantum Hosts and connect each to its respective Quantum Adapter",
        "Set a large distance between the Quantum Hosts in the detail panel",
        "Connect the Quantum Hosts with a direct Quantum Channel",
        "Run simulation and send a message from one Classical Host to another to observe high error rate",
        "Add a Quantum Repeater halfway between the Quantum Hosts",
        // "Configure repeater properties by setting memory capacity",
        "Run simulation with different distances between repeaters",
        "Record error rates at each distance configuration",
        "Find the optimal repeater placement for your hybrid network"
    ],
    "requirements": {
        "nodes": [...senderNodes, ...receiverNodes, SimulationNodeType.QUANTUM_REPEATER],
        "connections": [...senderConnections, ...receiverConnections, [SimulationNodeType.QUANTUM_HOST, SimulationNodeType.QUANTUM_REPEATER], [SimulationNodeType.QUANTUM_REPEATER, SimulationNodeType.QUANTUM_HOST]],
        simulation: true,
    },
    "tips": [
        "Error rates typically increase exponentially with distance in quantum channels",
        "The quality of the end-to-end communication depends on both the classical and quantum components",
        "Try multiple repeater configurations to find the optimal balance between performance and resources",
        // "Memory capacity of repeaters directly impacts their effectiveness at maintaining quantum coherence",
        "Document your findings in a graph showing the relationship between distance and error rate",
        "For practical applications, consider the trade-off between adding more repeaters versus accepting higher error rates"
    ]
}