import { SimulationNodeType } from "@/components/node/base/enums";
import { ExerciseI } from "./exercise";

const senderNodes = [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST];
const senderConnections = [[SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER], [SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER], [SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST]];

const receiverNodes = [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST];
const receiverConnections = [[SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER], [SimulationNodeType.CLASSICAL_ROUTER, SimulationNodeType.QUANTUM_ADAPTER], [SimulationNodeType.QUANTUM_ADAPTER, SimulationNodeType.QUANTUM_HOST]];

export const EXERCISE1: ExerciseI = {
    "id": "basic-network-construction",
    "title": "Basic Network Construction",
    "description": `
Create a hybrid classical-quantum network with adapters for connecting both sender and receiver paths.
This exercise introduces a fundamental concept in quantum networking. Since real-world quantum systems must interface with the existing classical internet, understanding this link is crucial. You'll learn how the **Quantum Adapter** acts as a key component to translate between *classical bits* and *quantum qubits*. By building a complete sender-to-receiver path, you will grasp the basic architecture required for any hybrid communication.
    `,
    "difficulty": "Beginner",
    "estimatedTime": "15 min",  
    "category": "hybrid",
    "steps": [
        "Drag a Classical Host (sender) from the left sidebar onto the canvas",
        "Add a Classical Router to connect to the sender host",
        "Place a Quantum Adapter to bridge classical and quantum domains",
        "Add a Quantum Host as the quantum endpoint for the sender path",
        "Create connections between these components in sequence (Classical Host → Router → Adapter → Quantum Host)",
        "Repeat the same process to create the receiver path with identical components",
        "Ensure all connections are properly established by checking connection indicators",
        "Run the simulation to observe data flow across both classical and quantum domains"
      ],
    "requirements": {
        "nodes": [...senderNodes, ...receiverNodes],
        "connections": [...senderConnections, ...receiverConnections],
        "simulation": true,
        "messages": 1
    },
    "tips": [
        "Make sure to create both sender and receiver paths completely for proper communication",
        "Quantum Adapters are essential for translating between classical and quantum protocols",
        "Pay attention to the direction of connections when linking components",
        "Try modifying parameters of the Quantum Adapter to see how it affects transmission quality"
    ]
}