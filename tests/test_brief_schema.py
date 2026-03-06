"""Tests for brief schema validation."""

from app.schemas.schemas import BriefOutput


def test_valid_brief():
    data = {
        "industry": "roofing",
        "state": "NC",
        "employee_count": 22,
        "current_mod": 1.15,
        "top_loss_drivers": [
            {
                "title": "Falls from height",
                "why_it_matters": "Leading cause of death for roofers",
                "confidence": "high",
                "source_ids": ["abc-123"],
            }
        ],
        "coverage_blind_spots": [
            {
                "title": "Inland marine",
                "why_it_matters": "Tools and equipment on job sites need coverage",
                "source_ids": ["abc-123"],
            }
        ],
        "questions_to_ask": [
            {
                "question": "Do you use subcontractors?",
                "purpose": "Assess risk transfer",
                "source_ids": [],
            }
        ],
        "watchouts": [
            {
                "note": "High mod may limit carrier options",
                "source_ids": ["abc-123"],
            }
        ],
        "confidence_notes": [
            {
                "note": "Strong source coverage for NC roofing",
                "severity": "info",
            }
        ],
        "citation_map": [
            {
                "source_id": "abc-123",
                "title": "Roofing Safety Guide",
                "url": None,
            }
        ],
    }

    brief = BriefOutput(**data)
    assert brief.industry == "roofing"
    assert brief.state == "NC"
    assert len(brief.top_loss_drivers) == 1
    assert brief.top_loss_drivers[0].confidence == "high"


def test_minimal_brief():
    data = {
        "industry": "trucking",
        "state": "GA",
    }
    brief = BriefOutput(**data)
    assert brief.industry == "trucking"
    assert brief.top_loss_drivers == []
    assert brief.employee_count == 0


def test_brief_with_all_sections():
    data = {
        "industry": "manufacturing",
        "state": "NC",
        "employee_count": 50,
        "current_mod": 0.95,
        "top_loss_drivers": [
            {"title": "Machine guarding", "why_it_matters": "OSHA violations", "confidence": "high", "source_ids": ["s1"]},
            {"title": "Ergonomic injuries", "why_it_matters": "Repetitive motion", "confidence": "medium", "source_ids": ["s2"]},
        ],
        "coverage_blind_spots": [
            {"title": "Cyber liability", "why_it_matters": "CNC equipment connected to internet", "source_ids": ["s2"]},
        ],
        "questions_to_ask": [
            {"question": "What is your LOTO program?", "purpose": "Machine safety compliance", "source_ids": ["s1"]},
            {"question": "Do you have temp workers?", "purpose": "WC coverage gaps", "source_ids": []},
        ],
        "watchouts": [
            {"note": "EPA compliance for manufacturing waste", "source_ids": ["s1"]},
        ],
        "confidence_notes": [
            {"note": "Good source coverage", "severity": "info"},
        ],
        "citation_map": [
            {"source_id": "s1", "title": "Manufacturing Safety Guide", "url": None},
            {"source_id": "s2", "title": "Industrial Risk Report", "url": "https://example.com"},
        ],
    }

    brief = BriefOutput(**data)
    assert len(brief.top_loss_drivers) == 2
    assert len(brief.questions_to_ask) == 2
    assert brief.citation_map[1].url == "https://example.com"
