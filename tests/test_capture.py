"""Tests for QuickCapture ingestion.

Tests cover:
- File type detection
- Text signal parsing (carrier, premium, coverage, mod, employee count)
- Plain text capture processing
- API endpoint integration
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.services.capture_service import (
    detect_file_type,
    parse_insurance_signals,
    process_capture,
)
from app.main import app
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()


# ============================================================
# FILE TYPE DETECTION
# ============================================================


class TestDetectFileType:
    def test_pdf_by_extension(self):
        assert detect_file_type("quote.pdf") == "pdf"

    def test_image_jpg(self):
        assert detect_file_type("screenshot.jpg") == "image"

    def test_image_png(self):
        assert detect_file_type("doc.PNG") == "image"

    def test_text_by_extension(self):
        assert detect_file_type("notes.txt") == "text"

    def test_csv_by_extension(self):
        assert detect_file_type("data.csv") == "text"

    def test_pdf_by_content_type(self):
        assert detect_file_type("unknown", "application/pdf") == "pdf"

    def test_image_by_content_type(self):
        assert detect_file_type("unknown", "image/png") == "image"

    def test_unknown_defaults_text(self):
        assert detect_file_type("unknown", "application/octet-stream") == "text"


# ============================================================
# SIGNAL PARSING
# ============================================================


class TestParseInsuranceSignals:
    def test_empty_text(self):
        assert parse_insurance_signals("") == {}

    def test_carrier_detection(self):
        text = "Quote from Travelers Insurance for Workers Comp"
        signals = parse_insurance_signals(text)
        assert signals["carrier"] == "Travelers"

    def test_premium_detection(self):
        text = "Annual Premium: $142,000.00"
        signals = parse_insurance_signals(text)
        assert signals["premium"] == 142000

    def test_premium_without_cents(self):
        text = "Total Premium: $85,500"
        signals = parse_insurance_signals(text)
        assert signals["premium"] == 85500

    def test_coverage_type_detection(self):
        text = "Policy: Workers Compensation coverage effective 01/01/2025"
        signals = parse_insurance_signals(text)
        assert signals["coverage"] == "Workers Compensation"

    def test_coverage_gl(self):
        text = "This general liability policy provides..."
        signals = parse_insurance_signals(text)
        assert signals["coverage"] == "General Liability"

    def test_coverage_cyber(self):
        text = "Cyber liability limit: $1,000,000"
        signals = parse_insurance_signals(text)
        assert signals["coverage"] == "Cyber Liability"

    def test_mod_detection(self):
        text = "Experience Mod: 0.87"
        signals = parse_insurance_signals(text)
        assert signals["mod"] == 0.87

    def test_mod_emod(self):
        text = "Current EMOD: 1.15"
        signals = parse_insurance_signals(text)
        assert signals["mod"] == 1.15

    def test_mod_out_of_range_skipped(self):
        text = "Experience Mod: 5.0"
        signals = parse_insurance_signals(text)
        assert "mod" not in signals

    def test_employee_count(self):
        text = "Company has 250 employees"
        signals = parse_insurance_signals(text)
        assert signals["employee_count"] == 250

    def test_employee_count_label(self):
        text = "Employee Count: 45"
        signals = parse_insurance_signals(text)
        assert signals["employee_count"] == 45

    def test_coverage_limit(self):
        text = "Each Occurrence Limit: $1,000,000"
        signals = parse_insurance_signals(text)
        assert signals["coverage_limit"] == 1000000

    def test_multiple_signals(self):
        text = """
        Cincinnati Insurance Company
        Workers Compensation Policy
        Annual Premium: $67,500
        Experience Mod: 0.92
        Employees: 85
        """
        signals = parse_insurance_signals(text)
        assert signals["carrier"] == "Cincinnati"
        assert signals["coverage"] == "Workers Compensation"
        assert signals["premium"] == 67500
        assert signals["mod"] == 0.92
        assert signals["employee_count"] == 85

    def test_no_signals_in_random_text(self):
        text = "The quick brown fox jumps over the lazy dog"
        signals = parse_insurance_signals(text)
        assert signals == {}


# ============================================================
# PROCESS CAPTURE
# ============================================================


class TestProcessCapture:
    def test_plain_text(self):
        result = process_capture(plain_text="Premium: $50,000 from Travelers")
        assert result["source_type"] == "text"
        assert result["signals"]["carrier"] == "Travelers"
        assert result["signals"]["premium"] == 50000

    def test_file_bytes_text(self):
        text = "Hartford quote for General Liability $25,000"
        result = process_capture(
            file_bytes=text.encode("utf-8"),
            filename="quote.txt",
        )
        assert result["source_type"] == "text"
        assert result["signals"]["carrier"] == "Hartford"

    def test_no_input(self):
        result = process_capture()
        assert result["signals"] == {}

    def test_extracted_text_included(self):
        result = process_capture(plain_text="Some insurance text")
        assert result["extracted_text"] == "Some insurance text"


# ============================================================
# API ENDPOINT
# ============================================================


class TestCaptureEndpoint:
    def test_capture_plain_text(self):
        resp = client.post(
            "/api/v1/capture",
            data={"plain_text": "Quote from Travelers: Premium $100,000"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["signals"]["carrier"] == "Travelers"
        assert data["signals"]["premium"] == 100000

    def test_capture_with_account_id(self):
        resp = client.post(
            "/api/v1/capture",
            data={
                "plain_text": "Cincinnati WC quote",
                "account_id": "acct-123",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["account_id"] == "acct-123"

    def test_capture_no_input(self):
        resp = client.post("/api/v1/capture", data={})
        assert resp.status_code == 422
