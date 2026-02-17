"""
Shared test fixtures for all agent tests.
Provides LLM clients (agent + judge) and common pytest hooks.
"""
import os
import sys
import pytest
import yaml
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import ollama

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.config import get_config


# ─── CLI Options ─────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption(
        "--with-llm-judge",
        action="store_true",
        default=False,
        help="Enable LLM-as-Judge evaluation (uses Ollama, slower).",
    )


# ─── Test Config ─────────────────────────────────────────────────────────────

def _load_test_config() -> dict:
    config_path = Path(__file__).parent / "test_config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def test_config() -> dict:
    return _load_test_config()


# ─── Agent LLM (from main app config) ───────────────────────────────────────

@pytest.fixture(scope="session")
def agent_llm():
    """The same LLM the agent uses in production."""
    config = get_config()
    llm_config = config.llm
    return ChatOpenAI(
        model_name=llm_config.model,
        base_url=llm_config.base_url,
        api_key=llm_config.api_key,
        temperature=0,
    )


# ─── Judge LLM (from test config) ───────────────────────────────────────────

@pytest.fixture(scope="session")
def judge_llm(request, test_config):
    """
    Prometheus judge LLM via Ollama.
    Only initialized when --with-llm-judge is passed.
    """
    if not request.config.getoption("--with-llm-judge"):
        return None

    judge_cfg = test_config["judge_llm"]
    # return ChatOllama(
    #     model=judge_cfg["model"],
    #     base_url=judge_cfg["base_url"],
    #     temperature=judge_cfg["temperature"],
    #     timeout=judge_cfg.get("timeout", 120),
    # )
    return ollama.Client(
        host=judge_cfg["base_url"],
    )


@pytest.fixture(scope="session")
def use_llm_judge(request) -> bool:
    return request.config.getoption("--with-llm-judge")
