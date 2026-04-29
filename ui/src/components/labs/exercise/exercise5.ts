import { CODE5 } from "./code/exercise5.code";
import { ExerciseI } from "./exercise";
export const EXERCISE5: ExerciseI = {
    id: "lab5-qkd-debugging",
    title: "Quantum Key Distribution Debugging (BB84 Protocol)",
    description: "Debug a BB84 quantum key distribution implementation containing quantum logic errors that compromise security. Focus on understanding quantum cryptographic principles and identifying protocol vulnerabilities.",
    difficulty: "Intermediate",
    estimatedTime: "35 minutes",
    category: "Debugging",
    steps: [
        "Review the buggy BB84 implementation with AI assistance",
        "Test the code and identify discrepancies between expected and actual behavior",
        "Debug basis reconciliation logic error that affects key generation",
        "Fix QBER security threshold that fails to detect eavesdropping",
        "Correct measurement basis implementation for diagonal measurements",
        "Fix privacy amplification formula to prevent information leakage",
        "Verify all fixes produce correct protocol behavior"
    ],
    requirements: {
        nodes: ["QuantumHost", "QuantumHost", "ClassicalHost"],
        connections: [
            ["QuantumHost", "QuantumHost"], // Alice-Bob quantum channel
            ["QuantumHost", "ClassicalHost"], // Alice-Classical
            ["QuantumHost", "ClassicalHost"]  // Bob-Classical
        ],
        simulation: true,
        entanglement: false,
        messages: 100
    },
    tips: [
        "BB84 basis reconciliation should only keep bits where Alice and Bob used the same basis",
        "QBER threshold of ~11% is theoretical limit for detecting eavesdropping",
        "Diagonal basis measurements require Hadamard transformation before measurement",
        "Privacy amplification must account for information leakage to eavesdropper",
        "Use AI to understand quantum security principles behind each bug"
    ],
    coding: {
        enabled: true,
        language: "python",
        scaffold: {
            code: CODE5,
            sections: [
                {
                    id: "basis_reconciliation_bug",
                    name: "Basis Reconciliation Debug",
                    type: "editable",
                    functionName: "basis_reconciliation",
                    description: "Fix logic error in basis matching"
                },
                {
                    id: "qber_threshold_bug", 
                    name: "QBER Threshold Debug",
                    type: "editable",
                    functionName: "detect_eavesdropping",
                    description: "Correct security threshold for eavesdropping detection"
                },
                {
                    id: "measurement_basis_bug",
                    name: "Measurement Basis Debug", 
                    type: "editable",
                    functionName: "bob_measure_qubit",
                    description: "Fix diagonal basis measurement implementation"
                },
                {
                    id: "privacy_amplification_bug",
                    name: "Privacy Amplification Debug",
                    type: "editable", 
                    functionName: "privacy_amplification",
                    description: "Correct secure key length calculation"
                },
                {
                    id: "protocol_execution",
                    name: "Protocol Execution",
                    type: "editable",
                    functionName: "run_protocol",
                    description: "Main BB84 implementation using debugged functions"
                },
                {
                    id: "analysis",
                    name: "Results Analysis",
                    type: "editable", 
                    functionName: "analyze_results",
                    description: "Analyze protocol performance and security metrics"
                }
            ],
            imports: [
                "import numpy as np",
                "import random", 
                "from qutip import *"
            ],
            classStructure: {
                className: "BB84DebuggingLab",
                readonlyMethods: [
                    "__init__",
                    "get_host_by_name", 
                    "get_channel_between",
                    "_collect_results"
                ],
                editableMethods: [
                    "basis_reconciliation",
                    "detect_eavesdropping", 
                    "bob_measure_qubit",
                    "privacy_amplification",
                    "run_protocol",
                    "alice_prepare_qubit",
                    "calculate_qber", 
                    "analyze_results"
                ],
                systemMethods: [
                    "_validate_setup",
                    "_generate_test_data"
                ]
            }
        },
        aiPrompts: [
            "Explain how BB84 basis reconciliation should work",
            "Why is my QBER detection not working?", 
            "What's wrong with diagonal basis measurements?",
            "How do I fix basis reconciliation logic?",
            "What's the correct QBER threshold for BB84?",
            "Why is my key generation rate so low?",
            "What information does Eve gain from intercepting qubits?",
            "How should Bob measure qubits in diagonal basis?",
            "Fix my privacy amplification algorithm"
        ],
        validation: {
            maxQubits: 20,
            allowedOperations: [
                "basis_state",
                "hadamard_transform", 
                "measure",
                "send_qubit",
                "prepare_qubit",
                "random.randint",
                "random.choice"
            ],
            blockedOperations: [
                "import_os",
                "exec",
                "eval", 
                "subprocess",
                "file_operations"
            ],
            timeLimit: 30
        }
    }
};