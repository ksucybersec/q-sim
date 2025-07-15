import traceback
from typing import Dict, Any
import logging

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.router.structure import RoutingOutput
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.exceptions.llm_exception import LLMError
from config.config import get_config
from .agent_manager import AgentManager

class Coordinator:
    """Central coordinator for the AI agent system."""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Coordinator, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.config = get_config()
            self.agent_manager = AgentManager()
            self.active_workflows = {}
            self.logger = logging.getLogger("coordinator")
        
    async def initialize_system(self):
        if not getattr(self, "initialized", False):
            """Initialize all required agents and resources."""
            self.logger.info("Initializing agent system")
            print("Initializing  agents")
            # Register core agents
            self._register_core_agents()
            self.initialized = True
        else:
            print("System already initialized")
            self.logger.info("System already initialized")
            
        
    def _register_core_agents(self):
        """Register the core agents required by the system."""
        from ..agents.log_summarization.log_summarization_agent import LogSummarizationAgent

        self.agent_manager.register_agent(AgentType.LOG_SUMMARIZER, LogSummarizationAgent)

        from ..agents.topology_agent.topology_agent import TopologyAgent
        self.agent_manager.register_agent(AgentType.TOPOLOGY_DESIGNER, TopologyAgent)

        from ..agents.router.router_agent import RouterAgent
        self.agent_manager.register_agent(AgentType.ORCHESTRATOR, RouterAgent)

        from ..agents.lab_assistant.lab_assistant_agent import LabAssistantAgent
        self.agent_manager.register_agent(AgentType.LAB_ASSISTANT_AGENT, LabAssistantAgent)
        
    async def execute_workflow(self, workflow_id: WorkflowType, workflow_data: Dict[str, Any]):
        """Execute a multi-agent workflow."""
        self.active_workflows[workflow_id] = {"status": "running", "data": {}}
        
        try:
            if workflow_id == WorkflowType.LOG_SUMMARIZATION:
                # Example of a specific workflow
                agent_id = AgentType.LOG_SUMMARIZER
                task_data = workflow_data.get("task_data")
                
                self.logger.info(f"Executing workflow {workflow_id} with agent {agent_id}")
                
                # Execute the agent task
                result = await self._run_agent_task(agent_id, task_data)
                
                # Update workflow status
                self.active_workflows[workflow_id]["status"] = "completed"
                self.active_workflows[workflow_id]["result"] = result

                return result
            
        
            elif workflow_id == WorkflowType.TOPOLOGY_WORKFLOW:
                agent_id = AgentType.TOPOLOGY_DESIGNER
                task_data = workflow_data.get("task_data")
                
                self.logger.info(f"Executing workflow {workflow_id} with agent {agent_id}")
                
                # Execute the agent task
                result = await self._run_agent_task(agent_id, task_data)
                
                # Update workflow status
                self.active_workflows[workflow_id]["status"] = "completed"
                self.active_workflows[workflow_id]["result"] = result

                return result

            elif workflow_id == WorkflowType.ROUTING:
                routing_output = await self._run_agent_task(AgentType.ORCHESTRATOR, {
                    'task_id': AgentTaskType.ROUTING,
                    'input_data': {
                        'conversation_id': workflow_data.get('conversation_id'),
                        'user_query': workflow_data,
                        'agent_details': self.agent_manager.get_agents_and_capabilities()
                    }
                })
                routing_output = RoutingOutput(**routing_output)
                if routing_output.agent_id:
                    agent = self.agent_manager.get_agent(routing_output.agent_id)
                    
                    if agent:
                        routing_output.agent_response = await self._run_agent_task(routing_output.agent_id, {
                            'task_id': routing_output.task_id,
                            'input_data': routing_output.input_data
                        })
                    else:
                        self.logger.info(f"Routing output: {routing_output}")
                        raise LLMError(f"Routing failed: {routing_output}")
                return routing_output
            
            elif workflow_id == WorkflowType.LAB_ASSISTANT_WORKFLOW.value:
                agent_id = AgentType.LAB_ASSISTANT_AGENT
                task_data = workflow_data.get("task_data")
                
                self.logger.info(f"Executing workflow {workflow_id} with agent {agent_id}")
                
                # Execute the agent task
                result = await self._run_agent_task(agent_id, task_data)
                
                # Update workflow status
                self.active_workflows[workflow_id]["status"] = "completed"
                self.active_workflows[workflow_id]["result"] = result

                return result

        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {str(e)}", traceback.format_exc())
            self.active_workflows[workflow_id]["status"] = "failed"
            self.active_workflows[workflow_id]["error"] = str(e)
            raise e
            
    async def _run_agent_task(self, agent_id: str, task_data: Dict[str, Any]):
        """Execute a task with a specific agent."""
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found. Available agents {self.agent_manager.list_agents()}")
            
        # Execute agent task, TODO: Check this
        # result = await asyncio.to_thread(agent.run, **task_data)
        result = await agent.run(**task_data)
        return result
        
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        if workflow_id not in self.active_workflows:
            return {"status": "not_found"}
        return self.active_workflows[workflow_id]