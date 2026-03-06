"""Tests for brief generator: state code extraction and state enrichment."""
from app.services.brief_generator import extract_state_code
from app.services.brief_renderer import build_brief_json, render_brief_text


class TestExtractStateCode:
    """Test state code extraction from various location formats."""

    def test_two_letter_code(self):
        assert extract_state_code("NC") == "NC"

    def test_city_comma_code(self):
        assert extract_state_code("Asheville, NC") == "NC"

    def test_city_space_code(self):
        assert extract_state_code("Asheville NC") == "NC"

    def test_full_state_name(self):
        assert extract_state_code("North Carolina") == "NC"

    def test_city_full_state_name(self):
        assert extract_state_code("Charlotte, North Carolina") == "NC"

    def test_georgia(self):
        assert extract_state_code("Savannah, GA") == "GA"

    def test_tennessee_full(self):
        assert extract_state_code("Tennessee") == "TN"

    def test_south_carolina(self):
        assert extract_state_code("Myrtle Beach, SC") == "SC"

    def test_unknown_returns_none(self):
        assert extract_state_code("Not specified") is None

    def test_empty_returns_none(self):
        assert extract_state_code("") is None

    def test_none_returns_none(self):
        assert extract_state_code(None) is None

    def test_lowercase_full_name(self):
        assert extract_state_code("north carolina") == "NC"


class TestBriefJsonWithState:
    """Test that brief JSON includes state data when provided."""

    def test_brief_without_state_data(self):
        result = build_brief_json(
            industry_name="Roofing",
            location="Asheville, NC",
            employee_count=50,
            mod=1.2,
            vehicle_exposure="10 trucks",
            top_claims=["Falls from height"],
            regional_notes="Hail belt exposure.",
            coverage_exposures=["Property damage"],
            conversation_starters=["How do you manage fall protection?"],
        )
        assert "state_wc_notes" not in result
        assert "state_compliance_items" not in result

    def test_brief_with_state_data(self):
        result = build_brief_json(
            industry_name="Roofing",
            location="Asheville, NC",
            employee_count=50,
            mod=1.2,
            vehicle_exposure="10 trucks",
            top_claims=["Falls from height"],
            regional_notes="Hail belt exposure.",
            coverage_exposures=["Property damage"],
            conversation_starters=["How do you manage fall protection?"],
            state_wc_notes="NC WC rules apply.",
            state_compliance_items=["NC GC License required"],
            tort_environment="moderate",
            cat_exposures=["Hurricane exposure on coast"],
        )
        assert result["state_wc_notes"] == "NC WC rules apply."
        assert result["state_compliance_items"] == ["NC GC License required"]
        assert result["tort_environment"] == "moderate"
        assert result["cat_exposures"] == ["Hurricane exposure on coast"]

    def test_rendered_brief_includes_state_sections(self):
        brief_json = build_brief_json(
            industry_name="Roofing",
            location="Asheville, NC",
            employee_count=50,
            mod=None,
            vehicle_exposure=None,
            top_claims=["Falls"],
            regional_notes="Notes.",
            coverage_exposures=["GL"],
            conversation_starters=["Q1"],
            state_wc_notes="NC WC rules.",
            state_compliance_items=["GC License required"],
            tort_environment="moderate",
            cat_exposures=["Hurricane risk"],
        )
        text = render_brief_text(brief_json)
        assert "STATE WORKERS COMP NOTES" in text
        assert "NC WC rules." in text
        assert "STATE-SPECIFIC COMPLIANCE" in text
        assert "GC License required" in text
        assert "CATASTROPHE EXPOSURES" in text
        assert "Hurricane risk" in text
        assert "TORT ENVIRONMENT: MODERATE" in text

    def test_rendered_brief_without_state_has_no_state_sections(self):
        brief_json = build_brief_json(
            industry_name="Roofing",
            location="Somewhere",
            employee_count=None,
            mod=None,
            vehicle_exposure=None,
            top_claims=["Falls"],
            regional_notes="Notes.",
            coverage_exposures=["GL"],
            conversation_starters=["Q1"],
        )
        text = render_brief_text(brief_json)
        assert "STATE WORKERS COMP NOTES" not in text
        assert "STATE-SPECIFIC COMPLIANCE" not in text
