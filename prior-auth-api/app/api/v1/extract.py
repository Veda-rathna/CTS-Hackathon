"""PDF Document Extraction endpoint."""
from __future__ import annotations

import io
import re
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/extract", tags=["Document Ingestion"])


class ExtractionResponse(BaseModel):
    """Structured extraction response from PDF PA document."""

    procedure_code: Optional[str] = Field(
        None, description="Extracted CPT/HCPCS procedure code"
    )
    diagnosis_codes: List[str] = Field(
        default_factory=list, description="Extracted ICD-10 diagnosis codes"
    )
    state: Optional[str] = Field(
        None, description="Extracted 2-letter US state code"
    )
    patient_age: Optional[int] = Field(
        None, description="Extracted patient age in years"
    )
    clinical_notes: Optional[str] = Field(
        None, description="Extracted clinical notes / medical documentation"
    )
    confidence: float = Field(
        1.0, description="Extraction confidence score (0.0 - 1.0)"
    )
    missing_fields: List[str] = Field(
        default_factory=list, description="List of required fields that could not be automatically extracted"
    )


US_STATES_MAP = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR", "CALIFORNIA": "CA",
    "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE", "FLORIDA": "FL", "GEORGIA": "GA",
    "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
    "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO",
    "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM", "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH",
    "OKLAHOMA": "OK", "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT",
    "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY"
}


def _extract_text_from_pdf(content: bytes) -> str:
    """Extract raw text from PDF bytes."""
    # Attempt using pypdf / PyPDF2
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception:
        pass

    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        if text.strip():
            return text
    except Exception:
        pass

    # Fallback string extraction for unencrypted text streams
    text_content = []
    for line in content.splitlines():
        printable = "".join(chr(b) for b in line if 32 <= b <= 126 or b in (9, 10, 13))
        if printable.strip():
            text_content.append(printable)
    return "\n".join(text_content)


@router.post(
    "",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Prior Authorization Request fields from PDF",
    description=(
        "Ingests a PDF prior authorization request document and extracts "
        "the procedure code, diagnosis codes, patient state, age, and clinical notes. "
        "Does NOT make coverage decisions — requires human verification before submission."
    ),
)
async def extract_pdf(file: UploadFile = File(...)) -> ExtractionResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid PDF document (.pdf extension).",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded PDF file is empty.",
        )

    raw_text = _extract_text_from_pdf(content)

    # 1. Procedure Code extraction
    procedure_code = None
    proc_match = re.search(r'\b(?:CPT|HCPCS|Procedure|Code)?\s*:?\s*([A-Z0-9]{5})\b', raw_text, re.IGNORECASE)
    if proc_match:
        candidate = proc_match.group(1).upper()
        if re.match(r'^(?:[0-9]{5}|[A-Z][0-9]{4}|[0-9]{4}[A-Z])$', candidate):
            procedure_code = candidate

    if not procedure_code:
        # Secondary search for any isolated 5-digit number or HCPCS code
        cpt_matches = re.findall(r'\b([0-9]{5}|[A-Z][0-9]{4})\b', raw_text)
        if cpt_matches:
            procedure_code = cpt_matches[0]

    # 2. Diagnosis Codes extraction (ICD-10 pattern)
    diagnosis_codes = []
    icd_matches = re.findall(r'\b([A-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?)\b', raw_text)
    for code in icd_matches:
        code_upper = code.upper()
        # Filter out common false positives like CPT/HCPCS codes or state codes
        if not re.match(r'^[A-Z][0-9]{4}$', code_upper) and code_upper not in US_STATES_MAP.values():
            if code_upper not in diagnosis_codes:
                diagnosis_codes.append(code_upper)

    # 3. State extraction
    state = None
    state_match = re.search(r'\bState\s*:?\s*([A-Z]{2})\b', raw_text, re.IGNORECASE)
    if state_match:
        st = state_match.group(1).upper()
        if st in US_STATES_MAP.values():
            state = st

    if not state:
        for full_name, abbrev in US_STATES_MAP.items():
            if re.search(rf'\b{full_name}\b', raw_text, re.IGNORECASE):
                state = abbrev
                break

    # 4. Patient Age extraction
    patient_age = None
    age_match = re.search(r'\bAge\s*:?\s*([0-9]{1,3})\b', raw_text, re.IGNORECASE)
    if age_match:
        try:
            age_val = int(age_match.group(1))
            if 0 <= age_val <= 120:
                patient_age = age_val
        except ValueError:
            pass

    # 5. Clinical notes extraction
    clinical_notes = raw_text.strip() if raw_text.strip() else None

    # Calculate missing fields
    missing = []
    if not procedure_code:
        missing.append("procedure_code")
    if not diagnosis_codes:
        missing.append("diagnosis_codes")
    if not state:
        missing.append("state")

    confidence = 1.0 - (len(missing) * 0.25)
    confidence = max(0.2, min(1.0, confidence))

    return ExtractionResponse(
        procedure_code=procedure_code,
        diagnosis_codes=diagnosis_codes,
        state=state,
        patient_age=patient_age,
        clinical_notes=clinical_notes[:2000] if clinical_notes else None,
        confidence=round(confidence, 2),
        missing_fields=missing,
    )
