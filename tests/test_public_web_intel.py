"""Tests for Public Web Intelligence Extractor."""

import pytest

from app.services.public_web_intel import extract_public_web_intel


# ============================================================
# FIXTURES
# ============================================================

ROOFING_WEBSITE_TEXT = """
Apex Roofing – Serving Charlotte and Mecklenburg County Since 2012

We specialize in residential roof replacement, storm restoration, and steep-slope
roofing for homeowners across the greater Charlotte area. Our crews are OSHA-trained
with full fall protection and ladder safety certification.

As a CertainTeed-certified installer, we deliver manufacturer-backed quality.
All work is bonded and insured. We use subcontractors for specialized gutter and
siding work under strict certificate compliance requirements.

Our multi-crew operations allow us to handle 3-5 active job sites simultaneously.
"""

ROOFING_SOCIAL_TEXT = """
Excited to share our latest project – complete roof replacement in Huntersville!

Now hiring experienced roofers for our growing team.

Proud to be recognized as a 2024 Top Contractor by Charlotte Business Journal.

Storm season is here – our storm response crews are ready to help homeowners
with damage assessment and emergency tarping.
"""

TRUCKING_WEBSITE_TEXT = """
FastFreight Logistics – Long haul refrigerated transport since 1998.

We operate a fleet of 45 temperature-controlled trucks across the eastern seaboard.
DOT-compliant with a comprehensive drug testing and safety training program.
All drivers are CDL-A certified with hazmat endorsement available.
"""

MINIMAL_TEXT = "We fix things."


# ============================================================
# COMPANY IDENTITY TESTS
# ============================================================


class TestCompanyIdentity:

    def test_company_name_passthrough(self):
        result = extract_public_web_intel({
            "company_name": "Apex Roofing",
            "raw_website_text": ROOFING_WEBSITE_TEXT,
        })
        assert result["company_identity"]["company_name"] == "Apex Roofing"

    def test_founded_year_extracted(self):
        result = extract_public_web_intel({
            "company_name": "Apex Roofing",
            "raw_website_text": ROOFING_WEBSITE_TEXT,
        })
        assert result["company_identity"]["founded_year"] == 2012

    def test_service_area_extracted(self):
        result = extract_public_web_intel({
            "company_name": "Apex Roofing",
            "raw_website_text": ROOFING_WEBSITE_TEXT,
        })
        areas = result["company_identity"]["service_area"]
        assert len(areas) >= 1
        assert any("Charlotte" in a for a in areas)

    def test_no_text_empty_identity(self):
        result = extract_public_web_intel({"company_name": "Test Co"})
        assert result["company_identity"]["company_name"] == "Test Co"
        assert result["company_identity"]["founded_year"] is None
        assert result["company_identity"]["service_area"] == []


# ============================================================
# OPERATIONS SIGNAL TESTS
# ============================================================


class TestOperationsSignals:

    def test_roofing_operations_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        ops = result["operations_signals"]
        assert any("replacement" in s.lower() or "repair" in s.lower() for s in ops)

    def test_storm_restoration_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        ops = result["operations_signals"]
        assert any("storm" in s.lower() for s in ops)

    def test_steep_slope_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        ops = result["operations_signals"]
        assert any("steep" in s.lower() for s in ops)

    def test_trucking_operations_detected(self):
        result = extract_public_web_intel({"raw_website_text": TRUCKING_WEBSITE_TEXT})
        ops = result["operations_signals"]
        assert any("haul" in s.lower() for s in ops)

    def test_refrigerated_detected(self):
        result = extract_public_web_intel({"raw_website_text": TRUCKING_WEBSITE_TEXT})
        ops = result["operations_signals"]
        assert any("temperature" in s.lower() for s in ops)

    def test_empty_text_no_ops(self):
        result = extract_public_web_intel({"raw_website_text": ""})
        assert result["operations_signals"] == []

    def test_operations_capped(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        assert len(result["operations_signals"]) <= 8


# ============================================================
# SAFETY SIGNAL TESTS
# ============================================================


class TestSafetySignals:

    def test_osha_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        safety = result["safety_signals"]
        assert any("osha" in s.lower() for s in safety)

    def test_fall_protection_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        safety = result["safety_signals"]
        assert any("fall protection" in s.lower() for s in safety)

    def test_ladder_safety_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        safety = result["safety_signals"]
        assert any("ladder" in s.lower() for s in safety)

    def test_dot_compliance_detected(self):
        result = extract_public_web_intel({"raw_website_text": TRUCKING_WEBSITE_TEXT})
        safety = result["safety_signals"]
        assert any("dot" in s.lower() for s in safety)

    def test_drug_testing_detected(self):
        result = extract_public_web_intel({"raw_website_text": TRUCKING_WEBSITE_TEXT})
        safety = result["safety_signals"]
        assert any("drug" in s.lower() for s in safety)

    def test_no_safety_from_minimal_text(self):
        result = extract_public_web_intel({"raw_website_text": MINIMAL_TEXT})
        assert result["safety_signals"] == []


# ============================================================
# SCALE SIGNAL TESTS
# ============================================================


class TestScaleSignals:

    def test_multi_crew_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        scale = result["scale_signals"]
        assert any("multi" in s.lower() for s in scale)

    def test_fleet_size_detected(self):
        result = extract_public_web_intel({"raw_website_text": TRUCKING_WEBSITE_TEXT})
        scale = result["scale_signals"]
        # "fleet of 45" or similar should match
        assert len(scale) >= 1

    def test_founding_year_in_scale(self):
        result = extract_public_web_intel({"raw_website_text": TRUCKING_WEBSITE_TEXT})
        scale = result["scale_signals"]
        assert any("founding" in s.lower() or "year" in s.lower() for s in scale)


# ============================================================
# CARRIER-RELEVANT SIGNAL TESTS
# ============================================================


class TestCarrierSignals:

    def test_certification_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        carrier = result["carrier_relevant_signals"]
        assert any("certif" in s.lower() for s in carrier)

    def test_subcontractor_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        carrier = result["carrier_relevant_signals"]
        assert any("subcontract" in s.lower() for s in carrier)

    def test_bonding_detected(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        carrier = result["carrier_relevant_signals"]
        assert any("bond" in s.lower() for s in carrier)


# ============================================================
# OBSERVED PUBLIC SIGNAL TESTS (SOCIAL)
# ============================================================


class TestObservedSignals:

    def test_social_signals_extracted(self):
        result = extract_public_web_intel({"raw_social_text": ROOFING_SOCIAL_TEXT})
        observed = result["observed_public_signals"]
        assert len(observed) >= 1

    def test_hiring_detected(self):
        result = extract_public_web_intel({"raw_social_text": ROOFING_SOCIAL_TEXT})
        observed = result["observed_public_signals"]
        assert any("hiring" in s.lower() for s in observed)

    def test_storm_response_detected(self):
        result = extract_public_web_intel({"raw_social_text": ROOFING_SOCIAL_TEXT})
        observed = result["observed_public_signals"]
        assert any("storm" in s.lower() or "weather" in s.lower() for s in observed)

    def test_no_social_no_observed(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        assert result["observed_public_signals"] == []


# ============================================================
# CAUTION TESTS
# ============================================================


class TestCautions:

    def test_caution_with_website_text(self):
        result = extract_public_web_intel({"raw_website_text": ROOFING_WEBSITE_TEXT})
        assert any("marketing" in c.lower() or "verified" in c.lower() for c in result["cautions"])

    def test_caution_with_social_text(self):
        result = extract_public_web_intel({"raw_social_text": ROOFING_SOCIAL_TEXT})
        assert any("social" in c.lower() for c in result["cautions"])

    def test_caution_with_no_text(self):
        result = extract_public_web_intel({"company_name": "Test Co"})
        assert any("no public" in c.lower() or "limited" in c.lower() for c in result["cautions"])


# ============================================================
# GRACEFUL DEGRADATION TESTS
# ============================================================


class TestGracefulDegradation:

    def test_empty_input(self):
        result = extract_public_web_intel({})
        assert result["company_identity"]["company_name"] == ""
        assert result["operations_signals"] == []
        assert result["safety_signals"] == []

    def test_minimal_text_no_crash(self):
        result = extract_public_web_intel({"raw_website_text": MINIMAL_TEXT})
        assert isinstance(result, dict)

    def test_response_structure(self):
        result = extract_public_web_intel({})
        expected_keys = {
            "company_identity", "operations_signals", "safety_signals",
            "scale_signals", "carrier_relevant_signals",
            "observed_public_signals", "cautions",
        }
        assert set(result.keys()) == expected_keys


# ============================================================
# API ENDPOINT TEST
# ============================================================


class TestAPIEndpoint:

    @pytest.fixture
    def client(self):
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.session import get_db

        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_endpoint_returns_200(self, client):
        response = client.post("/api/v1/intel/public-web-intel", json={
            "company_name": "Apex Roofing",
            "raw_website_text": ROOFING_WEBSITE_TEXT,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["company_identity"]["company_name"] == "Apex Roofing"
        assert len(data["operations_signals"]) >= 1

    def test_endpoint_empty_body(self, client):
        response = client.post("/api/v1/intel/public-web-intel", json={})
        assert response.status_code == 200
