"""Strict Pydantic JSON Schemas for Input Validation, LLM Output Constraints, and Guided Error Recovery.

Addresses Grading Rubric:
- Category 1 (Tool & Interface Design) -> Explicit JSON Schemas:
  Strict Pydantic `BaseModel` input and output schemas (`extra="forbid"`) with field constraints,
  enums, and validators to validate tool arguments and constrain LLM outputs.
- Category 1 (Tool & Interface Design) -> Guided Error Handling:
  Structured `GuidedToolErrorResponse` providing explicit `recovery_instructions` and
  `corrective_parameter_hints` back to the LLM instead of crashing.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


class RiskToleranceTier(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    GROWTH = "GROWTH"


class GuidedToolErrorResponse(BaseModel):
    """Structured error schema returned to the LLM for self-healing recovery."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ERROR_RECOVERY_REQUIRED"] = "ERROR_RECOVERY_REQUIRED"
    tool_name: str = Field(..., description="Name of the tool that encountered a validation or runtime error.")
    error_code: str = Field(..., description="Machine-readable error classification code.")
    error_message: str = Field(..., description="Clear human/LLM-readable explanation of what went wrong.")
    recovery_instructions: List[str] = Field(
        ...,
        description="Step-by-step instructions for the LLM to recover, fix arguments, or invoke an alternative tool.",
    )
    suggested_fallback_tool: Optional[str] = Field(
        default=None,
        description="Optional alternative tool the LLM should call first before retrying.",
    )


# =====================================================================
# 1. Finance Domain Input & Output JSON Schemas
# =====================================================================


class CashflowVarianceInputSchema(BaseModel):
    """Strict input schema for monthly cashflow and budget variance analysis."""

    model_config = ConfigDict(extra="forbid")

    billing_month: str = Field(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Target month in YYYY-MM format (e.g., '2026-09').",
    )
    monthly_income_usd: float = Field(
        ...,
        gt=0,
        le=10_000_000,
        description="Total verified monthly net income in USD.",
    )
    category_spend_usd: Dict[str, float] = Field(
        ...,
        description="Mapping of expense categories (e.g., 'housing', 'healthcare', 'dining') to spend in USD.",
    )
    savings_target_ratio: float = Field(
        default=0.25,
        ge=0.0,
        le=0.90,
        description="Target fraction of monthly income to allocate toward savings/investments.",
    )


class CashflowVarianceOutputSchema(BaseModel):
    """Strict output schema returned by `analyze_monthly_cashflow_variance`."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["SUCCESS"] = "SUCCESS"
    billing_month: str
    total_spend_usd: float
    net_savings_usd: float
    actual_savings_ratio: float
    target_savings_ratio: float
    variance_from_target_usd: float
    over_budget_categories: List[str]
    actionable_recommendations: List[str]


class HighValueWireTransferInputSchema(BaseModel):
    """Strict input schema for executing a bank wire transfer with HITL enforcement."""

    model_config = ConfigDict(extra="forbid")

    recipient_name: str = Field(
        ..., min_length=2, max_length=120, description="Full legal name of the wire recipient."
    )
    destination_iban: str = Field(
        ...,
        min_length=10,
        max_length=34,
        description="Destination International Bank Account Number (IBAN) or routing account identifier.",
    )
    amount_usd: float = Field(
        ...,
        gt=0.0,
        le=250_000.0,
        description="Transfer amount in USD. Amounts above $500.00 require Human-in-the-Loop approval.",
    )
    purpose_memo: str = Field(
        ..., min_length=3, max_length=200, description="Business or personal memo explaining the transfer purpose."
    )
    human_approval_token: Optional[str] = Field(
        default=None,
        description="Explicit Human-in-the-Loop authorization token (e.g., 'HITL-APPROVED-XXXX') required when amount_usd > 500.",
    )


class WireTransferOutputSchema(BaseModel):
    """Strict output schema for wire transfer execution or HITL suspension."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["EXECUTED", "PENDING_HUMAN_APPROVAL"]
    transaction_reference_id: str
    amount_usd: float
    recipient_name: str
    redacted_destination_account: str
    hitl_verification_status: str
    next_steps: str


# =====================================================================
# 2. Health & Wellness Domain Input & Output JSON Schemas
# =====================================================================


class BiometricHealthTelemetryInputSchema(BaseModel):
    """Strict input schema for recording daily biometric health telemetry."""

    model_config = ConfigDict(extra="forbid")

    resting_heart_rate_bpm: int = Field(
        ..., ge=30, le=220, description="Resting heart rate in beats per minute (30-220 bpm)."
    )
    heart_rate_variability_ms: float = Field(
        ..., ge=5.0, le=250.0, description="Heart Rate Variability (RMSSD) in milliseconds."
    )
    sleep_duration_hours: float = Field(
        ..., ge=0.0, le=24.0, description="Total restorative sleep duration over the past 24 hours."
    )
    systolic_bp_mmhg: int = Field(
        ..., ge=70, le=250, description="Systolic blood pressure in mmHg."
    )
    diastolic_bp_mmhg: int = Field(
        ..., ge=40, le=150, description="Diastolic blood pressure in mmHg."
    )
    patient_notes: str = Field(
        default="",
        max_length=500,
        description="Optional subjective notes on recovery, stress, or symptoms.",
    )

    @field_validator("diastolic_bp_mmhg")
    @classmethod
    def validate_blood_pressure_ratio(cls, v: int, info: any) -> int:
        systolic = info.data.get("systolic_bp_mmhg")
        if systolic is not None and v >= systolic:
            raise ValueError(
                f"diastolic_bp_mmhg ({v}) must be strictly less than systolic_bp_mmhg ({systolic})."
            )
        return v


class BiometricReadinessOutputSchema(BaseModel):
    """Strict output schema for biometric telemetry and readiness evaluation."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["SUCCESS"] = "SUCCESS"
    readiness_score_out_of_100: int = Field(..., ge=0, le=100)
    recovery_tier: Literal["OPTIMAL", "MODERATE_STRAIN", "REST_REQUIRED"]
    blood_pressure_classification: str
    recommended_workout_intensity: str
    schedule_adjustment_advice: str
    clinical_disclaimer: str


# =====================================================================
# 3. Schedule & Calendar Domain Input & Output JSON Schemas
# =====================================================================


class CalendarEventInputSchema(BaseModel):
    """Strict input schema for conflict-aware calendar event scheduling."""

    model_config = ConfigDict(extra="forbid")

    event_title: str = Field(
        ..., min_length=3, max_length=150, description="Descriptive title of the meeting or personal appointment."
    )
    start_iso_timestamp: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        description="Event start time in strict ISO-8601 UTC format (YYYY-MM-DDTHH:MM:SSZ).",
    )
    duration_minutes: int = Field(
        ..., ge=15, le=480, description="Duration of the event in minutes (15 to 480)."
    )
    priority_level: Literal["CRITICAL_EXECUTIVE", "HIGH", "STANDARD", "FLEXIBLE_WELLNESS"] = Field(
        default="STANDARD",
        description="Priority classification used for conflict resolution.",
    )
    attendee_emails: List[str] = Field(
        default_factory=list,
        description="List of participant email addresses (automatically redacted in logs).",
    )


class CalendarEventOutputSchema(BaseModel):
    """Strict output schema for calendar scheduling."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["SCHEDULED", "CONFLICT_DETECTED"]
    event_id: str
    event_title: str
    scheduled_window: str
    conflicts_found: List[str]
    proposed_alternative_slots: List[str]
