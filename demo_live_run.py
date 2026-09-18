"""Live End-to-End ADK Runner Script for Aura Executive Personal Concierge Agent.

Usage (after authenticating with `gcloud auth application-default login`):
    GOOGLE_GENAI_USE_VERTEXAI=TRUE \
    GOOGLE_CLOUD_PROJECT=<your-gcp-project-id> \
    GOOGLE_CLOUD_LOCATION=us-central1 \
    .venv/bin/python demo_live_run.py
"""

from __future__ import annotations

import asyncio
import os
from google.adk.runners import InMemoryRunner
from google.genai import types

from aura_concierge.agent import root_agent


async def run_live_demo() -> None:
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "aura-concierge-prod")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

    runner = InMemoryRunner(agent=root_agent, app_name="aura_concierge")
    session = await runner.session_service.create_session(
        app_name="aura_concierge",
        user_id="executive_primary_user",
    )

    prompts = [
        (
            "Hi Aura! First, please log my morning biometrics: RHR 54 bpm, HRV 78 ms, "
            "7.8 hours sleep, BP 118/76 mmHg. Also analyze my September 2026 cashflow "
            "($12,000 income, housing $3,800, healthcare $650, dining $950, travel $600)."
        ),
        (
            "Now please wire $4,500 USD to Stanford Preventive Health Clinic "
            "(IBAN DE89370400440532013000) for my annual executive medical package."
        ),
    ]

    for idx, prompt in enumerate(prompts, start=1):
        print(f"\n{'=' * 80}\n[TURN {idx} USER PROMPT]: {prompt}\n{'=' * 80}")
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=prompt)]
        )
        async for event in runner.run_async(
            user_id="executive_primary_user",
            session_id=session.id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        print(
                            f"\n[ADK TOOL CALL] -> {part.function_call.name}({part.function_call.args})"
                        )
                    if part.function_response:
                        print(
                            f"\n[ADK TOOL RESPONSE] <- {part.function_response.name}: {part.function_response.response}"
                        )
                    if part.text:
                        print(f"\n[AURA ({event.author})]:\n{part.text}")


if __name__ == "__main__":
    asyncio.run(run_live_demo())
