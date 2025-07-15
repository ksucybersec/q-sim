export interface ServerSimulationStatus {
    is_running: boolean
}

export interface ControlConfigI {
    enable_ai_feature: boolean;
    enable_realtime_log_summary: boolean;
}

export interface UpsertUserIDResponse {
    user: any;
    is_new_user: boolean;
}