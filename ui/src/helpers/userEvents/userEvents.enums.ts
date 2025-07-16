export enum UserEventType {
  // Authentication
  LOGIN = "login",
  LOGOUT = "logout",
  
  // Navigation
  PAGE_VIEW = "page_view",
  MODULE_ENTER = "module_enter",
  MODULE_EXIT = "module_exit",
  
  // Interactions
  CLICK = "click",
  PARAMETER_CHANGE = "parameter_change",
  SIMULATION_START = "simulation_start",
  SIMULATION_COMPLETE = "simulation_complete",
  SIMULATION_RESET = "simulation_reset",
  
  // Learning Actions
  HELP_ACCESS = "help_access",
  TUTORIAL_START = "tutorial_start",
  TUTORIAL_COMPLETE = "tutorial_complete",
  QUIZ_ATTEMPT = "quiz_attempt",
  QUIZ_SUBMIT = "quiz_submit",
  
  // Errors & Recovery
  ERROR_OCCURRED = "error_occurred",
  UNDO_ACTION = "undo_action",
  REDO_ACTION = "redo_action",
  TASK_ABANDON = "task_abandon",
  
  // Assessment
  PRE_TEST = "pre_test",
  POST_TEST = "post_test",
  SELF_ASSESSMENT = "self_assessment",
  SURVEY_RESPONSE = "survey_response",
  
  // Simulator Specific
  COMPONENT_DRAG = "component_drag",
  COMPONENT_DROP = "component_drop",
  COMPONENT_CONNECT = "component_connect",
  COMPONENT_DISCONNECT = "component_disconnect",
  COMPONENT_SELECT = "component_select",
  COMPONENT_CONFIGURE = "component_configure",
  
  // Lab Activities
  LAB_START = "lab_start",
  LAB_COMPLETE = "lab_complete",
  LAB_CANCEL = "lab_cancel",
  LAB_STEP_COMPLETE = "lab_step_complete",
  INSTRUCTIONS_VIEW = "instructions_view",
  TIPS_VIEW = "tips_view",
  REQUIREMENTS_VIEW = "requirements_view",
  
  // AI Agent
  AI_AGENT_OPEN = "ai_agent_open",
  AI_AGENT_CLOSE = "ai_agent_close",
  AI_AGENT_MESSAGE = "ai_agent_message",
  AI_AGENT_RESPONSE = "ai_agent_response",
  
  // Timeline/Logs
  TIMELINE_FILTER = "timeline_filter",
  TIMELINE_SEARCH = "timeline_search",
  LOG_LEVEL_CHANGE = "log_level_change"
}

export enum ComponentType {
  CLASSICAL_HOST = "classical_host",
  CLASSICAL_ROUTER = "classical_router",
  QUANTUM_HOST = "quantum_host",
  QUANTUM_ADAPTER = "quantum_adapter",
  QUANTUM_REPEATER = "quantum_repeater"
}

export enum LabType {
  BASIC_NETWORK_CONSTRUCTION = "basic_network_construction",
  QUANTUM_KEY_DISTRIBUTION = "quantum_key_distribution",
  QUANTUM_REPEATER_ANALYSIS = "quantum_repeater_analysis"
}

export enum NetworkType {
  QUANTUM = "quantum",
  CLASSICAL = "classical",
  HYBRID = "hybrid"
}