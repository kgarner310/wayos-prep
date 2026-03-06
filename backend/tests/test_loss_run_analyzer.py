"""Tests for the loss run analyzer service."""
from app.services.loss_run_analyzer import analyze_loss_runs, render_loss_run_text


def test_analyze_empty_entries():
    result = analyze_loss_runs([])
    assert result.get("error") == "No line entries provided"


def test_analyze_single_line_clean():
    entries = [{
        "line_of_business": "Workers Comp",
        "policy_year": "2024",
        "premium": 50000,
        "num_claims": 0,
        "total_incurred": 0,
        "total_paid": 0,
        "open_reserves": 0,
        "large_claims": None,
    }]
    result = analyze_loss_runs(entries)

    assert "totals" in result
    assert result["totals"]["premium"] == 50000
    assert result["totals"]["claims"] == 0
    assert result["totals"]["incurred"] == 0
    assert result["totals"]["loss_ratio"] == 0.0
    assert len(result["line_summaries"]) == 1
    assert result["line_summaries"][0]["line"] == "Workers Comp"

    # Clean record should have a talking point about clean history
    clean_points = [p for p in result["talking_points"] if "clean" in p.lower() or "Clean" in p]
    assert len(clean_points) > 0


def test_analyze_high_loss_ratio():
    entries = [{
        "line_of_business": "GL",
        "policy_year": "2024",
        "premium": 10000,
        "num_claims": 5,
        "total_incurred": 12000,
        "total_paid": 10000,
        "open_reserves": 2000,
        "large_claims": None,
    }]
    result = analyze_loss_runs(entries)

    assert result["totals"]["loss_ratio"] == 1.2
    # Should flag the high loss ratio
    assert any("loss ratio" in f.lower() for f in result["flags"])
    # Overall ratio should be flagged
    assert any("running hot" in f.lower() for f in result["flags"])


def test_analyze_multiple_lines():
    entries = [
        {
            "line_of_business": "WC",
            "policy_year": "2024",
            "premium": 100000,
            "num_claims": 3,
            "total_incurred": 40000,
            "total_paid": 30000,
            "open_reserves": 10000,
        },
        {
            "line_of_business": "Auto",
            "policy_year": "2024",
            "premium": 20000,
            "num_claims": 1,
            "total_incurred": 5000,
            "total_paid": 5000,
            "open_reserves": 0,
        },
        {
            "line_of_business": "Property",
            "policy_year": "2024",
            "premium": 15000,
            "num_claims": 0,
            "total_incurred": 0,
            "total_paid": 0,
            "open_reserves": 0,
        },
    ]
    result = analyze_loss_runs(entries)

    assert result["totals"]["premium"] == 135000
    assert result["totals"]["incurred"] == 45000
    assert result["totals"]["claims"] == 4
    assert len(result["line_summaries"]) == 3

    # Normalized line names
    line_names = [s["line"] for s in result["line_summaries"]]
    assert "Workers Comp" in line_names
    assert "Commercial Auto" in line_names
    assert "Property" in line_names


def test_analyze_large_claims_flagged():
    entries = [{
        "line_of_business": "Workers Comp",
        "policy_year": "2024",
        "premium": 50000,
        "num_claims": 2,
        "total_incurred": 80000,
        "total_paid": 60000,
        "open_reserves": 20000,
        "large_claims": ["Employee fall from scaffold — $75,000"],
    }]
    result = analyze_loss_runs(entries)

    assert len(result["large_claims"]) == 1
    assert any("large" in f.lower() or "notable" in f.lower() for f in result["flags"])


def test_analyze_high_reserves_flagged():
    entries = [{
        "line_of_business": "Workers Comp",
        "policy_year": "2024",
        "premium": 50000,
        "num_claims": 1,
        "total_incurred": 100000,
        "total_paid": 20000,
        "open_reserves": 80000,
    }]
    result = analyze_loss_runs(entries)

    assert any("reserves" in f.lower() for f in result["flags"])


def test_analyze_high_frequency():
    entries = [{
        "line_of_business": "Workers Comp",
        "policy_year": "2024",
        "premium": 50000,
        "num_claims": 15,
        "total_incurred": 20000,
        "total_paid": 15000,
        "open_reserves": 5000,
    }]
    result = analyze_loss_runs(entries)

    assert any("frequency" in f.lower() for f in result["flags"])


def test_normalize_line_names():
    entries = [
        {"line_of_business": "wc", "premium": 10000, "num_claims": 0, "total_incurred": 0},
        {"line_of_business": "gl", "premium": 5000, "num_claims": 0, "total_incurred": 0},
        {"line_of_business": "e&o", "premium": 3000, "num_claims": 0, "total_incurred": 0},
    ]
    result = analyze_loss_runs(entries)
    line_names = [s["line"] for s in result["line_summaries"]]

    assert "Workers Comp" in line_names
    assert "General Liability" in line_names
    assert "Professional Liability" in line_names


def test_render_loss_run_text():
    entries = [{
        "line_of_business": "Workers Comp",
        "policy_year": "2024",
        "premium": 50000,
        "num_claims": 2,
        "total_incurred": 25000,
        "total_paid": 20000,
        "open_reserves": 5000,
    }]
    analysis = analyze_loss_runs(entries)
    text = render_loss_run_text(analysis, "ABC Manufacturing")

    assert "ABC MANUFACTURING" in text
    assert "WAYOS PREP" in text
    assert "$50,000" in text
    assert "BY LINE OF BUSINESS" in text
    assert "Workers Comp" in text


def test_talking_points_always_include_mod_reference():
    entries = [{
        "line_of_business": "Workers Comp",
        "policy_year": "2024",
        "premium": 50000,
        "num_claims": 1,
        "total_incurred": 10000,
        "total_paid": 10000,
        "open_reserves": 0,
    }]
    result = analyze_loss_runs(entries)

    assert any("mod" in p.lower() for p in result["talking_points"])


def test_good_loss_ratio_talking_point():
    entries = [{
        "line_of_business": "Workers Comp",
        "premium": 100000,
        "num_claims": 1,
        "total_incurred": 15000,
        "total_paid": 15000,
        "open_reserves": 0,
    }]
    result = analyze_loss_runs(entries)

    # 15% loss ratio — should mention strong history
    assert any("strong" in p.lower() or "leverage" in p.lower() for p in result["talking_points"])
