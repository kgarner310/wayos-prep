"""Seed demo data for WAYOS PREP.

Run: python seed_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.models import Source
from app.services.ingestion import ingest_raw_text
from app.services.parser import clean_text
from app.services.chunker import chunk_text
from app.services.tagging import tag_source, tag_chunk
from app.models.models import SourceChunk
from app.core.enums import SourceStatus

SAMPLE_SOURCES = [
    {
        "title": "Roofing Contractor Risk Guide: Workers Comp and Safety",
        "source_type": "trade_publication",
        "authority_level": "trade_association",
        "jurisdiction_state": "nc",
        "published_at": datetime(2025, 8, 15, tzinfo=timezone.utc),
        "publisher": "National Roofing Contractors Association",
        "raw_text": """# Roofing Contractor Risk Guide

## Falls From Height: The #1 Loss Driver

Falls from height remain the leading cause of death and serious injury in the roofing industry. OSHA reports that falls account for approximately 33% of all construction fatalities, with roofers facing the highest rate of fatal falls among all construction trades.

### Key Statistics
- The average workers compensation claim for a roofing fall exceeds $100,000
- Lost-time claim frequency for roofing contractors is 3-5x higher than general construction
- Residential re-roofing operations carry higher fall risk due to steep-slope work

### Risk Mitigation
- Fall protection plans are required for work above 6 feet (OSHA 29 CFR 1926.501)
- Personal fall arrest systems, guardrails, or safety nets must be used
- Regular toolbox talks on fall prevention reduce claim frequency by 40-60%

## Subcontractor Management

Many roofing contractors rely heavily on subcontractors, creating significant risk transfer challenges:
- Certificate of insurance tracking is often inconsistent
- Subcontractor workers comp coverage gaps can create employer liability for the general contractor
- Improper classification of 1099 workers vs employees is a common audit finding
- NC requires all subcontractors with 3+ employees to carry workers comp

## Experience Modification Rate

Roofing contractors typically carry experience mods above 1.0 due to high claim frequency. Key factors:
- High-severity fall claims dramatically impact the mod for 3 years
- Frequency of small claims (cuts, strains) also drives mod increases
- A mod above 1.25 signals poor loss history and may limit carrier options

## Workers Compensation in North Carolina

North Carolina is a competitive workers comp state with key considerations:
- The NC Rate Bureau sets advisory rates for roofing class codes
- Class code 5551 (roofing) carries some of the highest WC rates in the state
- NC requires workers comp for employers with 3+ employees
- The NC Industrial Commission administers claims and disputes

## Commercial Auto Exposure

Roofing contractors operate trucks, trailers, and material delivery vehicles:
- Fleet accidents are the second-largest loss driver after falls
- Hired and non-owned auto coverage is critical for contractors using personal vehicles
- Material delivery from supplier to job site creates auto liability exposure
- Driver MVR reviews should be conducted annually

## Coverage Gaps to Watch

Common coverage blind spots for roofing contractors include:
- Inland marine coverage for tools and equipment on job sites
- Builders risk coverage during active construction
- Completed operations exposure (leaks discovered after job completion)
- Pollution liability for tear-off debris and disposal
- Umbrella coverage may be required by general contractors
""",
    },
    {
        "title": "Trucking Industry Loss Trends and Fleet Risk Management",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": None,
        "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
        "publisher": "National Insurance Risk Council",
        "raw_text": """# Trucking Industry Loss Trends 2025

## Fleet Accidents: Primary Loss Driver

Motor vehicle accidents remain the dominant loss driver for trucking operations:
- Average commercial auto liability claim exceeds $150,000
- Nuclear verdicts (jury awards exceeding $10 million) have increased 300% since 2015
- Distracted driving and driver fatigue are the leading accident causes
- DOT compliance violations correlate strongly with accident frequency

### Driver Turnover Crisis

The trucking industry faces chronic driver turnover exceeding 90% annually for large carriers:
- New/inexperienced drivers are 3x more likely to be involved in preventable accidents
- Driver recruitment pressure leads to relaxed hiring standards
- CDL training quality varies dramatically across programs
- Driver retention programs reduce accident frequency by 25-35%

## Workers Compensation for Trucking

Despite drivers spending most time on the road, workers comp claims remain significant:
- Loading/unloading injuries account for 40% of trucker WC claims
- Slips, trips, and falls at delivery locations are common
- Cumulative trauma injuries (back, neck, shoulder) from prolonged driving
- Multi-state operations complicate workers comp jurisdiction and filing

## Coverage Considerations

### Commercial Auto
- Primary liability limits of $1 million are standard; many shippers require $2-5 million
- Motor cargo coverage protects against damage to freight
- Trailer interchange agreements need specific coverage endorsement
- Non-owned trailer physical damage often overlooked

### General Liability
- Premises liability at terminal locations
- Completed operations for freight brokers
- Contractual liability for shipper agreements

### Umbrella/Excess
- Nuclear verdict exposure makes high umbrella limits essential
- $5-10 million umbrella limits are increasingly standard
- Some carriers pulling back from trucking umbrella market

## Regulatory Compliance

- FMCSA CSA scores directly impact insurance pricing
- ELD mandate compliance is now table stakes
- Drug and alcohol testing program (DOT requirements)
- Annual driver qualification file maintenance required
- Hours of service violations are a leading citation

## Fleet Management Best Practices

- Implement dash cameras (front and driver-facing)
- Monthly driver scorecard programs
- Pre-trip and post-trip inspection protocols
- Preventive maintenance scheduling reduces breakdowns and accidents
- Speed governor implementation for governed fleets
""",
    },
    {
        "title": "Manufacturing Safety: Machine Guarding and Workers Comp",
        "source_type": "article",
        "authority_level": "standards_body",
        "jurisdiction_state": "nc",
        "published_at": datetime(2025, 10, 1, tzinfo=timezone.utc),
        "publisher": "Manufacturing Safety Alliance",
        "raw_text": """# Manufacturing Safety: Essential Risk Controls

## Machine Guarding: Critical Exposure

Machine guarding violations remain OSHA's most frequently cited standard in manufacturing:
- OSHA Standard 1910.212 requires point-of-operation guards on all machines
- Amputations and crush injuries from unguarded machinery result in severe WC claims
- Average machine guarding injury claim exceeds $75,000 in workers comp costs
- Lockout/tagout (LOTO) compliance is essential during maintenance operations

### Common Machine Guarding Issues
- Missing or bypassed safety guards on presses, saws, and conveyors
- Inadequate lockout/tagout procedures during maintenance
- Failure to train employees on energy control procedures
- Emergency stop buttons not properly positioned or maintained

## Combustible Dust Hazard

Manufacturing operations that generate combustible dust face explosion risk:
- Wood, metal, plastic, and grain dusts can create explosive atmospheres
- OSHA's National Emphasis Program targets combustible dust hazards
- Dust collection systems require regular inspection and maintenance
- Housekeeping programs are the first line of defense

## Ergonomic and Repetitive Motion Injuries

- Repetitive motion injuries account for 30% of manufacturing WC claims
- Material handling (lifting, carrying, pushing) drives musculoskeletal injuries
- Assembly line work creates cumulative trauma disorder exposure
- Ergonomic assessments and job rotation programs reduce injury rates

## Workers Compensation Considerations

- Manufacturing class codes vary widely by specific operation
- NC class code 3632 (machine shops) has moderate WC rates
- Payroll verification and proper employee classification are critical
- Experience mod management through return-to-work programs
- Safety committee programs can qualify for NC premium discounts

## General Liability Exposure

- Products liability for manufactured goods
- Completed operations for custom fabrication
- Recall expense coverage increasingly important
- Contractual liability for OEM supply agreements

## Property and Equipment

- Equipment breakdown coverage (boiler and machinery)
- Business interruption from supply chain disruptions
- Inland marine for goods in transit
- Cyber liability for CNC and IoT-connected equipment
- Property valuation must account for specialized machinery

## Regulatory Environment

- OSHA general industry standards (29 CFR 1910) apply
- EPA environmental compliance for manufacturing waste
- State-specific regulations may impose additional requirements
- NC OSHA (administered by NC DOL) conducts inspections
- Violation penalties have increased significantly in recent years

## Subcontractor and Temporary Worker Risk

- Temporary staffing agencies create workers comp exposure questions
- Borrowed servant doctrine may apply in NC
- Certificate tracking for maintenance subcontractors
- Multi-employer worksite responsibilities under OSHA
""",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Source).count()
        if existing > 0:
            print(f"Database already has {existing} sources. Skipping seed.")
            return

        print("Seeding demo data...")
        for data in SAMPLE_SOURCES:
            data = dict(data)  # copy to avoid mutating the original
            raw_text = data.pop("raw_text")
            source = ingest_raw_text(db=db, raw_text=raw_text, **data)
            print(f"  Created source: {source.title} ({source.id})")

            # Parse
            source.raw_text = clean_text(source.raw_text)
            source.status = SourceStatus.PARSED
            tag_source(db, source)
            db.commit()
            print(f"    Parsed and tagged")

            # Chunk
            chunks_data = chunk_text(
                source.raw_text,
                source_jurisdiction=source.jurisdiction,
                source_jurisdiction_state=source.jurisdiction_state,
                authority_score=float(source.authority_score),
                freshness_score=float(source.freshness_score),
            )
            for cd in chunks_data:
                chunk = SourceChunk(
                    source_id=source.id,
                    chunk_index=cd["chunk_index"],
                    heading=cd.get("heading"),
                    text_content=cd["text_content"],
                    token_count=cd["token_count"],
                    char_count=cd["char_count"],
                    chunk_hash=cd["chunk_hash"],
                    jurisdiction=cd.get("jurisdiction"),
                    jurisdiction_state=cd.get("jurisdiction_state"),
                    authority_score=cd["authority_score"],
                    freshness_score=cd["freshness_score"],
                )
                db.add(chunk)
                db.flush()
                tag_chunk(db, chunk)

            source.status = SourceStatus.CHUNKED
            db.commit()
            print(f"    Created {len(chunks_data)} chunks")

            # Embed (only if API key is available)
            try:
                from app.services.embeddings import embed_chunks
                chunks = db.query(SourceChunk).filter(SourceChunk.source_id == source.id).all()
                count = embed_chunks(db, chunks)
                if count > 0:
                    source.status = SourceStatus.READY
                    db.commit()
                    print(f"    Embedded {count} chunks - source is READY")
                else:
                    # Mark as ready anyway for demo purposes (tag-based retrieval will work)
                    source.status = SourceStatus.READY
                    db.commit()
                    print(f"    No API key for embeddings - marked READY for tag-based retrieval")
            except Exception as e:
                source.status = SourceStatus.READY
                db.commit()
                print(f"    Embedding skipped ({e}) - marked READY for tag-based retrieval")

        print(f"\nSeed complete. {len(SAMPLE_SOURCES)} sources created.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
