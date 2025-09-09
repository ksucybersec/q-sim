from ai_agent.src.agents.topology_agent.structure import (
    OptimizeTopologyOutput,
    OptimizeTopologyRequest,
    SynthesisTopologyOutput,
    SynthesisTopologyRequest,
)
from data.models.topology.world_model import WorldModal


TEST_WORLD = [
    {
        "pk": "01JSMD3F6SZF664Y71V5Z5DCKG",
        "name": "My World",
        "size": [1704.87353515625, 1257.727027755322],
        "zones": [
            {
                "name": "Zone 0",
                "type": "SECURE",
                "size": [712.058837890625, 164.97709512260846],
                "position": [358.058837890625, 116.9779035300458],
                "networks": [
                    {
                        "name": "Network-1",
                        "address": "",
                        "type": "QUANTUM_NETWORK",
                        "location": [358.058837890625, 116.9779035300458],
                        "hosts": [
                            {
                                "name": "QuantumHost-8",
                                "type": "QuantumHost",
                                "address": "",
                                "location": [646.11767578125, 134.97709512260846],
                            },
                            {
                                "name": "QuantumHost-3",
                                "type": "QuantumHost",
                                "address": "",
                                "location": [337.11767578125, 131.9779035300458],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "QuantumHost-8",
                                "to_node": "QuantumHost-3",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.31,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "QuantumHost-8-QuantumHost-3",
                            }
                        ],
                    }
                ],
                "adapters": [
                    {
                        "name": "QuantumAdapter-6",
                        "type": "QuantumAdapter",
                        "address": "",
                        "location": [232.69091796875, 247.94664510913495],
                        "quantumHost": "QuantumHost-3",
                        "classicalHost": "ClassicalRouter-2",
                        "classicalNetwork": "Network-2",
                        "quantumNetwork": "Network-1",
                    },
                    {
                        "name": "QuantumAdapter-7",
                        "type": "QuantumAdapter",
                        "address": "",
                        "location": [669.69091796875, 287.9358663433037],
                        "quantumHost": "QuantumHost-8",
                        "classicalHost": "ClassicalRouter-4",
                        "classicalNetwork": "Network-3",
                        "quantumNetwork": "Network-1",
                    },
                ],
            },
            {
                "name": "Zone 1",
                "type": "SECURE",
                "size": [326.0, 700.2731689571546],
                "position": [172.34228515625, 410.8986796011857],
                "networks": [
                    {
                        "name": "Network-2",
                        "address": "",
                        "type": "CLASSICAL_NETWORK",
                        "location": [172.34228515625, 410.8986796011857],
                        "hosts": [
                            {
                                "name": "ClassicalRouter-2",
                                "type": "ClassicalRouter",
                                "address": "192.168.1.1",
                                "location": [246.40478515625, 425.8986796011857],
                            },
                            {
                                "name": "ClassicalHost-1",
                                "type": "ClassicalHost",
                                "address": "192.168.1.2",
                                "location": [187.34228515625, 631.8431689571545],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "ClassicalRouter-2",
                                "to_node": "ClassicalHost-1",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.21,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalRouter-2-ClassicalHost-1",
                            }
                        ],
                    }
                ],
                "adapters": [],
            },
            {
                "name": "Zone 2",
                "type": "SECURE",
                "size": [872.671142578125, 682.8455941794664],
                "position": [732.202392578125, 474.8814335758556],
                "networks": [
                    {
                        "name": "Network-3",
                        "address": "",
                        "type": "CLASSICAL_NETWORK",
                        "location": [732.202392578125, 474.8814335758556],
                        "hosts": [
                            {
                                "name": "ClassicalHost-5",
                                "type": "ClassicalHost",
                                "address": "192.168.1.1",
                                "location": [777.34228515625, 622.8455941794664],
                            },
                            {
                                "name": "ClassicalRouter-4",
                                "type": "ClassicalRouter",
                                "address": "192.168.1.2",
                                "location": [707.40478515625, 489.8814335758557],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "ClassicalHost-5",
                                "to_node": "ClassicalRouter-4",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.17,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalHost-5-ClassicalRouter-4",
                            }
                        ],
                    }
                ],
                "adapters": [],
            },
        ],
    }
]


OUTPUT_EXAMPLE = {
    "success": True,
    "error": None,
    "optimized_topology": {
        "pk": "01JSMD3F6SZF664Y71V5Z5DCKG",
        "name": "My World (Optimized)",
        "size": [1704.87353515625, 1257.727027755322],
        "zones": [
            {
                "name": "Zone 0",
                "type": "SECURE",
                "size": [712.058837890625, 164.97709512260846],
                "position": [358.058837890625, 116.9779035300458],
                "networks": [
                    {
                        "name": "Network-1",
                        "address": "",
                        "type": "QUANTUM_NETWORK",
                        "location": [358.058837890625, 116.9779035300458],
                        "hosts": [
                            {
                                "name": "QuantumHost-8",
                                "type": "QuantumHost",
                                "address": "",
                                "location": [646.11767578125, 134.97709512260846],
                            },
                            {
                                "name": "QuantumHost-3",
                                "type": "QuantumHost",
                                "address": "",
                                "location": [337.11767578125, 131.9779035300458],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "QuantumHost-8",
                                "to_node": "QuantumHost-3",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.31,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "QuantumHost-8-QuantumHost-3",
                            }
                        ],
                    }
                ],
                "adapters": [
                    {
                        "name": "QuantumAdapter-6",
                        "type": "QuantumAdapter",
                        "address": "",
                        "location": [232.69091796875, 247.94664510913495],
                        "quantumHost": "QuantumHost-3",
                        "classicalHost": "ClassicalRouter-2",
                        "classicalNetwork": "Network-2",
                        "quantumNetwork": "Network-1",
                    },
                    {
                        "name": "QuantumAdapter-7",
                        "type": "QuantumAdapter",
                        "address": "",
                        "location": [669.69091796875, 287.9358663433037],
                        "quantumHost": "QuantumHost-8",
                        "classicalHost": "ClassicalRouter-4",
                        "classicalNetwork": "Network-3",
                        "quantumNetwork": "Network-1",
                    },
                ],
            },
            {
                "name": "Zone 1",
                "type": "SECURE",
                "size": [326.0, 700.2731689571546],
                "position": [172.34228515625, 410.8986796011857],
                "networks": [
                    {
                        "name": "Network-2",
                        "address": "",
                        "type": "CLASSICAL_NETWORK",
                        "location": [172.34228515625, 410.8986796011857],
                        "hosts": [
                            {
                                "name": "ClassicalRouter-2",
                                "type": "ClassicalRouter",
                                "address": "192.168.1.1",
                                "location": [246.40478515625, 425.8986796011857],
                            },
                            {
                                "name": "ClassicalHost-1",
                                "type": "ClassicalHost",
                                "address": "192.168.1.2",
                                "location": [187.34228515625, 631.8431689571545],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "ClassicalRouter-2",
                                "to_node": "ClassicalHost-1",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.21,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalRouter-2-ClassicalHost-1",
                            },
                            {
                                "from_node": "ClassicalRouter-2",
                                "to_node": "ClassicalRouter-4",
                                "bandwidth": 1000,
                                "latency": 15,
                                "length": 0.48,
                                "loss_per_km": 0.05,
                                "noise_model": "default",
                                "name": "L-CR2-CR4-REDUNDANT",
                            },
                        ],
                    }
                ],
                "adapters": [],
            },
            {
                "name": "Zone 2",
                "type": "SECURE",
                "size": [872.671142578125, 682.8455941794664],
                "position": [732.202392578125, 474.8814335758556],
                "networks": [
                    {
                        "name": "Network-3",
                        "address": "",
                        "type": "CLASSICAL_NETWORK",
                        "location": [732.202392578125, 474.8814335758556],
                        "hosts": [
                            {
                                "name": "ClassicalHost-5",
                                "type": "ClassicalHost",
                                "address": "192.168.1.1",
                                "location": [777.34228515625, 622.8455941794664],
                            },
                            {
                                "name": "ClassicalRouter-4",
                                "type": "ClassicalRouter",
                                "address": "192.168.1.2",
                                "location": [707.40478515625, 489.8814335758557],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "ClassicalHost-5",
                                "to_node": "ClassicalRouter-4",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.17,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalHost-5-ClassicalRouter-4",
                            }
                        ],
                    }
                ],
                "adapters": [],
            },
        ],
    },
    "cost": 150.75,
    "original_topology": TEST_WORLD[0],
    "optimization_steps": [
        {
            "change_path": [
          "$.zones[1].networks[0].connections",
          "$.zones[2].networks[0].connections"
        ],
            "change": "Added a connection between ClassicalRouter-2 and ClassicalRouter-4.",
            "reason": "To provide classical redundancy and an alternative path between the two main classical network segments (Network-2 and Network-3), reducing reliance on the quantum network path via adapters for classical connectivity between routers.",
            "citation": ["Network Redundancy Principles"],
            "comments": "Assumed standard fiber link properties (1000 bandwidth, 15ms latency, calculated length) for the new connection. Cost estimate increased slightly.",
        },
        {
            "change_path": [
          "$.zones[1].networks[0].connections",
          "$.zones[2].networks[0].connections"
        ],
            "change": "Added a connection between ClassicalRouter-2 and ClassicalRouter-4.",
            "reason": "The primary goal was classical path redundancy based on general principles, as no specific instructions targeted the quantum segment.",
            "citation": None,
            "comments": "Existing quantum link bandwidth seems adequate based on provided data.",
        },
    ],
    "overall_feedback": "The topology is functional but could benefit from additional connections for redundancy and improved communication between classical networks.",
}

TOPOLOGY_OPTIMIZE_EXAMPLES = [
    {
        "input": OptimizeTopologyRequest(
            **{"world_id": "01JSMD3F6SZF664Y71V5Z5DCKG", "optional_instructions": None, 'conversation_id': '12345'}
        ),
        "extra_info": f"Sample world used for this example: {WorldModal(**TEST_WORLD[0]).model_dump_json()}",
        "output": OptimizeTopologyOutput(**OUTPUT_EXAMPLE),
    }
]


SYNTHESIZE_INPUT_EXAMPLE = {
    "user_query": "Create a classical network topology with 2 hosts connected via one router.", 
    'conversation_id': '12345'
}

SYNTHESIZE_OUTPUT_EXAMPLE = {
    "error": None,
    "success": True,
    "generated_topology": {
        "name": "My World",
        "size": [1059, 1129.43],
        "zones": [
            {
                "name": "Zone 0",
                "type": "SECURE",
                "size": [702.328857421875, 658.4300000000001],
                "position": [256.671142578125, 371],
                "networks": [
                    {
                        "name": "Network-1",
                        "address": "",
                        "type": "CLASSICAL_NETWORK",
                        "location": [256.671142578125, 371],
                        "hosts": [
                            {
                                "name": "ClassicalHost-2",
                                "type": "ClassicalHost",
                                "address": "192.168.1.1",
                                "location": [631.671142578125, 581],
                            },
                            {
                                "name": "ClassicalRouter-3",
                                "type": "ClassicalRouter",
                                "address": "192.168.1.2",
                                "location": [443.202392578125, 386],
                            },
                            {
                                "name": "ClassicalHost-1",
                                "type": "ClassicalHost",
                                "address": "192.168.1.3",
                                "location": [271.671142578125, 590],
                                "parentNetworkName": "Network-1",
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "ClassicalHost-2",
                                "to_node": "ClassicalRouter-3",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.27,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalHost-2-ClassicalRouter-3",
                            },
                            {
                                "from_node": "ClassicalHost-1",
                                "to_node": "ClassicalRouter-3",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.27,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalHost-1-ClassicalRouter-3",
                            },
                        ],
                    }
                ],
                "adapters": [],
            }
        ],
    },
    "overall_feedback": "Topology synthesized successfully.",
    "cost": 0.0,
    "thought_process": [
        "Created a classical network topology with 2 hosts connected via one router."
    ],
    "input_query": SYNTHESIZE_INPUT_EXAMPLE['user_query']
}

SYNTHESIZE_INPUT_EXAMPLE_1 = {
    "user_query": "Create a topology with 2 classical hosts connected via a quantum encryption channel and a classical router.",
    "conversation_id": '67898'
}

SYNTHESIZE_OUTPUT_EXAMPLE_1 = {
    "error": None,
    "success": True,
    "generated_topology": {
        "name": "My World",
        "size": [1629.7470703125, 1257.727027755322],
        "zones": [
            {
                "name": "Zone 0",
                "type": "SECURE",
                "size": [676.11767578125, 164.97709512260846],
                "position": [322.11767578125, 116.97790353004581],
                "networks": [
                    {
                        "name": "Network-1",
                        "address": "",
                        "type": "QUANTUM_NETWORK",
                        "location": [322.11767578125, 116.97790353004581],
                        "hosts": [
                            {
                                "name": "QuantumHost-8",
                                "type": "QuantumHost",
                                "address": "",
                                "location": [610.176513671875, 134.97709512260846],
                            },
                            {
                                "name": "QuantumHost-3",
                                "type": "QuantumHost",
                                "address": "",
                                "location": [301.176513671875, 131.9779035300458],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "QuantumHost-8",
                                "to_node": "QuantumHost-3",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.31,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "QuantumHost-8-QuantumHost-3",
                            }
                        ],
                    }
                ],
                "adapters": [
                    {
                        "name": "QuantumAdapter-6",
                        "type": "QuantumAdapter",
                        "address": "",
                        "location": [189.536376953125, 247.94664510913492],
                        "quantumHost": "QuantumHost-3",
                        "classicalHost": "ClassicalRouter-2",
                        "classicalNetwork": "Network-2",
                        "quantumNetwork": "Network-1",
                    },
                    {
                        "name": "QuantumAdapter-7",
                        "type": "QuantumAdapter",
                        "address": "",
                        "location": [626.536376953125, 287.9358663433037],
                        "quantumHost": "QuantumHost-8",
                        "classicalHost": "ClassicalRouter-4",
                        "classicalNetwork": "Network-3",
                        "quantumNetwork": "Network-1",
                    },
                ],
            },
            {
                "name": "Zone 1",
                "type": "SECURE",
                "size": [276.40478515625, 691.8431689571545],
                "position": [172.34228515625, 410.8986796011857],
                "networks": [
                    {
                        "name": "Network-2",
                        "address": "",
                        "type": "CLASSICAL_NETWORK",
                        "location": [172.34228515625, 410.8986796011857],
                        "hosts": [
                            {
                                "name": "ClassicalRouter-2",
                                "type": "ClassicalRouter",
                                "address": "192.168.1.1",
                                "location": [206.607177734375, 425.8986796011857],
                            },
                            {
                                "name": "ClassicalHost-1",
                                "type": "ClassicalHost",
                                "address": "192.168.1.2",
                                "location": [152.013427734375, 631.8431689571545],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "ClassicalRouter-2",
                                "to_node": "ClassicalHost-1",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.23,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalRouter-2-ClassicalHost-1",
                            }
                        ],
                    }
                ],
                "adapters": [],
            },
            {
                "name": "Zone 2",
                "type": "SECURE",
                "size": [837.34228515625, 682.8455941794664],
                "position": [692.40478515625, 474.8814335758557],
                "networks": [
                    {
                        "name": "Network-3",
                        "address": "",
                        "type": "CLASSICAL_NETWORK",
                        "location": [692.40478515625, 474.8814335758557],
                        "hosts": [
                            {
                                "name": "ClassicalHost-5",
                                "type": "ClassicalHost",
                                "address": "192.168.1.1",
                                "location": [742.013427734375, 622.8455941794664],
                            },
                            {
                                "name": "ClassicalRouter-4",
                                "type": "ClassicalRouter",
                                "address": "192.168.1.2",
                                "location": [667.607177734375, 489.8814335758557],
                            },
                        ],
                        "connections": [
                            {
                                "from_node": "ClassicalHost-5",
                                "to_node": "ClassicalRouter-4",
                                "bandwidth": 1000,
                                "latency": 10,
                                "length": 0.17,
                                "loss_per_km": 0.1,
                                "noise_model": "default",
                                "name": "ClassicalHost-5-ClassicalRouter-4",
                            }
                        ],
                    }
                ],
                "adapters": [],
            },
        ],
    },
    "overall_feedback": "Topology synthesized successfully.",
    "cost": 0.0,
    "thought_process": [
        "Created a classical network topology with 2 hosts connected via one router."
    ],
    "input_query": SYNTHESIZE_INPUT_EXAMPLE_1['user_query']
}


SYNTHESIZE_EXAMPLES = [
    # {
    #     "input": SynthesisTopologyRequest(**SYNTHESIZE_INPUT_EXAMPLE).model_dump_json(),
    #     "output": SynthesisTopologyOutput(
    #         **SYNTHESIZE_OUTPUT_EXAMPLE
    #     ).model_dump_json(),
    # },
    # {
    #     "input": SynthesisTopologyRequest(
    #         **SYNTHESIZE_INPUT_EXAMPLE_1
    #     ).model_dump_json(),
    #     "output": SynthesisTopologyOutput(
    #         **SYNTHESIZE_OUTPUT_EXAMPLE_1
    #     ).model_dump_json(),
    # },
]
