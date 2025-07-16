import { AgentID, AgentTask } from "@/components/ai-agents/agent-declaration";
import { UserEventType } from "./userEvents.enums";

export interface UserEventData {
    // Core Event Data
    user_id: string;
    session_id: string;
    event_type: UserEventType;
    timestamp: Date | number;

    // Context
    page_url?: string;
    module_name?: string;
    world_id?: string;
    simulation_id?: string;
    lab_id?: string;
    // TODO: Check type
    component_type?: string;

    // Interaction Details
    click_coordinates?: { x: number; y: number };
    element_id?: string;
    element_type?: string;
    element_description?: string;

    // Component/Lab Specific
    component_id?: string;
    connection_from?: string;
    connection_to?: string;
    lab_step?: number | string | null;
    lab_progress?: number;

    // AI Help Analytics
    agent_message?: string;
    agent_response?:  Record<string, any>;
    agent_id?: AgentID;
    task_id?: AgentTask;
    ai_message_extra_data?: Record<string, any>;
    conversation_id?: string;
    conversation_context?: Record<string, any>;
    help_category?: string; // "conceptual", "procedural", "troubleshooting"
    help_effectiveness?: number; // 1-5 rating after task completion
    pre_help_attempts?: number; // failed attempts before asking AI
    post_help_success?: boolean; // did student succeed after AI help
    help_sequence_id?: string; // links related help interactions
    question_complexity?: number; // 1-5 scale
    response_type?: string; // "direct_answer", "guided_discovery", "hint"
    time_to_apply_advice?: number; // ms between help and implementation

    // Parameter Changes
    parameter_name?: string;
    old_value?: any;
    new_value?: any;

    // Performance Data
    response_time_ms?: number;
    task_duration_ms?: number;
    success?: boolean;

    // Assessment Data
    score?: number;
    max_score?: number;
    answer_data?: Record<string, any>;

    // Survey/Rating Data
    rating?: number; // 1-5 scale
    rating_scale?: string; // "likert", "sus", "nasa_tlx"

    // Error Information
    error_message?: string;
    error_type?: string;

    // Simulation Data
    simulation_config?: Record<string, any>;
    simulation_results?: Record<string, any>;

    // Additional Context
    metadata?: Record<string, any>;
}
