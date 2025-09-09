from dotenv import load_dotenv


if not load_dotenv():
    print("Error loading .env file")
    import sys

    sys.exit(-1)

from ai_agent.src.agents.topology_agent.parser import (
    convert_simplified_to_complex_with_layout,
)
from ai_agent.src.agents.topology_agent.structure import SynthesisTopologyOutput

from utils.visualize import visualize_network
from data.models.topology.summarizer import generate_topology_summary


generated_response = """
{
    "error": null,
    "success": true,
    "generated_topology": {
      "world_name": "Bank Secure Ledger Transfer",
      "nodes": [
        {"name": "HQ_Classical_Server", "type": "ClassicalHost", "network": "HQ_Classical_Net"},
        {"name": "HQ_Adapter", "type": "Adapter", "classical_network": "HQ_Classical_Net", "quantum_network": "Bank_Quantum_Backbone"},
        {"name": "HQ_Quantum_Host", "type": "QuantumHost", "network": "Bank_Quantum_Backbone"},
        {"name": "DC_Quantum_Host", "type": "QuantumHost", "network": "Bank_Quantum_Backbone"},
        {"name": "DC_Adapter", "type": "Adapter", "classical_network": "DC_Classical_Net", "quantum_network": "Bank_Quantum_Backbone"},
        {"name": "DC_Classical_Server", "type": "ClassicalHost", "network": "DC_Classical_Net"}
      ],
      "connections": [
        ["HQ_Classical_Server", "HQ_Adapter"],
        ["HQ_Adapter", "HQ_Quantum_Host"],
        ["HQ_Quantum_Host", "DC_Quantum_Host"],
        ["DC_Quantum_Host", "DC_Adapter"],
        ["DC_Adapter", "DC_Classical_Server"]
      ],
      "networks": [
        ["HQ_Classical_Net", "CLASSICAL_NETWORK"],
        ["DC_Classical_Net", "CLASSICAL_NETWORK"],
        ["Bank_Quantum_Backbone", "QUANTUM_NETWORK"]
      ],
      "zones": [
        {"name": "Bank_Secure_Zone", "networks": ["HQ_Classical_Net", "DC_Classical_Net", "Bank_Quantum_Backbone"]}
      ]
    },
    "overall_feedback": "This topology provides an ultra-secure, tamper-proof channel for financial ledger transfer between the bank's headquarters and a remote data center. It leverages a dedicated quantum network as the backbone, with each classical server connected via its own quantum adapter, ensuring end-to-end security.",
    "cost": 6000.00,
    "thought_process": [
      "The primary requirement is an ultra-secure, tamper-proof channel between two classical servers (HQ and Data Center).",
      "The solution must use a quantum network for the transfer.",
      "Identified the need for two `ClassicalHost` nodes: `HQ_Classical_Server` and `DC_Classical_Server`.",
      "Since classical hosts cannot directly connect to a quantum network, a dedicated `Adapter` is required for each classical endpoint: `HQ_Adapter` and `DC_Adapter`.",
      "Each adapter needs a corresponding `QuantumHost` to interface with the quantum network: `HQ_Quantum_Host` and `DC_Quantum_Host`.",
      "Established two `CLASSICAL_NETWORK` instances (`HQ_Classical_Net`, `DC_Classical_Net`) for the local classical environments.",
      "Created one central `QUANTUM_NETWORK` (`Bank_Quantum_Backbone`) to serve as the secure link.",
      "Defined connections to ensure the data flow: Classical Server -> Adapter -> Quantum Host -> Quantum Network -> Quantum Host -> Adapter -> Classical Server.",
      "Grouped all networks into a single `Bank_Secure_Zone` to represent the bank's secure infrastructure."
    ],
    "input_query": "A bank needs to set up an ultra-secure channel between its main headquarters and a remote data center for transferring financial ledgers. The server at the headquarters is classical, and the archival server at the data center is also classical. The plan is to use a quantum network for the transfer to ensure it's tamper-proof"
  }
"""


def test_llm_op():
    op = SynthesisTopologyOutput.model_validate_json(generated_response)
    cp = convert_simplified_to_complex_with_layout(op)
    # visualize_network(cp, 'test_sim.png')
    summ = generate_topology_summary(cp)

    print(summ)


if __name__ == "__main__":
    test_llm_op()
