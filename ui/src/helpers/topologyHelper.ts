import { SimulationNodeType } from "@/components/node/base/enums";
import { SimulatorNode } from "@/components/node/base/baseNode";
import { ConnectionManager } from "@/components/node/connections/connectionManager";

function getNeighbors(
  node: SimulatorNode,
  connectionManager: ConnectionManager
): SimulatorNode[] {
  const connections = connectionManager.getAllConnections();
  const neighbors: SimulatorNode[] = [];
  for (const c of connections) {
    if (c.metaData.from === node && c.metaData.to) neighbors.push(c.metaData.to);
    if (c.metaData.to === node && c.metaData.from) neighbors.push(c.metaData.from);
  }
  return neighbors;
}

function isClassicalType(t: SimulationNodeType): boolean {
  return t === SimulationNodeType.CLASSICAL_HOST || t === SimulationNodeType.CLASSICAL_ROUTER;
}

function isQuantumLinkType(t: SimulationNodeType): boolean {
  return t === SimulationNodeType.QUANTUM_HOST || t === SimulationNodeType.QUANTUM_REPEATER;
}

/**
 * Returns node types that are valid as a "next" connected node from the given node,
 * following validator rules (port limits, layer separation, no adapter-adapter).
 * Only returns validator-aligned types: ClassicalHost, ClassicalRouter, QuantumHost, QuantumRepeater, Adapter.
 */
export function getCompatibleNextNodeTypes(
  node: SimulatorNode,
  connectionManager: ConnectionManager
): SimulationNodeType[] {
  const neighbors = getNeighbors(node, connectionManager);
  const degree = neighbors.length;
  const neighborTypes = neighbors.map((n) => n.nodeType);

  switch (node.nodeType) {
    case SimulationNodeType.CLASSICAL_HOST:
    case SimulationNodeType.CLASSICAL_ROUTER:
      return [
        SimulationNodeType.CLASSICAL_HOST,
        SimulationNodeType.CLASSICAL_ROUTER,
        SimulationNodeType.QUANTUM_ADAPTER,
      ];

    case SimulationNodeType.QUANTUM_ADAPTER: {
      if (degree >= 2) return [];
      const hasClassical = neighborTypes.some(isClassicalType);
      const hasQuantum = neighborTypes.includes(SimulationNodeType.QUANTUM_HOST);
      // Exactly 2 ports: 1 Classical + 1 QuantumHost. Offer only the missing side.
      if (hasClassical && !hasQuantum) return [SimulationNodeType.QUANTUM_HOST];
      if (hasQuantum && !hasClassical)
        return [SimulationNodeType.CLASSICAL_HOST, SimulationNodeType.CLASSICAL_ROUTER];
      return [
        SimulationNodeType.CLASSICAL_HOST,
        SimulationNodeType.CLASSICAL_ROUTER,
        SimulationNodeType.QUANTUM_HOST,
      ];
    }

    case SimulationNodeType.QUANTUM_HOST: {
      if (degree >= 2) return [];
      const hasAdapter = neighborTypes.includes(SimulationNodeType.QUANTUM_ADAPTER);
      const hasQuantumLink = neighborTypes.some(isQuantumLinkType);
      // Exactly 2 ports: 1 Adapter + 1 quantum link (QHost or QRepeater). Offer only what's missing.
      if (hasAdapter && !hasQuantumLink)
        return [SimulationNodeType.QUANTUM_HOST, SimulationNodeType.QUANTUM_REPEATER];
      if (hasQuantumLink && !hasAdapter) return [SimulationNodeType.QUANTUM_ADAPTER];
      return [
        SimulationNodeType.QUANTUM_ADAPTER,
        SimulationNodeType.QUANTUM_HOST,
        SimulationNodeType.QUANTUM_REPEATER,
      ];
    }

    case SimulationNodeType.QUANTUM_REPEATER: {
      if (degree >= 2) return [];
      return [SimulationNodeType.QUANTUM_HOST, SimulationNodeType.QUANTUM_REPEATER];
    }

    default:
      return [];
  }
}
