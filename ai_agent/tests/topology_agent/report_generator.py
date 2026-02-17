"""
Generates Markdown evaluation reports for topology agent test runs.
Compares with the most recent previous report if one exists.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ReportGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _find_previous_report(self) -> Optional[Path]:
        """Find the most recent existing report."""
        reports = sorted(self.output_dir.glob("report_*.md"), reverse=True)
        return reports[0] if reports else None

    def _format_score(self, score: float) -> str:
        """Format score with emoji indicator."""
        pct = f"{score:.0%}"
        if score >= 0.9:
            return f"🟢 {pct}"
        elif score >= 0.6:
            return f"🟡 {pct}"
        else:
            return f"🔴 {pct}"

    def generate(self, test_cases: List[dict], all_scores: Dict[str, dict], used_llm_judge: bool):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"report_{timestamp}.md"

        lines = []
        lines.append(f"# Topology Agent Evaluation Report")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**LLM Judge**: {'Enabled' if used_llm_judge else 'Disabled'}\n")

        # ── Aggregate Summary ────────────────────────────────────────────
        lines.append("## Summary\n")
        lines.append("| Test Case | Schema | Structural | Logical | Requirements | Metadata | Aggregate |")
        lines.append("|-----------|--------|------------|---------|-------------|----------|-----------|")

        for tc in test_cases:
            tid = tc["id"]
            s = all_scores.get(tid, {})
            row = f"| {tid} "
            row += f"| {self._format_score(s.get('schema_compliance', 0))} "
            row += f"| {self._format_score(s.get('structural_validity', 0))} "
            row += f"| {self._format_score(s.get('logical_correctness', 0))} "
            row += f"| {self._format_score(s.get('requirement_fulfillment', 0))} "
            row += f"| {self._format_score(s.get('metadata_completeness', 0))} "
            row += f"| **{self._format_score(s.get('aggregate', 0))}** |"
            lines.append(row)

        # Overall aggregate
        aggregates = [s.get("aggregate", 0) for s in all_scores.values() if "aggregate" in s]
        overall = sum(aggregates) / len(aggregates) if aggregates else 0
        lines.append(f"\n**Overall Score: {self._format_score(overall)}**\n")

        # ── Per-Test Details ─────────────────────────────────────────────
        lines.append("---\n## Detailed Results\n")

        for tc in test_cases:
            tid = tc["id"]
            s = all_scores.get(tid, {})
            lines.append(f"### {tid}")
            lines.append(f"**Prompt**: _{tc['prompt']}_\n")

            if "error" in s:
                lines.append(f"> ❌ **Synthesis Failed**: {s['error']}\n")
                continue

            # Structural errors
            if s.get("structural_errors"):
                lines.append("**Structural Issues:**")
                for err in s["structural_errors"]:
                    lines.append(f"- {err}")
                lines.append("")

            # Logical assertion results
            if s.get("logical_details"):
                lines.append("**Logical Assertions:**")
                for detail in s["logical_details"]:
                    icon = "✅" if detail["passed"] else "❌"
                    lines.append(f"- {icon} {detail['assertion']}: {detail['reason']}")
                lines.append("")

            # Requirement issues
            if s.get("requirement_issues"):
                lines.append("**Requirement Gaps:**")
                for issue in s["requirement_issues"]:
                    lines.append(f"- {issue}")
                lines.append("")

            # LLM Judge
            if used_llm_judge and "llm_judge_details" in s:
                jd = s["llm_judge_details"]
                lines.append("**LLM Judge:**")
                lines.append(f"- Intent: {jd.get('intent_fulfillment_score', '?')}/10 — {jd.get('intent_fulfillment_reasoning', '')}")
                lines.append(f"- Logic: {jd.get('connection_logic_score', '?')}/10 — {jd.get('connection_logic_reasoning', '')}")
                lines.append(f"- Design: {jd.get('design_quality_score', '?')}/10 — {jd.get('design_quality_reasoning', '')}")
                if jd.get("critical_issues"):
                    lines.append("- Critical Issues:")
                    for ci in jd["critical_issues"]:
                        lines.append(f"  - {ci}")
                lines.append("")

            lines.append("---\n")

        # ── Comparison with Previous Run ─────────────────────────────────
        prev = self._find_previous_report()
        if prev and prev != report_path:
            lines.append(f"## Comparison")
            lines.append(f"Previous report: `{prev.name}`\n")

        report_content = "\n".join(lines)
        report_path.write_text(report_content)
        print(f"\n{'='*60}")
        print(f"📊 Report saved to: {report_path}")
        print(f"   Overall Score: {self._format_score(overall)}")
        print(f"{'='*60}\n")
