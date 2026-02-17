"""
Scoring utilities for topology agent evaluation.
Provides graph-based logical assertions and LLM-as-Judge scoring.
"""
import json
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

from ai_agent.src.agents.topology_agent.structure import SimplifiedTopology
from ai_agent.src.agents.topology_agent.validator import validate_static_topology


# =============================================================================
# Graph Utilities
# =============================================================================

def _build_adjacency(topology: SimplifiedTopology) -> Dict[str, List[str]]:
    """Build adjacency list from topology connections."""
    adj = {n.name: [] for n in topology.nodes}
    for conn in topology.connections:
        if len(conn) == 2:
            u, v = conn[0], conn[1]
            if u in adj:
                adj[u].append(v)
            if v in adj:
                adj[v].append(u)
    return adj


def _node_type_map(topology: SimplifiedTopology) -> Dict[str, str]:
    """Map node name → node type."""
    return {n.name: n.type for n in topology.nodes}


def _find_nodes(topology: SimplifiedTopology,
                node_type: Optional[str] = None,
                name_contains: Optional[str] = None) -> List[str]:
    """Find nodes matching optional type and name filters."""
    results = []
    for n in topology.nodes:
        if node_type and n.type != node_type:
            continue
        if name_contains and name_contains.lower() not in n.name.lower():
            continue
        results.append(n.name)
    return results


def _bfs_path(adj: Dict[str, List[str]], start: str, end: str) -> Optional[List[str]]:
    """BFS to find a path between two nodes. Returns the path or None."""
    if start == end:
        return [start]
    visited = {start}
    queue = deque([(start, [start])])
    while queue:
        current, path = queue.popleft()
        for neighbor in adj.get(current, []):
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None


# =============================================================================
# Assertion Checkers
# =============================================================================

def check_end_to_end_path(topology: SimplifiedTopology, assertion: dict) -> Tuple[bool, str]:
    """Check that a path exists between nodes matching the from/to filters."""
    adj = _build_adjacency(topology)
    from_nodes = _find_nodes(topology, assertion.get("from_type"), assertion.get("from_name_contains"))
    to_nodes = _find_nodes(topology, assertion.get("to_type"), assertion.get("to_name_contains"))

    if not from_nodes:
        return False, f"No source nodes found matching filters (type={assertion.get('from_type')}, name contains={assertion.get('from_name_contains')})"
    if not to_nodes:
        return False, f"No target nodes found matching filters (type={assertion.get('to_type')}, name contains={assertion.get('to_name_contains')})"

    # Check that at least one from_node can reach at least one to_node
    for fn in from_nodes:
        for tn in to_nodes:
            if fn == tn:
                continue
            path = _bfs_path(adj, fn, tn)
            if path:
                return True, f"Path found: {' → '.join(path)}"

    return False, f"No path exists between {from_nodes} and {to_nodes}"


def check_path_traverses_type(topology: SimplifiedTopology, assertion: dict) -> Tuple[bool, str]:
    """Check that the path between two nodes traverses specific node types."""
    adj = _build_adjacency(topology)
    type_map = _node_type_map(topology)
    must_traverse = set(assertion.get("must_traverse", []))

    from_nodes = _find_nodes(topology, assertion.get("from_type"), assertion.get("from_name_contains"))
    to_nodes = _find_nodes(topology, assertion.get("to_type"), assertion.get("to_name_contains"))

    if not from_nodes or not to_nodes:
        return False, "Source or target nodes not found"

    for fn in from_nodes:
        for tn in to_nodes:
            if fn == tn:
                continue
            path = _bfs_path(adj, fn, tn)
            if path:
                traversed_types = {type_map[n] for n in path if n in type_map}
                missing = must_traverse - traversed_types
                if not missing:
                    return True, f"Path {' → '.join(path)} traverses required types: {must_traverse}"
                else:
                    return False, f"Path {' → '.join(path)} missing types: {missing}"

    return False, f"No path exists between {from_nodes} and {to_nodes}"


def check_direct_neighbor(topology: SimplifiedTopology, assertion: dict) -> Tuple[bool, str]:
    """Check that all nodes of a type are directly connected to a specific neighbor type."""
    adj = _build_adjacency(topology)
    type_map = _node_type_map(topology)
    target_type = assertion.get("node_type")
    expected_neighbor = assertion.get("neighbor_type")
    name_filter = assertion.get("node_name_contains")

    nodes = _find_nodes(topology, target_type, name_filter)
    if not nodes:
        return False, f"No nodes found matching type={target_type}"

    failures = []
    for node in nodes:
        neighbor_types = [type_map[n] for n in adj.get(node, []) if n in type_map]
        if expected_neighbor not in neighbor_types:
            failures.append(f"'{node}' has neighbors {adj.get(node, [])} (types: {neighbor_types}), missing {expected_neighbor}")

    if failures:
        return False, "; ".join(failures)
    return True, f"All {target_type} nodes connect to {expected_neighbor}"


# Dispatcher
ASSERTION_CHECKERS = {
    "end_to_end_path_exists": check_end_to_end_path,
    "path_traverses_type": check_path_traverses_type,
    "direct_neighbor_type": check_direct_neighbor,
}


# =============================================================================
# Scoring Functions
# =============================================================================

def score_structural_validity(topology: SimplifiedTopology) -> Tuple[float, dict]:
    """Run the existing static validator. Returns (score, details)."""
    result = validate_static_topology(topology)
    score = 1.0 if result["is_valid"] else 0.0
    return score, result


def score_logical_correctness(topology: SimplifiedTopology, assertions: List[dict]) -> Tuple[float, List[dict]]:
    """Run all logical assertions. Returns (score, per-assertion results)."""
    if not assertions:
        return 1.0, []

    results = []
    passed = 0
    for assertion in assertions:
        checker = ASSERTION_CHECKERS.get(assertion["type"])
        if not checker:
            results.append({"assertion": assertion, "passed": False, "reason": f"Unknown assertion type: {assertion['type']}"})
            continue

        ok, reason = checker(topology, assertion)
        results.append({
            "assertion": assertion.get("description", assertion["type"]),
            "passed": ok,
            "reason": reason,
        })
        if ok:
            passed += 1

    score = passed / len(assertions) if assertions else 1.0
    return score, results


def score_requirement_fulfillment(topology: SimplifiedTopology, expected: dict) -> Tuple[float, List[str]]:
    """Check if the topology has the expected node counts and types."""
    issues = []
    checks_total = 0
    checks_passed = 0

    type_map = _node_type_map(topology)
    type_counts = {}
    for t in type_map.values():
        type_counts[t] = type_counts.get(t, 0) + 1

    # Exact node type counts
    for node_type, expected_count in expected.get("node_types", {}).items():
        checks_total += 1
        actual = type_counts.get(node_type, 0)
        if actual == expected_count:
            checks_passed += 1
        else:
            issues.append(f"{node_type}: expected {expected_count}, got {actual}")

    # Minimum node type counts
    for node_type, min_count in expected.get("min_node_types", {}).items():
        checks_total += 1
        actual = type_counts.get(node_type, 0)
        if actual >= min_count:
            checks_passed += 1
        else:
            issues.append(f"{node_type}: expected >= {min_count}, got {actual}")

    # Network count
    if "min_networks" in expected:
        checks_total += 1
        actual = len(topology.networks)
        if actual >= expected["min_networks"]:
            checks_passed += 1
        else:
            issues.append(f"Networks: expected >= {expected['min_networks']}, got {actual}")

    # Zone count
    if "min_zones" in expected:
        checks_total += 1
        actual = len(topology.zones)
        if actual >= expected["min_zones"]:
            checks_passed += 1
        else:
            issues.append(f"Zones: expected >= {expected['min_zones']}, got {actual}")

    score = checks_passed / checks_total if checks_total > 0 else 1.0
    return score, issues


def score_metadata_completeness(result: dict) -> Tuple[float, List[str]]:
    """Check that metadata fields are populated."""
    fields = ["overall_feedback", "cost", "thought_process", "input_query"]
    missing = []
    for field in fields:
        val = result.get(field)
        if val is None or val == "" or val == []:
            missing.append(field)

    score = (len(fields) - len(missing)) / len(fields)
    return score, missing


# =============================================================================
# LLM-as-Judge
# =============================================================================

class TopologyJudgement(BaseModel):
    """Structured output from the LLM judge."""
    intent_fulfillment_score: int = Field(ge=0, le=10, description="0-10: Does the topology fulfill the user's intent?")
    intent_fulfillment_reasoning: str = Field(description="Explain the intent fulfillment score")
    connection_logic_score: int = Field(ge=0, le=10, description="0-10: Are the connections logically correct?")
    connection_logic_reasoning: str = Field(description="Explain the connection logic score")
    design_quality_score: int = Field(ge=0, le=10, description="0-10: Is the design clean and well-organized?")
    design_quality_reasoning: str = Field(description="Explain the design quality score")
    critical_issues: List[str] = Field(default_factory=list, description="List of critical issues found")

    @property
    def weighted_score(self) -> float:
        return (
            self.intent_fulfillment_score * 0.4
            + self.connection_logic_score * 0.4
            + self.design_quality_score * 0.2
        ) / 10.0


JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for quantum network topology designs.
You receive a user's original request and the AI-generated topology JSON.
Score the topology on these criteria:

## Scoring Rubric (0-10 each):

### Intent Fulfillment (weight: 40%)
- 0-3: Topology fundamentally misunderstands the request
- 4-6: Partially addresses the request, missing key elements
- 7-9: Fully addresses the request with minor gaps
- 10: Perfectly matches user intent

### Connection Logic (weight: 40%)
- 0-3: Connections are nonsensical or broken
- 4-6: Some connections make sense, but critical paths are missing or wrong
- 7-9: All connections are logical, communication paths work
- 10: Optimal wiring

### Design Quality (weight: 20%)
- 0-3: Poor naming, unnecessary complexity
- 4-6: Functional but could be improved
- 7-9: Clean, well-organized design
- 10: Elegant, best practices

"""
# {format_instructions}

JUDGE_HUMAN_PROMPT = """## Original User Request:
{user_prompt}

## Generated Topology (JSON):
{topology_json}

Evaluate this topology against the user's request. Respond ONLY with the JSON object."""


def judge_topology(prompt: str, topology: SimplifiedTopology, llm) -> TopologyJudgement:
    """Run LLM-as-Judge evaluation on a generated topology."""
    # parser = PydanticOutputParser(pydantic_object=TopologyJudgement)

    # messages = [
    #     SystemMessage(content=JUDGE_SYSTEM_PROMPT.format(
    #         format_instructions=parser.get_format_instructions()
    #     )),
    #     HumanMessage(content=JUDGE_HUMAN_PROMPT.format(
    #         user_prompt=prompt,
    #         topology_json=topology.model_dump_json(indent=2),
    #     )),
    # ]

    # print("\n\n\n")
    # print(messages)
    # response = llm.invoke(messages)
    # print("\n\n\n")
    # print(response)
    # return parser.parse(response.content)

    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": JUDGE_HUMAN_PROMPT.format(
            user_prompt=prompt,
            topology_json=topology.model_dump_json(indent=2),
        )},
    ]

    response = llm.chat(
        model="maximgattobianco/prometheus-14b:latest",
        messages=messages,
        options={"temperature": 0},
        format=TopologyJudgement.model_json_schema(),
    )

    return TopologyJudgement.model_validate_json(response.message.content)


# =============================================================================
# Aggregate Score
# =============================================================================

def compute_aggregate_score(scores: Dict[str, float],
                            weights: Optional[Dict[str, float]] = None) -> float:
    """Weighted average of all dimension scores."""
    if weights is None:
        weights = {
            "logical_correctness": 0.35,
            "structural_validity": 0.25,
            "requirement_fulfillment": 0.20,
            "metadata_completeness": 0.05,
            "llm_judge": 0.15,
        }

    total_weight = 0.0
    weighted_sum = 0.0
    for key, weight in weights.items():
        if key in scores:
            weighted_sum += scores[key] * weight
            total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0
