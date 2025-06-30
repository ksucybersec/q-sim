from typing import Optional
from pydantic import BaseModel, Field, SecretStr


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4"
    lite_model: Optional[str] = None
    api_key: SecretStr
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 60
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    max_tokens: Optional[int] = 1000
    retry_attempts: int = 3

    # LangChain Config
    langchain_api_key: Optional[SecretStr] = None
    langchain_project_name: str = "simulator_agent_dev"
    langsmith_endpoint: Optional[str] = "https://api.smith.langchain.com"
    langchain_tracing: bool = False

class AgentValidationConfig(BaseModel):
    enabled: bool = True
    regenerate_on_invalid: bool = True

class AgentConfig(BaseModel):
    agent_validation: AgentValidationConfig