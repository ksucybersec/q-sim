import asyncio
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from src.agents.log_summarization.log_summarization_agent import LogSummarizationAgent
from langchain_openai import ChatOpenAI

# Sample test data
SAMPLE_LOGS = [
    "2023-10-15 08:23:15 ERROR database_service Connection timeout after 30s",
    "2023-10-15 08:24:10 WARN monitoring_agent CPU utilization at 95%",
    "2023-10-15 08:24:30 ERROR topology_designer Failed to load network config",
    "2023-10-15 08:25:15 INFO orchestration_layer Agent system initialized",
    "2023-10-15 08:26:45 WARN congestion_monitor High packet loss detected in node N7",
    "2023-10-15 08:27:30 ERROR database_service Query execution failed: timeout",
]
global_agent = None


@pytest.fixture
def log_agent():
    """Create a log summarization agent for testing."""
    global global_agent
    # Use actual LLM for testing
    if global_agent:
        return global_agent
    config = get_config()
    llm_config = config.llm
    try:
        llm = ChatOpenAI(
            model_name=llm_config.model,
            base_url=llm_config.base_url,
            api_key=llm_config.api_key,
            temperature=0,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize LLM client: {str(e)}")
    agent = LogSummarizationAgent(llm=llm)
    global_agent = agent
    return agent


@pytest.mark.asyncio
async def test_agent_initialization(log_agent):
    """Test agent initialization and task registration."""
    x = log_agent.llm.invoke(
        [
            {
                "role": "user",
                "content": "Mock Message.",
            },
        ]
    )
    assert log_agent.agent_id == "log_summarizer"
    assert "summarize" in log_agent.tasks
    assert "extract_patterns" in log_agent.tasks


@pytest.mark.asyncio
async def test_summarize_task(log_agent):
    """Test the log summarization task."""
    result = await log_agent.run("summarize", {"logs": SAMPLE_LOGS})

    # Verify result structure
    assert "error_count" in result
    assert "warning_count" in result
    assert "key_issues" in result
    assert "component_summary" in result
    assert "summary_text" in result

    # Verify counts
    assert result["error_count"] == 3
    assert result["warning_count"] == 2

    # Verify component summary
    assert "database_service" in result["component_summary"]
    assert "ERROR" in result["component_summary"]["database_service"]
    assert result["component_summary"]["database_service"]["ERROR"] == 2


@pytest.mark.asyncio
async def test_message_processing(log_agent):
    if not log_agent:
        pytest.skip("Log agent not initialized properly.")

    logs = "\n".join(SAMPLE_LOGS)
    """Test direct message processing."""
    message = {"content": f"Please summarize these logs:\n{''.join(logs)}"}

    result = await log_agent.process_message(message)
    print("------------------", result)
    # Verify basic result structure
    assert "summary_text" in result
    assert result["error_count"] == 3
    assert result["warning_count"] == 2


@pytest.mark.asyncio
async def test_empty_logs(log_agent):
    """Test handling of empty logs."""
    result = await log_agent.run("summarize", {"logs": []})

    assert result["error_count"] == 0
    assert result["warning_count"] == 0
    assert len(result["key_issues"]) == 0


@pytest.mark.asyncio
async def test_component_filtering(log_agent):
    """Test filtering logs by component."""
    result = await log_agent.run(
        "summarize", {"logs": SAMPLE_LOGS, "focus_components": ["database_service"]}
    )

    assert result["error_count"] == 2
    assert result["warning_count"] == 0
    assert len(result["component_summary"]) == 1
    assert "database_service" in result["component_summary"]


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(pytest.main(["-xvs", __file__]))
