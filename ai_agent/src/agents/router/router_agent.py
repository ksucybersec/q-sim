import logging
import traceback
from typing import Any, Dict

from pydantic import BaseModel
from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.router.examples import ROUTER_AGENT_EXAMPLES
from ai_agent.src.agents.router.prompt import PROMPT_TEMPLATE, ROUTER_SYSTEM_PROMPT, STEP_2_EXTRACTOR_PROMPT
from ai_agent.src.agents.router.structure import RoutingInput, RoutingOutput
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMError

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_structured_chat_agent, AgentExecutor

from data.models.conversation.conversation_ops import get_conversation_history


class RouterAgent(BaseAgent):
    logger = logging.getLogger(__name__)

    def __init__(self, llm=None):
        super().__init__(
            agent_id=AgentType.ORCHESTRATOR,
            description="Routes messages to the appropriate agent based on content",
        )
        self.llm = llm

    def _register_tasks(self) -> Dict[str, AgentTask]:
        return {
            AgentTaskType.ROUTING: AgentTask(
                name="Route Message",
                task_id=AgentTaskType.ROUTING,
                description="Routes messages to the appropriate agent based on content",
                input_schema=RoutingInput,
                output_schema=RoutingOutput,
                examples=ROUTER_AGENT_EXAMPLES,
            ),
            AgentTaskType.REFINE_INPUT: AgentTask(
                name="Refine Task Input",
                task_id= AgentTaskType.REFINE_INPUT,
                description= "Refines the task input based on the message content",
                input_schema=None,
                output_schema=None,
                examples=[]
            )
        }

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def run(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print(list(input_data.keys()))
        validated_input = self.validate_input(task_id, input_data)

        if task_id == AgentTaskType.ROUTING:
            result = await self.route_message(validated_input)
        elif task_id == AgentTaskType.REFINE_INPUT:
            result = await self.refine_task_input(validated_input)
        else:
            raise ValueError(f"Invalid task ID: {task_id}")

        return self.validate_output(task_id, result)
    
    async def route_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route the message using Structured Output (JSON Mode/Instructor) 
        instead of AgentExecutor to prevent tool hallucinations.
        """
        
        user_query_obj = input_data.get("user_query")
        agent_details = input_data.get("agent_details", {})
        conversation_id = user_query_obj.get("conversation_id") if isinstance(user_query_obj, dict) else input_data.get("conversation_id")

        if not user_query_obj or not agent_details:
             raise ValueError(f"User query and agent details are required. {input_data}")

        user_query_text = user_query_obj.get('user_query') if isinstance(user_query_obj, dict) else str(user_query_obj)

        if isinstance(agent_details, list):
            agent_details_str = "\n".join([str(a) for a in agent_details])
        else:
            agent_details_str = str(agent_details)

        last_5_messages = get_conversation_history(conversation_id, limit=5)
        history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in last_5_messages])

        target_llm = self.llm
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", ROUTER_SYSTEM_PROMPT),
            ("human", "Chat History:\n{history}\n\nUser Input Context:\n{input_context}\n\nUser Query Text:\n{query}")
        ])

        input_context = user_query_obj
        input_context.pop('agent_id')
        input_context.pop('task_id')
        input_context = "\n".join([f"{k}: {v}" for k,v in input_context.items()])

        chain = prompt | target_llm.with_structured_output(RoutingOutput)

        try:
            self.logger.info(f"Routing query: {user_query_text[:50]}...")
            
            response: RoutingOutput = await chain.ainvoke({
                # "agent_details": agent_details_str,
                "history": history_str,
                "input_context": input_context,
                "query": user_query_text
            })

            # 7. Return Dict (as expected by your system)
            return response.model_dump()

        except Exception as e:
            traceback.print_exc()
            self.logger.exception(f"Exception during routing execution!")
            # Fail Gracefully: Return a routing failure object instead of crashing
            raise e
            return {
                "agent_id": "orchestrator",
                "task_id": "routing",
                "reason": f"Routing failed internally: {str(e)}",
                "input_data": user_query_obj,
                "suggestion": "Please try rephrasing your request."
            }
        
    async def refine_task_input(self, input_data: Dict[str, Any]):
        user_query_obj = input_data.get("user_query")
        task_id = input_data.get("task_id")
        conversation_id = user_query_obj.get("conversation_id") if isinstance(user_query_obj, dict) else input_data.get("conversation_id")
        task_input_model = user_query_obj.get('task_input_model')

        last_5_messages = get_conversation_history(conversation_id, limit=5)
        history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in last_5_messages])

        input_context = user_query_obj
        input_context.pop('agent_id')
        input_context.pop('task_id')
        input_context = "\n".join([f"{k}: {v}" for k,v in input_context.items()])

        prompt = ChatPromptTemplate.from_messages([
            ("system", STEP_2_EXTRACTOR_PROMPT),
            ("human", "Chat History:\n{history}\n\nUser Input Context:\n{input_context}")
        ])
        chain2 = prompt | self.llm.with_structured_output(task_input_model)
        try:
            schema_instance = await chain2.ainvoke({
                "history": history_str,
                "input_context": input_context,
                "schema": task_input_model,
                'task_id': task_id
            })

            return schema_instance
        except Exception as e:
            self.logger.error(f"Step 2 Extraction failed: {e}")
            extracted_data = user_query_obj # Fallback to raw input