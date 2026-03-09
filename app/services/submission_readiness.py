"""Submission Readiness Service — deterministic scoring of submission completeness.

Evaluates whether a commercial insurance submission is ready for market by
checking against industry-specific templates. Produces scores, identifies
gaps, and generates practical next-step guidance for producers.

This service does NOT evaluate carrier appetite, quote likelihood, or
underwriter fit. It focuses solely on submission quality and completeness.
"""

import logging
from typing import Any, Optional

from app.knowledge.submission_requirements import (
    get_submission_template,
    IndustrySubmissionTemplate,
    SubmissionRequirement,
)
from app.services.learning_store import get_office_context

logger = logging.getLogger(__name__)

# ============================================================
# SCORING CONSTANTS
# ============================================================

_IMPORTANCE_PENALTY = {
    "critical": 15,
    "high": 10,
    "medium": 5,
    "low": 2,
}

_READINESS_LEVELS = [
    (80, "strong"),
    (60, "good"),
    (40, "fair"),
    (0, "poor"),
]

# Fields where a short value indicates thin/weak data
_MIN_LENGTH_FIELDS = {
    "operations_description": 20,
    "driver_information": 10,
    "subcontractor_usage": 5,
    "cargo_types": 5,
}

# Values that indicate unknowns or missing info
_WEAK_MARKERS = {"unknown", "n/a", "na", "tbd", "none", "not sure", "?", ""}

# Boolean fields where False is a weakness for specific industries
_FALSE_IS_WEAK = {
    "safety_program",
    "fall_protection_program",
}


# ============================================================
# HELPERS
# ============================================================


def normalize_submission_input(submission_data: dict) -> dict:
    """Normalize submission keys to lowercase with underscores."""
    normalized = {}
    for key, value in submission_data.items():
        clean_key = key.lower().strip().replace("-", "_").replace(" ", "_")
        normalized[clean_key] = value
    return normalized


def is_weak_field(field_name: str, value: Any) -> bool:
    """Check if a field value is present but thin, empty, or obviously weak."""
    if value is None:
        return True

    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in _WEAK_MARKERS:
            return True
        if field_name in _MIN_LENGTH_FIELDS:
            if len(stripped) < _MIN_LENGTH_FIELDS[field_name]:
                return True
        return False

    if isinstance(value, bool):
        if field_name in _FALSE_IS_WEAK and value is False:
            return True
        return False

    if isinstance(value, (int, float)):
        if value == 0 and field_name not in {"years_in_business"}:
            return True
        return False

    return False


def _get_readiness_level(score: int) -> str:
    """Map numeric score to readiness level."""
    for threshold, level in _READINESS_LEVELS:
        if score >= threshold:
            return level
    return "poor"


def _build_strength(req: SubmissionRequirement, value: Any) -> Optional[str]:
    """Build a strength description for a well-supplied field."""
    label = req.label
    if isinstance(value, bool) and value:
        return f"{label} documented"
    if isinstance(value, str) and value.strip().lower() in {"provided", "yes", "true"}:
        return f"{label} provided"
    if isinstance(value, (int, float)) and value > 0:
        return f"{label} disclosed"
    if isinstance(value, str) and len(value.strip()) >= 5:
        return f"{label} provided"
    return None


def build_readiness_explanation(
    score: int,
    level: str,
    missing_critical: list[str],
    missing_recommended: list[str],
    weak_fields: list[str],
    industry: str,
) -> str:
    """Build a deterministic human-readable explanation of the readiness score."""
    parts = [f"This {industry} submission scores {score}/100 ({level})."]

    if missing_critical:
        count = len(missing_critical)
        top = ", ".join(missing_critical[:3])
        if count == 1:
            parts.append(f"Critical gap: {top} is missing.")
        elif count <= 3:
            parts.append(f"{count} critical items missing: {top}.")
        else:
            parts.append(f"{count} critical items missing including {top}.")

    if weak_fields:
        count = len(weak_fields)
        top = ", ".join(weak_fields[:3])
        if count == 1:
            parts.append(f"{top} needs strengthening.")
        else:
            parts.append(f"{count} fields need strengthening including {top}.")

    if missing_recommended and not missing_critical:
        count = len(missing_recommended)
        parts.append(f"{count} recommended item{'s' if count > 1 else ''} could improve marketability.")

    if not missing_critical and not weak_fields and not missing_recommended:
        parts.append("All key information is present and well-documented.")

    return " ".join(parts)


def _build_next_steps(
    missing_critical: list[str],
    missing_high: list[str],
    weak_fields: list[str],
    missing_recommended: list[str],
) -> list[str]:
    """Build prioritized list of next steps for the producer."""
    steps = []

    for field_label in missing_critical:
        steps.append(f"Obtain {field_label} — this is critical for submission")

    for field_label in missing_high:
        steps.append(f"Provide {field_label} to strengthen the submission")

    for field_label in weak_fields:
        steps.append(f"Clarify or expand {field_label} — current detail is thin")

    for field_label in missing_recommended[:3]:
        steps.append(f"Consider adding {field_label} for better market response")

    return steps


# ============================================================
# MAIN EVALUATION
# ============================================================


def evaluate_submission_readiness(
    industry: str,
    submission_data: dict,
    jurisdiction: Optional[str] = None,
    office_id: Optional[str] = None,
) -> dict:
    """Evaluate submission readiness against industry-specific template.

    Returns a structured readiness report with score, gaps, strengths,
    and next steps. Does NOT evaluate carrier appetite or placement fit.
    """
    template = get_submission_template(industry)
    if template is None:
        return {
            "industry": industry,
            "jurisdiction": jurisdiction or "unknown",
            "readiness_score": 0,
            "readiness_level": "poor",
            "missing_critical_fields": [],
            "missing_recommended_fields": [],
            "weak_fields": [],
            "strengths": [],
            "next_steps": ["No submission template available for this industry"],
            "office_learnings": [],
            "explanation": f"No submission template found for '{industry}'. Cannot evaluate readiness.",
        }

    data = normalize_submission_input(submission_data)
    effective_jurisdiction = jurisdiction or template.jurisdiction

    score = 100
    missing_critical_labels = []
    missing_high_labels = []
    missing_recommended_labels = []
    weak_field_labels = []
    strengths = []

    # Evaluate required fields
    for req in template.required_fields:
        field_key = req.field_name.lower().strip()
        value = data.get(field_key)

        if value is None:
            penalty = _IMPORTANCE_PENALTY.get(req.importance, 5)
            score -= penalty
            if req.importance == "critical":
                missing_critical_labels.append(req.label)
            elif req.importance == "high":
                missing_high_labels.append(req.label)
        elif is_weak_field(field_key, value):
            score -= max(1, _IMPORTANCE_PENALTY.get(req.importance, 5) // 2)
            weak_field_labels.append(req.label)
        else:
            strength = _build_strength(req, value)
            if strength:
                strengths.append(strength)

    # Evaluate recommended fields
    for req in template.recommended_fields:
        field_key = req.field_name.lower().strip()
        value = data.get(field_key)

        if value is None:
            penalty = _IMPORTANCE_PENALTY.get(req.importance, 2)
            score -= penalty
            missing_recommended_labels.append(req.label)
        elif is_weak_field(field_key, value):
            score -= 1
            weak_field_labels.append(req.label)
        else:
            strength = _build_strength(req, value)
            if strength:
                strengths.append(strength)

    # Clamp
    score = max(0, min(100, score))

    level = _get_readiness_level(score)

    explanation = build_readiness_explanation(
        score=score,
        level=level,
        missing_critical=missing_critical_labels,
        missing_recommended=missing_recommended_labels,
        weak_fields=weak_field_labels,
        industry=industry,
    )

    next_steps = _build_next_steps(
        missing_critical=missing_critical_labels,
        missing_high=missing_high_labels,
        weak_fields=weak_field_labels,
        missing_recommended=missing_recommended_labels,
    )

    # Office learnings (additive only)
    office_learnings = []
    if office_id:
        ctx = get_office_context(office_id, industry)
        office_learnings = [l["note"] for l in ctx.get("learnings", [])]

    return {
        "industry": industry,
        "jurisdiction": effective_jurisdiction,
        "readiness_score": score,
        "readiness_level": level,
        "missing_critical_fields": missing_critical_labels,
        "missing_recommended_fields": missing_recommended_labels,
        "weak_fields": weak_field_labels,
        "strengths": strengths,
        "next_steps": next_steps,
        "office_learnings": office_learnings,
        "explanation": explanation,
    }
