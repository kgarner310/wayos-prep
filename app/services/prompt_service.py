"""Prompt Service — loads and builds prompts for artifact generation.

Reads system prompts from app/prompts/ directory and constructs
(system_prompt, user_prompt) pairs for LLM artifact generation.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

# In-memory cache
_prompt_cache: dict[str, str] = {}


def load_prompt(artifact_type: str) -> str:
    """Load system prompt for an artifact type from file."""
    if artifact_type in _prompt_cache:
        return _prompt_cache[artifact_type]

    filename = f"{artifact_type}_system.txt"
    filepath = os.path.join(PROMPTS_DIR, filename)

    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
        _prompt_cache[artifact_type] = content
        return content
    except FileNotFoundError:
        logger.warning("Prompt file not found: %s", filepath)
        return ""


def build_artifact_prompt(artifact_type: str, account_data: dict) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) pair for artifact generation.

    Args:
        artifact_type: One of coverage_gap, meeting_brief, workers_comp_snapshot, winnability
        account_data: Dict with account fields

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = load_prompt(artifact_type)

    # Build user prompt from account data
    parts = ["Analyze this commercial insurance account:\n"]

    name = account_data.get("account_name") or account_data.get("named_insured") or "Unknown"
    parts.append(f"Account: {name}")

    if account_data.get("industry"):
        parts.append(f"Industry: {account_data['industry']}")
    if account_data.get("state"):
        parts.append(f"State: {account_data['state']}")
    if account_data.get("employee_count"):
        parts.append(f"Employees: {account_data['employee_count']}")
    if account_data.get("annual_revenue"):
        parts.append(f"Annual Revenue: ${account_data['annual_revenue']:,.0f}")
    if account_data.get("payroll_estimate"):
        parts.append(f"Payroll Estimate: ${account_data['payroll_estimate']:,.0f}")

    coverages = account_data.get("current_coverages") or []
    if coverages:
        parts.append(f"Current Coverages: {', '.join(coverages)}")
    else:
        parts.append("Current Coverages: Not provided")

    carriers = account_data.get("current_carriers") or []
    if carriers:
        parts.append(f"Current Carriers: {', '.join(carriers)}")

    mod = account_data.get("workers_comp_mod")
    if mod is not None:
        parts.append(f"Workers Comp Mod: {mod}")

    claims = account_data.get("claims_summary")
    if claims:
        parts.append(f"Claims Summary: {claims}")

    if account_data.get("vehicle_count"):
        parts.append(f"Vehicles: {account_data['vehicle_count']}")
    if account_data.get("uses_subcontractors"):
        parts.append("Uses subcontractors: Yes")

    notes = account_data.get("notes") or ""
    if notes:
        parts.append(f"\nAdditional Notes: {notes}")

    user_prompt = "\n".join(parts)
    return system_prompt, user_prompt


def clear_prompt_cache():
    """Clear the in-memory prompt cache."""
    _prompt_cache.clear()
