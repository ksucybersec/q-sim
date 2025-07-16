import { ExportDataI } from "@/services/export.interface";
import { ExerciseI } from "../labs/exercise /exercise";
import { AgentID, AgentTask } from "./agent-declaration";
import { AgentResponse } from "./agent_response";

export interface ChatAttachmentI {
    type: string;
    name: string;
    preview: string;
}

export interface ChatMessageI<T = AgentResponse> {
    id: string;
    role: "system" | "user" | "agent";
    content: string;
    timestamp: string;
    mentionedAgent?: string;
    agentId?: AgentID;
    taskId?: AgentTask;
    referencedAgents?: AgentID[];
    attachments?: ChatAttachmentI[];
    agentResponse?: T;
}

export interface ChatRequestI {
    conversation_id: string;
    agent_id: AgentID;
    task_id?: AgentTask;
    user_query: string;
    tags?: string[];
}

export interface LogAgentRequest extends ChatRequestI {
    simulation_id: string;
}

export interface TopologyOptimizerRequest extends ChatRequestI {
    world_id: string;
    optional_instructions?: string;
}

export interface TopologyGenerationRequest extends ChatRequestI {
}

export interface AgentRouterRequest extends ChatRequestI {
    extra_kwargs: any
}

export interface LabAssistantRequest extends ChatRequestI {
    student_code: string
    cursor_line_number: number
}

export interface LabPeerAgentInput extends ChatRequestI {
    lab_instructions: ExerciseI
    current_topology?: ExportDataI
}

type ResponseType = "direct_answer" | "guided_discovery" | "hint";

export interface LabPeerAgentOutput {
  response: string;
  confidence_score?: number; // Optional, must be between 0.0 and 1.0
  thought_process: string;
  response_type: ResponseType;
}
