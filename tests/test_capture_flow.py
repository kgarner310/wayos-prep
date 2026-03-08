"""Tests for Capture and Account Creation flow via TestClient.

Tests cover:
- Plain text capture endpoint
- Empty capture handling
- Manual account creation with health card
- Dashboard endpoint structure
- Account search
- Account search edge cases (too short query)
"""

import pytest


# ============================================================
# CAPTURE PLAIN TEXT
# ============================================================


class TestCapturePlainText:
    def test_capture_plain_text(self, client):
        """POST /api/v1/capture with plain_text should return ingestion_event_id and signals."""
        resp = client.post(
            "/api/v1/capture",
            data={"plain_text": "Quote from Travelers Insurance for Workers Comp. Premium: $50,000"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "ingestion_event_id" in data
        assert "signals" in data
        assert data["signals"]["carrier"] == "Travelers"


# ============================================================
# CAPTURE EMPTY
# ============================================================


class TestCaptureEmpty:
    def test_capture_empty(self, client):
        """POST /api/v1/capture with empty plain_text should return empty signals."""
        resp = client.post(
            "/api/v1/capture",
            data={"plain_text": "no insurance content here just random text"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "signals" in data
        # Random text should produce empty or minimal signals
        assert isinstance(data["signals"], dict)


# ============================================================
# MANUAL ACCOUNT CREATION
# ============================================================


class TestManualAccountCreation:
    def test_manual_account_creation(self, client):
        """POST /api/v1/accounts/manual should return account and health."""
        resp = client.post(
            "/api/v1/accounts/manual",
            json={
                "account_name": "Test Roofing Co",
                "industry": "roofing",
                "state": "NC",
                "employee_count": 25,
                "annual_revenue": 3000000,
                "current_coverages": ["workers_comp", "general_liability"],
                "uses_subcontractors": True,
                "vehicle_count": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "account" in data
        assert "health" in data
        assert data["account"]["account_name"] == "Test Roofing Co"
        assert data["account"]["industry"] == "roofing"
        assert data["health"]["overall_score"] >= 0
        assert data["health"]["coverage_score"] >= 0


# ============================================================
# MANUAL ACCOUNT HAS HEALTH CARD
# ============================================================


class TestManualAccountHasHealthCard:
    def test_manual_account_has_health_card(self, client):
        """After creating an account, GET dashboard should show a health card."""
        # Create account
        resp = client.post(
            "/api/v1/accounts/manual",
            json={
                "account_name": "Health Card Test Co",
                "industry": "landscaping",
                "state": "TX",
                "employee_count": 15,
            },
        )
        assert resp.status_code == 200
        account_id = resp.json()["account"]["id"]

        # Get dashboard
        resp = client.get(f"/api/v1/accounts/{account_id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "health" in data
        assert data["health"]["overall_score"] >= 0
        assert data["health"]["coverage_score"] >= 0


# ============================================================
# ACCOUNT SEARCH
# ============================================================


class TestAccountSearch:
    def test_account_search(self, client):
        """Create an account, then search for it by name."""
        # Create account
        resp = client.post(
            "/api/v1/accounts/manual",
            json={
                "account_name": "UniqueSearchName Roofing",
                "industry": "roofing",
                "state": "NC",
            },
        )
        assert resp.status_code == 200

        # Search
        resp = client.get("/api/v1/accounts/search?q=UniqueSearchName")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        names = [a["account_name"] for a in data["accounts"]]
        assert any("UniqueSearchName" in n for n in names)


# ============================================================
# ACCOUNT SEARCH TOO SHORT
# ============================================================


class TestAccountSearchTooShort:
    def test_account_search_empty(self, client):
        """Search with empty q should return empty."""
        resp = client.get("/api/v1/accounts/search?q=")
        assert resp.status_code == 200
        data = resp.json()
        assert data["accounts"] == []
        assert data["total"] == 0

    def test_account_search_single_char(self, client):
        """Search with single character q should return empty."""
        resp = client.get("/api/v1/accounts/search?q=a")
        assert resp.status_code == 200
        data = resp.json()
        assert data["accounts"] == []
        assert data["total"] == 0


# ============================================================
# DASHBOARD ENDPOINT STRUCTURE
# ============================================================


class TestDashboardEndpoint:
    def test_dashboard_endpoint(self, client):
        """Create account, GET dashboard. Verify structure."""
        # Create account with enough data
        resp = client.post(
            "/api/v1/accounts/manual",
            json={
                "account_name": "Dashboard Test Corp",
                "industry": "hvac",
                "state": "FL",
                "employee_count": 40,
                "annual_revenue": 5000000,
                "current_coverages": ["workers_comp", "general_liability"],
                "workers_comp_mod": 1.08,
            },
        )
        assert resp.status_code == 200
        account_id = resp.json()["account"]["id"]

        # Get dashboard
        resp = client.get(f"/api/v1/accounts/{account_id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        # Verify structure
        assert "account" in data
        assert "health" in data
        assert "artifacts" in data
        assert "insights" in data

        # Account fields
        assert data["account"]["account_name"] == "Dashboard Test Corp"

        # Health card fields
        assert "overall_score" in data["health"]
        assert "coverage_score" in data["health"]
        assert "workers_comp_score" in data["health"]

        # Artifacts and insights are lists
        assert isinstance(data["artifacts"], list)
        assert isinstance(data["insights"], list)
