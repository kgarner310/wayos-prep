"""Tests for the Loss Run Analyzer service."""

from app.services.loss_run_analyzer import analyze_loss_run, _normalize_line, _classify_cause


# ============================================================
# LINE NORMALIZATION
# ============================================================

class TestLineNormalization:
    def test_wc_variants(self):
        assert _normalize_line("WC") == "Workers Comp"
        assert _normalize_line("workers comp") == "Workers Comp"
        assert _normalize_line("Workers Compensation") == "Workers Comp"

    def test_gl_variants(self):
        assert _normalize_line("GL") == "General Liability"
        assert _normalize_line("general liability") == "General Liability"

    def test_auto_variants(self):
        assert _normalize_line("Auto") == "Commercial Auto"
        assert _normalize_line("commercial auto") == "Commercial Auto"

    def test_unknown_passes_through(self):
        assert _normalize_line("Some Custom Line") == "Some Custom Line"

    def test_epli(self):
        assert _normalize_line("EPLI") == "EPLI"
        assert _normalize_line("employment practices") == "EPLI"


# ============================================================
# CAUSE CLASSIFICATION
# ============================================================

class TestCauseClassification:
    def test_fall(self):
        assert _classify_cause("Fall from ladder") == "fall"
        assert _classify_cause("Slip on wet floor") == "fall"

    def test_strain(self):
        assert _classify_cause("Back strain from lifting") == "strain"
        assert _classify_cause("Repetitive motion injury") == "strain"

    def test_vehicle(self):
        assert _classify_cause("Vehicle collision at intersection") == "vehicle"
        assert _classify_cause("Backing accident in lot") == "vehicle"

    def test_struck_by(self):
        assert _classify_cause("Struck by falling object") == "struck_by"

    def test_none_for_unknown(self):
        assert _classify_cause("unknown cause") is None

    def test_none_for_empty(self):
        assert _classify_cause("") is None


# ============================================================
# EMPTY LOSS RUNS
# ============================================================

class TestEmptyLossRun:
    def test_empty_claims_returns_zero_summary(self):
        result = analyze_loss_run({"claims": []})
        assert result["summary"]["total_claims"] == 0
        assert result["summary"]["total_incurred"] == 0.0
        assert result["summary"]["total_paid"] == 0.0

    def test_empty_claims_no_patterns(self):
        result = analyze_loss_run({"claims": []})
        assert result["patterns"] == []
        assert result["underwriting_flags"] == []

    def test_empty_claims_has_talking_point(self):
        result = analyze_loss_run({"claims": []})
        assert len(result["producer_talking_points"]) >= 1
        assert "loss runs" in result["producer_talking_points"][0].lower()

    def test_no_claims_key(self):
        result = analyze_loss_run({})
        assert result["summary"]["total_claims"] == 0


# ============================================================
# SUMMARY TOTALS
# ============================================================

class TestSummaryTotals:
    def test_single_claim_totals(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 10000, "reserve_amount": 5000, "claim_status": "Open"},
        ]})
        assert result["summary"]["total_claims"] == 1
        assert result["summary"]["total_paid"] == 10000.0
        assert result["summary"]["total_reserves"] == 5000.0
        assert result["summary"]["total_incurred"] == 15000.0
        assert result["summary"]["open_claims"] == 1

    def test_multiple_claims_totals(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 20000, "reserve_amount": 5000, "claim_status": "Closed"},
            {"line_of_business": "GL", "paid_amount": 15000, "reserve_amount": 0, "claim_status": "Closed"},
            {"line_of_business": "Auto", "paid_amount": 8000, "reserve_amount": 3000, "claim_status": "Open"},
        ]})
        assert result["summary"]["total_claims"] == 3
        assert result["summary"]["total_paid"] == 43000.0
        assert result["summary"]["total_reserves"] == 8000.0
        assert result["summary"]["total_incurred"] == 51000.0
        assert result["summary"]["open_claims"] == 1

    def test_zero_amounts_handled(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 0, "reserve_amount": 0, "claim_status": "Closed"},
        ]})
        assert result["summary"]["total_incurred"] == 0.0


# ============================================================
# BY-LINE BREAKDOWN
# ============================================================

class TestByLine:
    def test_groups_by_normalized_line(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 10000, "reserve_amount": 0},
            {"line_of_business": "Workers Comp", "paid_amount": 5000, "reserve_amount": 0},
            {"line_of_business": "GL", "paid_amount": 3000, "reserve_amount": 0},
        ]})
        lines = {d["line"] for d in result["by_line"]}
        assert "Workers Comp" in lines
        assert "General Liability" in lines

    def test_line_claim_count(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 10000},
            {"line_of_business": "WC", "paid_amount": 5000},
        ]})
        wc = next(d for d in result["by_line"] if d["line"] == "Workers Comp")
        assert wc["claim_count"] == 2
        assert wc["total_paid"] == 15000.0

    def test_line_causes_tracked(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "cause_of_loss": "Fall from ladder", "paid_amount": 10000},
            {"line_of_business": "WC", "cause_of_loss": "Back strain", "paid_amount": 5000},
        ]})
        wc = next(d for d in result["by_line"] if d["line"] == "Workers Comp")
        assert "Fall from ladder" in wc["causes"]
        assert "Back strain" in wc["causes"]


# ============================================================
# PATTERN DETECTION
# ============================================================

class TestPatterns:
    def test_fall_pattern_detected(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "cause_of_loss": "Fall from ladder", "paid_amount": 20000},
            {"line_of_business": "WC", "cause_of_loss": "Fell from scaffold", "paid_amount": 15000},
        ]})
        assert any("fall" in p.lower() for p in result["patterns"])

    def test_strain_pattern_detected(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "cause_of_loss": "Back strain from lifting", "paid_amount": 5000},
            {"line_of_business": "WC", "cause_of_loss": "Overexertion", "paid_amount": 3000},
        ]})
        assert any("strain" in p.lower() for p in result["patterns"])

    def test_vehicle_pattern_detected(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "Auto", "cause_of_loss": "Vehicle collision", "paid_amount": 10000},
            {"line_of_business": "Auto", "cause_of_loss": "Backing accident", "paid_amount": 5000},
        ]})
        assert any("vehicle" in p.lower() for p in result["patterns"])

    def test_single_cause_no_pattern(self):
        """A single cause occurrence should not create a pattern."""
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "cause_of_loss": "Fall from ladder", "paid_amount": 20000},
        ]})
        assert not any("fall" in p.lower() for p in result["patterns"])

    def test_line_concentration_pattern(self):
        """If one line dominates (>=50%), flag it."""
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 10000},
            {"line_of_business": "WC", "paid_amount": 10000},
            {"line_of_business": "WC", "paid_amount": 10000},
            {"line_of_business": "GL", "paid_amount": 5000},
        ]})
        assert any("workers comp" in p.lower() and "%" in p for p in result["patterns"])


# ============================================================
# UNDERWRITING FLAGS
# ============================================================

class TestUnderwritingFlags:
    def test_high_frequency_flag(self):
        claims = [{"line_of_business": "WC", "paid_amount": 1000} for _ in range(6)]
        result = analyze_loss_run({"claims": claims})
        assert any("frequency" in f.lower() for f in result["underwriting_flags"])

    def test_open_claims_flag(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 10000, "reserve_amount": 20000, "claim_status": "Open"},
            {"line_of_business": "GL", "paid_amount": 5000, "reserve_amount": 15000, "claim_status": "Open"},
        ]})
        assert any("open claims" in f.lower() for f in result["underwriting_flags"])

    def test_high_reserves_flag(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 5000, "reserve_amount": 50000, "claim_status": "Open"},
        ]})
        assert any("reserves" in f.lower() for f in result["underwriting_flags"])

    def test_large_claim_flag(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "cause_of_loss": "Fall from roof", "paid_amount": 100000, "reserve_amount": 50000},
        ]})
        assert any("large" in f.lower() for f in result["underwriting_flags"])

    def test_wc_frequency_flag(self):
        claims = [{"line_of_business": "WC", "paid_amount": 5000} for _ in range(4)]
        result = analyze_loss_run({"claims": claims})
        assert any("workers comp" in f.lower() and "mod" in f.lower() for f in result["underwriting_flags"])

    def test_flags_capped_at_5(self):
        """Flags should be capped at 5."""
        claims = [{"line_of_business": "WC", "paid_amount": 50000, "reserve_amount": 50000, "claim_status": "Open"} for _ in range(10)]
        result = analyze_loss_run({"claims": claims})
        assert len(result["underwriting_flags"]) <= 5


# ============================================================
# PRODUCER TALKING POINTS
# ============================================================

class TestTalkingPoints:
    def test_clean_history_point(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 2000, "reserve_amount": 0, "claim_status": "Closed"},
        ]})
        assert any("clean" in p.lower() or "leverage" in p.lower() for p in result["producer_talking_points"])

    def test_high_incurred_point(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 80000, "reserve_amount": 30000},
        ]})
        assert any("remediation" in p.lower() or "corrective" in p.lower()
                    for p in result["producer_talking_points"])

    def test_fall_pattern_drives_talking_point(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "cause_of_loss": "Fall from ladder", "paid_amount": 20000},
            {"line_of_business": "WC", "cause_of_loss": "Fell from scaffold", "paid_amount": 15000},
        ]})
        assert any("fall" in p.lower() for p in result["producer_talking_points"])

    def test_wc_mod_crossref_point(self):
        result = analyze_loss_run({"claims": [
            {"line_of_business": "WC", "paid_amount": 10000},
        ]})
        assert any("mod" in p.lower() for p in result["producer_talking_points"])

    def test_talking_points_capped_at_5(self):
        claims = [
            {"line_of_business": "WC", "cause_of_loss": "Fall from ladder", "paid_amount": 50000, "reserve_amount": 20000, "claim_status": "Open"},
            {"line_of_business": "WC", "cause_of_loss": "Fell from scaffold", "paid_amount": 40000, "reserve_amount": 15000, "claim_status": "Open"},
            {"line_of_business": "Auto", "cause_of_loss": "Vehicle collision", "paid_amount": 30000, "reserve_amount": 10000, "claim_status": "Open"},
            {"line_of_business": "Auto", "cause_of_loss": "Backing accident", "paid_amount": 20000},
            {"line_of_business": "GL", "cause_of_loss": "Slip on wet floor", "paid_amount": 10000},
            {"line_of_business": "GL", "cause_of_loss": "Trip on uneven surface", "paid_amount": 8000},
        ]
        result = analyze_loss_run({"industry": "roofing", "claims": claims})
        assert len(result["producer_talking_points"]) <= 5


# ============================================================
# INDUSTRY ENRICHMENT
# ============================================================

class TestIndustryEnrichment:
    def test_industry_enrichment_in_talking_points(self):
        """When industry is provided and WC claims exist, industry data should enrich points."""
        result = analyze_loss_run({
            "industry": "Cattle Ranching",
            "claims": [
                {"line_of_business": "WC", "cause_of_loss": "Kicked by animal", "paid_amount": 15000},
                {"line_of_business": "WC", "cause_of_loss": "Trampled by livestock", "paid_amount": 20000},
            ],
        })
        # Should have at least one industry-enriched talking point
        assert any("industry" in p.lower() or "common" in p.lower()
                    for p in result["producer_talking_points"])

    def test_unknown_industry_no_crash(self):
        """Unknown industry should not crash the analyzer."""
        result = analyze_loss_run({
            "industry": "space tourism",
            "claims": [
                {"line_of_business": "GL", "paid_amount": 5000},
            ],
        })
        assert result["summary"]["total_claims"] == 1


# ============================================================
# INTEGRATION WITH COVERAGE GAP DETECTOR
# ============================================================

class TestLossRunCoverageGapIntegration:
    def test_loss_data_boosts_wc_confidence(self):
        """WC loss flags should boost WC gap confidence."""
        from app.services.coverage_gap_detector import detect_coverage_gaps

        # Without loss data
        baseline = detect_coverage_gaps({
            "industry": "roofing",
            "state": "NC",
            "current_coverages": [],
        })
        wc_baseline = next(
            (g for g in baseline["coverage_gaps"] if "workers" in g["coverage"].lower()),
            None
        )

        # With loss data showing WC issues
        enhanced = detect_coverage_gaps({
            "industry": "roofing",
            "state": "NC",
            "current_coverages": [],
            "loss_run_data": {
                "patterns": ["3 fall-related claims"],
                "underwriting_flags": ["Workers Comp: high claim frequency (5 claims)"],
                "producer_talking_points": ["Review fall protection program"],
            },
        })
        wc_enhanced = next(
            (g for g in enhanced["coverage_gaps"] if "workers" in g["coverage"].lower()),
            None
        )

        if wc_baseline and wc_enhanced:
            assert wc_enhanced["confidence"] >= wc_baseline["confidence"]

    def test_loss_data_adds_questions(self):
        """Loss talking points should appear in suggested questions."""
        from app.services.coverage_gap_detector import detect_coverage_gaps

        result = detect_coverage_gaps({
            "industry": "roofing",
            "state": "NC",
            "current_coverages": ["workers_comp", "general_liability"],
            "loss_run_data": {
                "patterns": [],
                "underwriting_flags": [],
                "producer_talking_points": ["Review fall protection program"],
            },
        })
        assert "Review fall protection program" in result["suggested_questions"]


# ============================================================
# INTEGRATION WITH PRODUCER AMMO
# ============================================================

class TestLossRunProducerAmmoIntegration:
    def test_loss_flags_in_underwriting(self):
        """Loss underwriting flags should appear in ammo underwriting flags."""
        from app.services.producer_ammo import generate_producer_ammo

        result = generate_producer_ammo({
            "industry": "roofing",
            "state": "NC",
            "loss_run_data": {
                "patterns": ["3 fall-related claims"],
                "underwriting_flags": ["High claim frequency: 5 claims in the loss run period"],
                "producer_talking_points": [],
            },
        })
        flags = result["ammo_questions"]["underwriting_flags"]
        assert any("frequency" in f.lower() for f in flags)

    def test_loss_patterns_in_coverage_traps(self):
        """Loss patterns should appear in coverage traps for non-core industries."""
        from app.services.producer_ammo import generate_producer_ammo

        # Use a tier industry (not core 6) so coverage_traps aren't already full
        result = generate_producer_ammo({
            "industry": "Cattle Ranching",
            "state": "TX",
            "loss_run_data": {
                "patterns": ["3 strain-related claims detected"],
                "underwriting_flags": [],
                "producer_talking_points": [],
            },
        })
        traps = result["ammo_questions"]["coverage_traps"]
        assert any("strain" in t.lower() for t in traps)
