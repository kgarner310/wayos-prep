"""Tests for the brief renderer service."""
from app.services.brief_renderer import (
    build_brief_json,
    render_brief_text,
    render_underwriter_email,
    render_internal_note,
)


def test_build_brief_json():
    result = build_brief_json(
        industry_name="Roofing",
        location="North Carolina",
        employee_count=12,
        mod=1.15,
        vehicle_exposure="3 trucks",
        top_claims=["Falls from height", "Heat illness"],
        regional_notes="Hail belt exposure.",
        coverage_exposures=["Property damage from leaks"],
        conversation_starters=["How do you manage fall protection?"],
    )

    assert result["industry"] == "Roofing"
    assert result["location"] == "North Carolina"
    assert result["employee_count"] == 12
    assert result["mod"] == 1.15
    assert result["vehicle_exposure"] == "3 trucks"
    assert len(result["top_claim_drivers"]) == 2
    assert len(result["docs_to_request"]) == 4
    assert "generated_at" in result


def test_render_brief_text():
    brief_json = build_brief_json(
        industry_name="Roofing",
        location="North Carolina",
        employee_count=12,
        mod=1.15,
        vehicle_exposure="3 trucks",
        top_claims=["Falls from height", "Heat illness"],
        regional_notes="Hail belt exposure.",
        coverage_exposures=["Property damage from leaks"],
        conversation_starters=["How do you manage fall protection?"],
    )

    text = render_brief_text(brief_json)

    assert "WAYOS PREP — CLIENT BRIEF" in text
    assert "Roofing" in text
    assert "North Carolina" in text
    assert "12" in text
    assert "1.15" in text
    assert "Falls from height" in text
    assert "TOP CLAIM DRIVERS" in text
    assert "COVERAGE EXPOSURES" in text
    assert "CONVERSATION STARTERS" in text
    assert "QUICK DOCS TO REQUEST" in text
    assert "wayosprep.app" in text


def test_render_brief_text_with_na():
    brief_json = build_brief_json(
        industry_name="Landscaping",
        location="Texas",
        employee_count=None,
        mod=None,
        vehicle_exposure=None,
        top_claims=["Chemical exposure"],
        regional_notes="Year-round exposure.",
        coverage_exposures=["Herbicide overspray"],
        conversation_starters=["How many crew vehicles?"],
    )

    text = render_brief_text(brief_json)
    assert "N/A" in text


def test_render_underwriter_email():
    brief_json = build_brief_json(
        industry_name="Roofing",
        location="North Carolina",
        employee_count=12,
        mod=1.15,
        vehicle_exposure="3 trucks",
        top_claims=["Falls from height"],
        regional_notes="Hail belt exposure.",
        coverage_exposures=["Property damage"],
        conversation_starters=["Fall protection?"],
    )

    email = render_underwriter_email(brief_json)

    assert "Subject: Roofing Risk Notes" in email
    assert "North Carolina" in email
    assert "TOP CLAIM DRIVERS" in email
    assert "DOCUMENTS I WILL REQUEST" in email
    assert "wayosprep.app" in email


def test_render_internal_note():
    brief_json = build_brief_json(
        industry_name="Roofing",
        location="North Carolina",
        employee_count=12,
        mod=1.15,
        vehicle_exposure=None,
        top_claims=["Falls from height"],
        regional_notes="Hail belt exposure.",
        coverage_exposures=["Property damage"],
        conversation_starters=["Fall protection?"],
    )

    note = render_internal_note(brief_json)

    assert "WAYOS PREP — ACCOUNT PREP" in note
    assert "Roofing" in note
    assert "Big exposures" in note
    assert "Claim patterns" in note
    assert "Questions for insured" in note
    assert "wayosprep.app" in note
