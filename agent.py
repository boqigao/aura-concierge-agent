"""Root ADK Entrypoint for Aura Executive Personal Concierge Agent.

Exposes `root_agent` at the repository root so both `adk run .`, `agents-cli run`,
and automated repository evaluators can discover the complete multi-agent hierarchy,
tools, guardrails, memory systems, and observability hooks immediately.
"""

from aura_concierge.agent import (
    AURA_EXECUTIVE_CONSTITUTION_PROMPT,
    StrategicModelRouter,
    executive_concierge_coordinator,
    finance_wealth_specialist_agent,
    health_wellness_telemetry_agent,
    morning_executive_briefing_pipeline,
    parallel_domain_telemetry_gatherer,
    retrieve_cross_session_concierge_memory,
    root_agent,
    schedule_calendar_orchestrator_agent,
)

__all__ = [
    "AURA_EXECUTIVE_CONSTITUTION_PROMPT",
    "StrategicModelRouter",
    "executive_concierge_coordinator",
    "finance_wealth_specialist_agent",
    "health_wellness_telemetry_agent",
    "morning_executive_briefing_pipeline",
    "parallel_domain_telemetry_gatherer",
    "retrieve_cross_session_concierge_memory",
    "root_agent",
    "schedule_calendar_orchestrator_agent",
]
