from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import os
from pathlib import Path

from config.control_config import ControlConfig
from config.data_config import RedisConfig
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
        return cls(**config_dict)


loaded_config: AppConfig = None


def get_config(config_path: str = "config/config.yaml") -> AppConfig:
    global loaded_config
    if not loaded_config:
        config_path = os.getenv("CONFIG_PATH", config_path)
        """Load application configuration."""
        loaded_config = AppConfig.from_yaml(config_path)
    return loaded_config
