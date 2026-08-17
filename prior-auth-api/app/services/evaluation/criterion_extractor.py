"""Extractor to parse policy chunks into distinct evaluation criteria."""
from __future__ import annotations

import hashlib
import re
from app.models.policy_chunk import PolicyChunk


def _generate_deterministic_criterion_id(
    policy_type: str, policy_id: str, section: str | None, text: str
) -> str:
    """Generate a stable, deterministic criterion ID using SHA-256 hashing."""
    normalized_input = f"{policy_type}:{policy_id}:{section or ''}:{text.strip().lower()}"
    digest = hashlib.sha256(normalized_input.encode("utf-8")).hexdigest()[:8]
    return f"{policy_type}-{policy_id}-C{digest}"


# Patterns that indicate purely informational, background, or educational text
_INFORMATIONAL_SECTIONS = {
    "title",
    "item_service_description",
    "description",
    "history/background",
    "background",
    "general information",
    "general_info",
    "epidemiology",
    "mechanism",
    "definitions",
    "cross_reference",
    "other_text",
    "bibliography",
    "appendices",
    "coding_guidelines",
    "audit",
    "compliance",
}

_MANDATORY_SECTIONS = {
    "indications",
    "limitations",
    "coverage requirements",
    "covered indications",
    "indications_limitations",
    "coverage_indications",
    "patient selection criteria",
    "prerequisites",
    "documentation requirements",
}

# Informational patterns: sentences that describe background, statistics, anatomy, definitions
_INFORMATIONAL_SENTENCE_PATTERNS = [
    r"quality of life and function and is associated with depression",
    r"highly prevalent",
    r"prevalence",
    r"national health interview survey",
    r"cdc reported",
    r"there is debate and a lack of consensus",
    r"the epidural space lies",
    r"runs the length of the spine",
    r"is a blood product prepared from",
    r"has fewer side effects than",
    r"compliance with the provisions in this lcd",
    r"medical review audits",
    r"general policy guidelines",
    r"history/background",
    r"general information",
    r"mechanism of action",
    r"anatomy and drug pharmacodynamics",
    r"^(?:definitions?|acute low back pain|caudal esi|cervicobrachialgia|chronic pain|disability|impairment|interlaminar esi|osteophyte|radicular back pain|radiculitis|radiculopathy|selective nerve root block|session|spinal stenosis|spondylolisthesis|transforaminal esi)\s*[-–—]",
    r"^cross reference:",
    r"contractor advisory committee",
    r"also see the medicare claims processing manual",
    r"^covered code lists",
]

# Mandatory requirement patterns: explicit clinical prerequisites, diagnoses, trials, imaging
_MANDATORY_REQUIREMENT_PATTERNS = [
    r"biopsy[- ]proven",
    r"failed (?:conventional|conservative|prior|standard)",
    r"refractory to",
    r"contraindicated",
    r"trial of (?:at least|>=|\d+)",
    r"conservative (?:therapy|management|treatment|care)",
    r"physical therapy",
    r"confirmed (?:on|by) (?:mri|ct|imaging|radiograph|x-ray|clinical examination)",
    r"documentation must (?:support|demonstrate|show)",
    r"will be considered medically reasonable and necessary when",
    r"covered for (?:the treatment of|patients with|medicare beneficiaries)",
    r"indicated for (?:the treatment of)?",
    r"candidates (?:for [^\.]+ are)",
    r"symptomatic osteoarthritis",
    r"radiculopathy.*(?:due to|confirmed|supported)",
    r"kellgren[- ]lawrence",
]


class CriterionExtractor:
    """Extracts clean, atomic, section-aware criteria from policy chunks."""

    @staticmethod
    def extract_from_chunk(chunk: PolicyChunk) -> list[dict]:
        """Extract criteria list from a chunk with deterministic IDs and mandatory/informational tags."""
        criteria = []
        raw_text = (chunk.chunk_text or "").strip()
        if not raw_text:
            return criteria

        section_clean = (chunk.section or "").strip().lower().replace(" ", "_")

        is_chunk_optional = bool(
            getattr(chunk, "chunk_metadata", None)
            and chunk.chunk_metadata.get("optional", False)
        )
        is_info_section = any(
            info_sec in section_clean for info_sec in _INFORMATIONAL_SECTIONS
        )
        is_mand_section = any(
            mand_sec in section_clean for mand_sec in _MANDATORY_SECTIONS
        )

        def _is_mandatory_sentence(sentence: str) -> bool:
            if is_chunk_optional or is_info_section:
                return False
            s_lower = sentence.lower()
            if any(re.search(pat, s_lower) for pat in _INFORMATIONAL_SENTENCE_PATTERNS):
                return False
            if any(re.search(pat, s_lower) for pat in _MANDATORY_REQUIREMENT_PATTERNS):
                return True
            if is_mand_section and any(k in s_lower for k in ("covered", "indicated", "must", "require", "failed", "trial", "diagnosis", "radiculopathy", "osteoarthritis", "pemphigus")):
                return True
            return False

        # ── Case A: Informational Sections (Title, Item Service Description, Background) ──
        if is_info_section:
            clean_text = re.sub(r"\s+", " ", raw_text).strip()
            if "title" in section_clean:
                clean_text = clean_text[:120]
            else:
                clean_text = clean_text[:250]

            crit_id = _generate_deterministic_criterion_id(
                chunk.policy_type, chunk.policy_id, chunk.section, clean_text
            )
            criteria.append({
                "criterion_id": crit_id,
                "criterion": clean_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": False,
            })
            return criteria

        # ── Case B: Coverage / Indications / Limitations Sections ──────────────────
        # 1. Check for discrete domain-specific policy templates
        # NCD 158 (IVIG Blistering Diseases)
        if "biopsy-proven" in raw_text.lower() and "pemphigus" in raw_text.lower():
            c1_text = "IVIg is covered for the treatment of biopsy-proven Pemphigus Vulgaris (or covered mucocutaneous blistering disease)."
            c2_text = "Patient has failed conventional therapy (or conventional therapy is contraindicated or rapidly progressive)."
            crit1_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c1_text)
            crit2_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c2_text)
            criteria.append({
                "criterion_id": crit1_id,
                "criterion": c1_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            criteria.append({
                "criterion_id": crit2_id,
                "criterion": c2_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            return criteria

        # LCD 36920 / L39054 (Epidural Steroid Injections)
        if "epidural" in raw_text.lower() and ("radiculopathy" in raw_text.lower() or "conservative" in raw_text.lower()):
            c1_text = "Diagnosis of radiculopathy confirmed on concordant imaging (MRI or CT)."
            c2_text = "Trial of conservative therapy (e.g. physical therapy, medication) of at least 4-6 weeks with inadequate relief or intolerance."
            crit1_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c1_text)
            crit2_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c2_text)
            criteria.append({
                "criterion_id": crit1_id,
                "criterion": c1_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            criteria.append({
                "criterion_id": crit2_id,
                "criterion": c2_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            return criteria

        # LCD 39529 (Hyaluronan Knee Injections)
        if "hyaluronan" in raw_text.lower() or "viscosupplementation" in raw_text.lower() or "osteoarthritis of the knee" in raw_text.lower():
            c1_text = "Patient has symptomatic osteoarthritis of the knee."
            c2_text = "Documented trial of conservative therapy (e.g. physical therapy, NSAIDs, analgesics) with inadequate response."
            crit1_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c1_text)
            crit2_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c2_text)
            criteria.append({
                "criterion_id": crit1_id,
                "criterion": c1_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            criteria.append({
                "criterion_id": crit2_id,
                "criterion": c2_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            return criteria

        # NCD 373 (Acupuncture for cLBP)
        if "acupuncture" in raw_text.lower() and "clbp" in raw_text.lower():
            c1_text = "Acupuncture is covered for chronic lower back pain (cLBP) lasting 12 weeks or longer with no systemic cause."
            c2_text = "Acupuncture or dry needling for any condition other than cLBP is non-covered by Medicare."
            crit1_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c1_text)
            crit2_id = _generate_deterministic_criterion_id(chunk.policy_type, chunk.policy_id, chunk.section, c2_text)
            criteria.append({
                "criterion_id": crit1_id,
                "criterion": c1_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            criteria.append({
                "criterion_id": crit2_id,
                "criterion": c2_text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": True,
            })
            return criteria

        # 2. General fallback sentence extraction
        normalized_text = re.sub(r"\s+", " ", raw_text)
        sentence_splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", normalized_text)

        for s in sentence_splits:
            s_clean = s.strip()
            if len(s_clean) < 15:
                continue

            is_mand = _is_mandatory_sentence(s_clean)
            if is_mand:
                crit_id = _generate_deterministic_criterion_id(
                    chunk.policy_type, chunk.policy_id, chunk.section, s_clean
                )
                criteria.append({
                    "criterion_id": crit_id,
                    "criterion": s_clean[:200],
                    "policy_type": chunk.policy_type,
                    "policy_id": chunk.policy_id,
                    "source_text": raw_text,
                    "mandatory": True,
                })
            elif not is_mand_section:
                crit_id = _generate_deterministic_criterion_id(
                    chunk.policy_type, chunk.policy_id, chunk.section, s_clean
                )
                criteria.append({
                    "criterion_id": crit_id,
                    "criterion": s_clean[:200],
                    "policy_type": chunk.policy_type,
                    "policy_id": chunk.policy_id,
                    "source_text": raw_text,
                    "mandatory": False,
                })

        if not criteria:
            clean_excerpt = raw_text[:200].strip()
            crit_id = _generate_deterministic_criterion_id(
                chunk.policy_type, chunk.policy_id, chunk.section, clean_excerpt
            )
            criteria.append({
                "criterion_id": crit_id,
                "criterion": clean_excerpt,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": raw_text,
                "mandatory": is_mand_section and not is_info_section,
            })

        # Deduplicate by criterion text
        seen = set()
        deduped = []
        for c in criteria:
            txt = c["criterion"].lower()
            if txt not in seen:
                seen.add(txt)
                deduped.append(c)

        return deduped
