"""QuickCapture — lightweight ingestion for screenshots, PDFs, and plain text.

Extracts insurance-relevant signals (carrier, premium, coverage, etc.)
from uploaded content. Uses pytesseract for OCR when available, falls
back to raw text extraction.
"""

import io
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Carrier names we know about — expand as needed
KNOWN_CARRIERS = [
    "Travelers", "Cincinnati", "Liberty Mutual", "Hartford", "Zurich",
    "Chubb", "CNA", "Hanover", "Employers", "BHHC", "Berkshire Hathaway",
    "State Auto", "Westfield", "Erie", "Selective", "Markel", "AMERITAS",
    "Nationwide", "Auto-Owners", "Grinnell", "Great American",
    "Philadelphia", "Tokio Marine", "Arch", "RLI", "Frankenmuth",
]

# Policy type keywords
POLICY_TYPE_KEYWORDS = {
    "workers compensation": "Workers Compensation",
    "workers comp": "Workers Compensation",
    "work comp": "Workers Compensation",
    "wc": "Workers Compensation",
    "general liability": "General Liability",
    "gl": "General Liability",
    "commercial auto": "Commercial Auto",
    "auto liability": "Commercial Auto",
    "commercial property": "Commercial Property",
    "property": "Commercial Property",
    "umbrella": "Umbrella/Excess",
    "excess": "Umbrella/Excess",
    "professional liability": "Professional Liability",
    "e&o": "Professional Liability",
    "errors and omissions": "Professional Liability",
    "d&o": "Directors & Officers",
    "epli": "EPLI",
    "employment practices": "EPLI",
    "cyber": "Cyber Liability",
    "inland marine": "Inland Marine",
    "bop": "Business Owners Policy",
    "business owners": "Business Owners Policy",
}


def detect_file_type(filename: str, content_type: Optional[str] = None) -> str:
    """Detect file type from filename or content type."""
    name_lower = (filename or "").lower()
    if name_lower.endswith(".pdf"):
        return "pdf"
    if name_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
        return "image"
    if name_lower.endswith((".txt", ".csv")):
        return "text"
    # Fall back to content type
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return "pdf"
    if "image" in ct:
        return "image"
    return "text"


def extract_text_from_image(file_bytes: bytes) -> str:
    """Run OCR on image bytes. Falls back to empty string if pytesseract unavailable."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img)
    except ImportError:
        logger.warning("pytesseract or PIL not installed — OCR unavailable")
        return ""
    except Exception as e:
        logger.error("OCR extraction failed: %s", e)
        return ""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes. Falls back to empty string."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            return "\n".join(pages)
    except ImportError:
        logger.warning("pdfplumber not installed — PDF text extraction unavailable")
        return ""
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        return ""


def parse_insurance_signals(text: str) -> dict:
    """Parse common insurance signals from raw text.

    Returns dict with keys: carrier, premium, coverage, coverage_limit,
    mod, employee_count. Missing values are None.
    """
    signals: dict = {}
    if not text:
        return signals

    text_lower = text.lower()

    # Carrier detection
    for carrier in KNOWN_CARRIERS:
        if carrier.lower() in text_lower:
            signals["carrier"] = carrier
            break

    # Premium detection — look for dollar amounts
    premium_patterns = [
        r"(?:premium|total\s+premium|annual\s+premium)[:\s]*\$?([\d,]+(?:\.\d{2})?)",
        r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:premium|annual)",
    ]
    for pattern in premium_patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                signals["premium"] = int(float(m.group(1).replace(",", "")))
            except (ValueError, IndexError):
                pass
            break

    # Coverage / policy type detection
    for keyword, coverage_type in POLICY_TYPE_KEYWORDS.items():
        if keyword in text_lower:
            signals["coverage"] = coverage_type
            break

    # Coverage limit
    limit_patterns = [
        r"(?:limit|coverage\s+limit|each\s+occurrence)[:\s]*\$?([\d,]+(?:\.\d{2})?)",
        r"\$\s*([\d,]+(?:\.\d{2})?)\s*/\s*\$?\s*[\d,]+",
    ]
    for pattern in limit_patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                val = int(float(m.group(1).replace(",", "")))
                if val >= 10000:  # Filter out small numbers that aren't limits
                    signals["coverage_limit"] = val
            except (ValueError, IndexError):
                pass
            break

    # Experience mod
    mod_patterns = [
        r"(?:experience\s+mod|mod\s+rate|e-mod|emod)[:\s]*([\d]+\.[\d]+)",
        r"([\d]+\.[\d]+)\s*(?:experience\s+mod|mod\s+rate|e-mod)",
    ]
    for pattern in mod_patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                mod_val = float(m.group(1))
                if 0.3 <= mod_val <= 3.0:  # Reasonable mod range
                    signals["mod"] = mod_val
            except (ValueError, IndexError):
                pass
            break

    # Employee count
    emp_patterns = [
        r"(?:employee|employees|employee\s+count|headcount|full[\s-]time)[:\s]*(\d+)",
        r"(\d+)\s*(?:employees|full[\s-]time\s+employees)",
    ]
    for pattern in emp_patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                count = int(m.group(1))
                if 1 <= count <= 100000:
                    signals["employee_count"] = count
            except (ValueError, IndexError):
                pass
            break

    return signals


def process_capture(
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    plain_text: Optional[str] = None,
) -> dict:
    """Process a capture input (file upload or plain text).

    Returns:
        {
            "source_type": "image"|"pdf"|"text",
            "extracted_text": str,
            "signals": {...},
        }
    """
    if plain_text:
        extracted = plain_text
        source_type = "text"
    elif file_bytes:
        source_type = detect_file_type(filename, content_type)
        if source_type == "image":
            extracted = extract_text_from_image(file_bytes)
        elif source_type == "pdf":
            extracted = extract_text_from_pdf(file_bytes)
        else:
            extracted = file_bytes.decode("utf-8", errors="replace")
    else:
        return {"source_type": "text", "extracted_text": "", "signals": {}}

    signals = parse_insurance_signals(extracted)

    return {
        "source_type": source_type,
        "extracted_text": extracted,
        "signals": signals,
    }
