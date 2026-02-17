"""
Tests for the Topology Agent's synthesize task.
Parametrized over evaluation_dataset.yaml.

Usage:
    # Graph assertions only (fast, no extra LLM cost)
    python -m pytest ai_agent/tests/topology_agent/test_topology_agent.py -xvs

    # With LLM-as-Judge (slower, uses Ollama)
    python -m pytest ai_agent/tests/topology_agent/test_topology_agent.py -xvs --with-llm-judge
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pytest
import yaml

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_agent.src.agents.topology_agent.topology_agent import TopologyAgent
from ai_agent.src.agents.topology_agent.structure import (
    SimplifiedTopology,
    SynthesisTopologyOutput,
    SynthesisTopologyRequest,
)
from ai_agent.src.agents.base.enums import AgentTaskType

from ai_agent.tests.topology_agent.scoring import (
    score_structural_validity,
    score_logical_correctness,
    score_requirement_fulfillment,
    score_metadata_completeness,
    judge_topology,
    compute_aggregate_score,
)
from ai_agent.tests.topology_agent.report_generator import ReportGenerator

# ─── Dataset Loading ─────────────────────────────────────────────────────────

DATASET_PATH = Path(__file__).parent / "evaluation_dataset.yaml"


def load_dataset() -> List[dict]:
    with open(DATASET_PATH, "r") as f:
        data = yaml.safe_load(f)
    return data["test_cases"]


TEST_CASES = load_dataset()
TEST_IDS = [tc["id"] for tc in TEST_CASES]


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def topology_agent(agent_llm):
    """Initialize the topology agent with the production LLM."""
    agent = TopologyAgent(llm=agent_llm)
    return agent


@pytest.fixture(scope="session")
def all_results():
    """Shared dict to collect results across all test cases for the final report."""
    return {}


@pytest.fixture(scope="session")
def report_gen(test_config):
    """Report generator instance."""
    reports_dir = Path(__file__).parent / test_config["reports"]["output_dir"]
    return ReportGenerator(reports_dir)


# ─── Generate Topologies (runs once per session) ────────────────────────────



@pytest.fixture(scope="session")
def generated_outputs(topology_agent) -> Dict[str, dict]:
    """
    Run synthesis for all test cases upfront.
    Returns a dict of {test_id: raw_output_dict_or_error}.
    """
    outputs = {}
    output_json = []
    for tc in TEST_CASES:
        test_id = tc["id"]
        try:
            input_data = SynthesisTopologyRequest(
                user_query=tc["prompt"],
                conversation_id=f"test_{test_id}",
            )
            result = asyncio.get_event_loop().run_until_complete(
                topology_agent.synthesize_topology(input_data)
            )
            if result is not None:
                outputs[test_id] = {"success": True, "result": result}
                output_json.append({"test_id": test_id, "result": result.model_dump()})
            else:
                outputs[test_id] = {"success": False, "error": "Agent returned None"}
                output_json.append({"test_id": test_id, "error": "Agent returned None"})
        except Exception as e:
            outputs[test_id] = {"success": False, "error": str(e)}
            output_json.append({"test_id": test_id, "error": str(e)})

    # save the outputs to a file
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump(output_json, f, indent=4)
        print(f"Saved outputs to {f.name}")

    return outputs


def _get_topology(generated_outputs: dict, test_id: str) -> SimplifiedTopology:
    """Extract SimplifiedTopology from generated output, or skip test."""
    output = generated_outputs.get(test_id)
    if not output or not output["success"]:
        pytest.skip(f"Synthesis failed for '{test_id}': {output.get('error', 'unknown')}")
    result: SynthesisTopologyOutput = output["result"]
    if not isinstance(result.generated_topology, SimplifiedTopology):
        pytest.skip(f"Output for '{test_id}' is not SimplifiedTopology (got {type(result.generated_topology).__name__})")
    return result.generated_topology


# ─── Tests ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("test_case", TEST_CASES, ids=TEST_IDS)
class TestTopologySynthesis:

    def test_schema_compliance(self, test_case, generated_outputs):
        """LLM output must parse into SynthesisTopologyOutput."""
        output = generated_outputs.get(test_case["id"])
        assert output is not None, f"No output for test case '{test_case['id']}'"
        assert output["success"], f"Synthesis failed: {output.get('error')}"
        assert isinstance(output["result"], SynthesisTopologyOutput)

    def test_structural_validity(self, test_case, generated_outputs):
        """Generated topology must pass static validation rules."""
        topology = _get_topology(generated_outputs, test_case["id"])
        score, details = score_structural_validity(topology)

        if not details["is_valid"]:
            error_str = "\n".join(f"  - {e}" for e in details["errors"])
            pytest.fail(f"Structural validation failed:\n{error_str}")

    def test_logical_correctness(self, test_case, generated_outputs):
        """Generated topology must satisfy logical path assertions."""
        topology = _get_topology(generated_outputs, test_case["id"])
        assertions = test_case.get("logical_assertions", [])
        if not assertions:
            pytest.skip("No logical assertions defined for this test case")

        score, results = score_logical_correctness(topology, assertions)

        failures = [r for r in results if not r["passed"]]
        if failures:
            failure_str = "\n".join(f"  - [{r['assertion']}]: {r['reason']}" for r in failures)
            pytest.fail(f"Logical correctness: {len(failures)}/{len(assertions)} assertions failed:\n{failure_str}")

    def test_requirement_fulfillment(self, test_case, generated_outputs):
        """Generated topology must have expected node counts and types."""
        topology = _get_topology(generated_outputs, test_case["id"])
        expected = test_case.get("expected", {})
        score, issues = score_requirement_fulfillment(topology, expected)

        if issues:
            issue_str = "\n".join(f"  - {i}" for i in issues)
            pytest.fail(f"Requirement fulfillment ({score:.0%}):\n{issue_str}")

    def test_metadata_completeness(self, test_case, generated_outputs):
        """Metadata fields must be populated."""
        output = generated_outputs.get(test_case["id"])
        if not output or not output["success"]:
            pytest.skip("Synthesis failed")

        result_dict = output["result"].model_dump()
        score, missing = score_metadata_completeness(result_dict)

        if missing:
            pytest.fail(f"Missing metadata fields: {missing}")


# ─── Report Generation (runs after all tests) ───────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def generate_report(request, generated_outputs, test_config, use_llm_judge, judge_llm):
    """Generate the evaluation report after all tests complete."""
    yield  # Let all tests run first

    report_gen = ReportGenerator(
        output_dir=Path(__file__).parent / test_config["reports"]["output_dir"]
    )

    all_scores = {}
    for tc in TEST_CASES:
        test_id = tc["id"]
        output = generated_outputs.get(test_id)

        scores = {}

        if not output or not output["success"]:
            scores = {"schema_compliance": 0.0, "error": output.get("error", "unknown")}
            all_scores[test_id] = scores
            continue

        result: SynthesisTopologyOutput = output["result"]
        scores["schema_compliance"] = 1.0

        if isinstance(result.generated_topology, SimplifiedTopology):
            topo = result.generated_topology
            s_val, s_details = score_structural_validity(topo)
            scores["structural_validity"] = s_val
            scores["structural_errors"] = s_details.get("errors", [])

            s_logic, logic_results = score_logical_correctness(topo, tc.get("logical_assertions", []))
            scores["logical_correctness"] = s_logic
            scores["logical_details"] = logic_results

            s_req, req_issues = score_requirement_fulfillment(topo, tc.get("expected", {}))
            scores["requirement_fulfillment"] = s_req
            scores["requirement_issues"] = req_issues

            result_dict = result.model_dump()
            s_meta, missing = score_metadata_completeness(result_dict)
            scores["metadata_completeness"] = s_meta

            # LLM Judge (optional)
            if use_llm_judge and judge_llm:
                try:
                    print(f"  🔍 Judging '{test_id}'...", end=" ", flush=True)
                    judgement = judge_topology(tc["prompt"], topo, judge_llm)
                    scores["llm_judge"] = judgement.weighted_score
                    scores["llm_judge_details"] = judgement.model_dump()
                    print(f"score={judgement.weighted_score:.2f} ✓")
                except Exception as e:
                    scores["llm_judge"] = 0.0
                    scores["llm_judge_error"] = str(e)
                    print(f"FAILED: {e}")

            scores["aggregate"] = compute_aggregate_score(scores)
        else:
            scores["note"] = f"Output was {type(result.generated_topology).__name__}, not SimplifiedTopology"

        all_scores[test_id] = scores

    report_gen.generate(TEST_CASES, all_scores, use_llm_judge)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
