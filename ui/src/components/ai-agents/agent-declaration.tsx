import {
    Network,
    AlertTriangle,
    BarChart2,
    Cpu,
    Book
} from "lucide-react"
import { JSX } from "react/jsx-runtime";

export interface AgentI {
    id: AgentID;
    name: string;
    description: string;
    icon: JSX.Element;
    color: string;
    textColor: string;
    borderColor: string;
    type: "active" | "passive";
    inputs: string[];
    outputs: string[];
}

export enum AgentID {
    TOPOLOGY_DESIGNER = "topology_designer",
    CONGESTION_MONITOR = "congestion_monitor",
    PERFORMANCE_ANALYZER = "performance_analyzer",
    COMPOUND_AI_ARCHITECT = "compound_ai_architect",
    ORCHESTRATOR = "orchestrator",
    LOG_SUMMARIZER = "log_summarizer",
    LAB_ASSISTANT_AGENT = "lab_assistant_agent"
}

export enum AgentTask {
    LOG_SUMMARIZATION = "summarize",
    LOG_QNA = "log_qna",
    EXTRACT_PATTERNS = "extract_patterns",
    OPTIMIZE_TOPOLOGY = "optimize_topology",
    SYNTHESIZE_TOPOLOGY = "synthesize_topology",
    TOPOLOGY_QNA = "topology_qna",
    LAB_PEER = "lab_peer"
}

export const AGENT_DEFINITION: AgentI[] = [
    {
        id: AgentID.TOPOLOGY_DESIGNER,
        name: "Topology Designer",
        description: "Creates optimal network architectures with built-in congestion prevention",
        icon: <Network className="h-5 w-5" />,
        color: "bg-blue-500",
        textColor: "text-blue-500",
        borderColor: "border-blue-500",
        type: "active",
        inputs: [
            "Configuration file (JSON): network parameters",
            "Historical simulation data (CSV): past congestion patterns",
        ],
        outputs: [
            "Network topology graph (JSON): node connections with credit allocations",
            "Congestion prediction heatmap (PNG)",
        ],
    },
    // {
    //     id: AgentID.CONGESTION_MONITOR,
    //     name: "Congestion Monitor",
    //     description: "Detects decoherence and congestion in Q networks in real-time",
    //     icon: <AlertTriangle className="h-5 w-5" />,
    //     color: "bg-amber-500",
    //     textColor: "text-amber-500",
    //     borderColor: "border-amber-500",
    //     type: "passive",
    //     inputs: ["Real-time FLIT transmission data (stream)", "Q network state snapshot (binary)"],
    //     outputs: [
    //         "Congestion alerts (JSON): timestamp, location, severity",
    //         "Interactive network visualization (HTML/PNG)",
    //     ],
    // },
    // {
    //     id: AgentID.PERFORMANCE_ANALYZER,
    //     name: "Performance Analyzer",
    //     description: "Evaluates network efficiency and generates improvement recommendations",
    //     icon: <BarChart2 className="h-5 w-5" />,
    //     color: "bg-green-500",
    //     textColor: "text-green-500",
    //     borderColor: "border-green-500",
    //     type: "passive",
    //     inputs: ["Complete simulation log (CSV/JSON Array): all network events", "Initial topology configuration (JSON)"],
    //     outputs: ["Performance metrics dashboard (HTML/PNG)", "Topology improvement recommendations (JSON)"],
    // },
    // {
    //     id: AgentID.COMPOUND_AI_ARCHITECT,
    //     name: "Compound AI Architect",
    //     description: "Orchestrates multiple AI agents to design optimized system topologies",
    //     icon: <Cpu className="h-5 w-5" />,
    //     color: "bg-purple-500",
    //     textColor: "text-purple-500",
    //     borderColor: "border-purple-500",
    //     type: "active",
    //     inputs: [
    //         "Agent library specifications (JSON): capabilities of available agent types",
    //         "Simulation requirements (JSON): performance targets and constraints",
    //         "Historical simulation metrics (CSV): previous outcomes",
    //     ],
    //     outputs: [
    //         "Multi-agent deployment plan (JSON): agents used and resulting topology with explanations",
    //         "FLIT traffic forecast report (CSV): predicted communication pattern",
    //     ],
    // },
    {
        id: AgentID.LOG_SUMMARIZER,
        name: "Log Summarizer",
        description: "Aggregates and summarizes network logs for quick analysis and reporting",
        icon: <Book className="h-5 w-5" />,
        color: "bg-gray-500",
        textColor: "text-gray-500",
        borderColor: "border-gray-500",
        type: "passive",
        inputs: ["Raw network logs (JSON/CSV): detailed event data"],
        outputs: [
            "Summary report (HTML): key metrics and anomalies",
            "Aggregated log data (JSON): structured and filtered logs",
        ],
    },
];