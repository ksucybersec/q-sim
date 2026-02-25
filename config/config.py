from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import os
from pathlib import Path

from config.control_config import ControlConfig
from config.data_config import RedisConfig
from config.dev_config import DevConfig
from config.llm_config import AgentConfig, LLMConfig
from config.simulator_config import SimulationConfig


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class AppConfig(BaseSettings):
    llm: LLMConfig
    logging: LoggingConfig
    redis: RedisConfig
    agents: AgentConfig
    simulator: SimulationConfig
    control_config: ControlConfig
    dev: DevConfig

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    @classmethod
    def from_yaml(cls, file_path: str) -> "AppConfig":
        """Load config from YAML file with environment variable interpolation."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(path, "r") as f:
            yaml_str = f.read()

        # Environment variable substitution
        for key, value in os.environ.items():
            placeholder = f"${{{key}}}"
            if placeholder in yaml_str:
                # print(f"Found placeholder: {placeholder} with value: {value[:2]}XXX${value[-2:]}")
                yaml_str = yaml_str.replace(placeholder, value)

        config_dict = yaml.safe_load(yaml_str)

        config_obj = cls(**config_dict)

        # ------------------------------------------------------------------
        # LLM overrides from simple environment variables
        #
        # This allows users to control the LLM provider/model/base_url/api_key
        # with a small set of shared environment variables that are also used
        # by external tools (e.g. the edu_agent_plugin):
        #
        #   - LLM_PROVIDER or provider
        #   - LLM_MODEL   or model
        #   - LLM_BASE_URL or base_url
        #   - OPENAI_API_KEY
        #
        # These override whatever is set in config.yaml while keeping the
        # existing YAML defaults as a sensible base.
        # ------------------------------------------------------------------
        llm_provider = os.getenv("LLM_PROVIDER") or os.getenv("provider")
        if llm_provider:
            config_obj.llm.provider = llm_provider

        llm_model = os.getenv("LLM_MODEL") or os.getenv("model")
        if llm_model:
            config_obj.llm.model = llm_model
            # If lite_model was left as the default, mirror the main model
            if not config_obj.llm.lite_model:
                config_obj.llm.lite_model = llm_model

        llm_base_url = os.getenv("LLM_BASE_URL") or os.getenv("base_url")
        if llm_base_url:
            config_obj.llm.base_url = llm_base_url

        llm_api_key = os.getenv("OPENAI_API_KEY")
        if llm_api_key:
            # Ensure we keep the expected SecretStr type for api_key
            config_obj.llm.api_key = SecretStr(llm_api_key)

        if not config_obj.control_config.enable_ai_feature:
            config_obj.control_config.enable_realtime_log_summary = False

        if config_obj.dev.enable_mock_responses:
            print("=========== WARNING ===========")
            print("Loaded configuration with mock responses enabled.")

        return config_obj


loaded_config: AppConfig = None


def get_config(config_path: str = "config/config.yaml") -> AppConfig:
    global loaded_config
    if not loaded_config:
        config_path = os.getenv("CONFIG_PATH", config_path)
        """Load application configuration."""
        loaded_config = AppConfig.from_yaml(config_path)
    return loaded_config
