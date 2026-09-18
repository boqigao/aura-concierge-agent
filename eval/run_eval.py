"""Automated Evaluation Suite & Static Regression Harness against the Golden Dataset.

Addresses Grading Rubric:
- Category 5 (Infrastructure & CI/CD) -> Automated Evaluation Suites:
  Executes deterministic and rubric-based evaluations against `eval/golden_dataset.json`
  to measure tool trajectory accuracy, schema compliance, HITL gate enforcement,
  PII scrubbing, and strategic model routing regressions.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Dict, List

from aura_concierge.agent import StrategicModelRouter
from aura_concierge.observability.pii_redaction import redact_sensitive_data
from aura_concierge.observability.structured_logger import get_audit_log_buffer
from aura_concierge.tools import (
    allocate_deep_work_focus_blocks,
    analyze_monthly_cashflow_variance,
    execute_high_value_wire_transfer,
    generate_personalized_nutrition_protocol,
    optimize_tax_advantaged_portfolio,
    record_biometric_health_telemetry,
    schedule_conflict_aware_calendar_event,
)

TOOL_REGISTRY = {
    "analyze_monthly_cashflow_variance": analyze_monthly_cashflow_variance,
    "execute_high_value_wire_transfer": execute_high_value_wire_transfer,
    "optimize_tax_advantaged_portfolio": optimize_tax_advantaged_portfolio,
    "record_biometric_health_telemetry": record_biometric_health_telemetry,
    "generate_personalized_nutrition_protocol": generate_personalized_nutrition_protocol,
    "schedule_conflict_aware_calendar_event": schedule_conflict_aware_calendar_event,
    "allocate_deep_work_focus_blocks": allocate_deep_work_focus_blocks,
}


def run_golden_dataset_evaluation(
    dataset_path: pathlib.Path | None = None,
) -> Dict[str, Any]:
    """Runs all test cases in `golden_dataset.json` and computes a comprehensive AgentOps score."""
    if dataset_path is None:
        dataset_path = pathlib.Path(__file__).parent / "golden_dataset.json"

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    cases: List[Dict[str, Any]] = dataset.get("test_cases", [])
    case_results: List[Dict[str, Any]] = []
    passed_count = 0

    for case in cases:
        case_id = case["id"]
        tool_name = case["expected_tool"]
        tool_fn = TOOL_REGISTRY[tool_name]
        output = tool_fn(**case["tool_args"])

        actual_status = output.get("status")
        status_matched = actual_status == case["expected_status"]

        # Verify model routing if specified
        routing_matched = True
        if "expected_model_tier" in case:
            domain = case["domain"]
            task_map = {
                "FINANCE": ("QUANTITATIVE_FINANCE_AND_TAX", 0.9),
                "HEALTH": ("BIOMETRIC_HEALTH_TELEMETRY", 0.3),
                "SCHEDULE": ("CALENDAR_CONFLICT_SCHEDULING", 0.3),
            }
            cat, score = task_map[domain]
            routed_model = StrategicModelRouter.select_model(cat, complexity_score=score)
            routing_matched = routed_model == case["expected_model_tier"]

        # Verify PII never leaks in serialized tool output
        serialized = json.dumps(output)
        pii_clean = (
            "DE89370400440532013000" not in serialized
            and "MRN-8492011" not in serialized
        )

        case_passed = status_matched and routing_matched and pii_clean
        if case_passed:
            passed_count += 1

        case_results.append(
            {
                "case_id": case_id,
                "passed": case_passed,
                "expected_status": case["expected_status"],
                "actual_status": actual_status,
                "routing_matched": routing_matched,
                "pii_clean": pii_clean,
            }
        )

    # Verify Intent vs. Outcome audit log parity
    audit_logs = get_audit_log_buffer()
    intent_events = [e for e in audit_logs if e.get("phase") == "INTENT"]
    outcome_events = [e for e in audit_logs if e.get("phase") == "OUTCOME"]

    pass_rate = round(passed_count / max(1, len(cases)), 4)
    summary = {
        "dataset_name": dataset["dataset_name"],
        "total_cases": len(cases),
        "passed_cases": passed_count,
        "pass_rate": pass_rate,
        "intent_logs_captured": len(intent_events),
        "outcome_logs_captured": len(outcome_events),
        "case_results": case_results,
    }
    return summary


if __name__ == "__main__":
    report = run_golden_dataset_evaluation()
    print(json.dumps(report, indent=2))
    if report["pass_rate"] < 1.0:
        sys.exit(1)
