import json
import logging
import os
from typing import Dict, List, Any, Union
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from ai_agent.src.agents.base.base_agent import BaseAgent
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMDoesNotExists
from config.config import get_config
from langchain_ollama import ChatOllama


class MultiModelChatOpenAI(ChatOpenAI):
    sub_models: Dict[str, Union[ChatOpenAI, BaseChatModel]] = {}

    def add_sub_model(self, name: str, model: Union[ChatOpenAI, BaseChatModel]):
        """Add a sub-model to the chat OpenAI instance."""
        self.sub_models[name] = model
        print(
            f"Added sub-model '{name}' with ID {getattr(model, 'model_name', getattr(model, 'model', 'Unknown Model'))}"
        )

    def use(self, *model_order: str):
        """Use a sub-model by name."""
        for name in model_order:
            if name in self.sub_models:
                return self.sub_models[name]
        raise LLMDoesNotExists(model_order)


class AgentManager:
    """Manages the lifecycle and coordination of AI agents in the system."""

    def __init__(self):
        self.config = get_config()
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.api_client = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the language model client."""
        api_key = os.getenv("OPENAI_API_KEY") or self.config.llm.api_key
        try:
            llm = MultiModelChatOpenAI(
                model_name=self.config.llm.model,
                temperature=self.config.llm.temperature,
                api_key=api_key,
                base_url=self.config.llm.base_url,
            )
            lite_llm = ChatOpenAI(
                model_name=self.config.llm.lite_model or self.config.llm.model,
                temperature=self.config.llm.temperature,
                api_key=api_key,
                base_url=self.config.llm.base_url,
            )
            llm.add_sub_model("lite", lite_llm)
            local_llm = ChatOllama(
                model="llama3.1:8b",
                temperature=0,
                base_url="http://100.119.118.117:11434",
                format="json",
            )
            llm.add_sub_model("local_llm", local_llm)
            # models = llm.root_client.models.list()
            # model_exists = any(model.id == self.config.llm.model for model in models)

            # if not model_exists:
            #     raise ValueError(f"Model '{self.config.llm.model}' not found in the LLM")
            # print([model.id for model in models])

            # llm = ChatOllama(
            #     model=self.config.llm.model,
            #     temperature=self.config.llm.temperature,
            #     api_key=api_key,
            #     base_url=self.config.llm.base_url
            # )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM client: {str(e)}")

        return llm

    def register_agent(self, agent_id: AgentType, agent_class: BaseAgent, **kwargs):
        """Register a new agent in the system."""
        if agent_id in self.agents:
            raise ValueError(f"Agent with ID '{agent_id}' already exists")

        agent_instance = agent_class(llm=self.api_client, **kwargs)
        self.agents[agent_id] = agent_instance
        return agent_instance

    def get_agent(self, agent_id: AgentType):
        """Retrieve an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[AgentType]:
        """List all registered agent IDs."""
        return list(self.agents.keys())

    def get_agents_and_capabilities(self) -> List[str]:
        """Get a list of all agents and their capabilities."""
        capabilities = [
            json.dumps(self.get_agent(agent_id).get_capabilities(), indent=2)
            for agent_id in self.list_agents()
        ]
        return capabilities

    def execute_agent(
        self, agent_id: AgentType, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific agent with the given input data."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"No agent found with ID '{agent_id}'")

        return agent.run(input_data)

    def shutdown_agent(self, agent_id: AgentType) -> bool:
        """Shutdown and unregister an agent."""
        if agent_id in self.agents:
            # Clean up resources if needed
            del self.agents[agent_id]
            return True
        return False
