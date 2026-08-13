"""Chunking service — normalizes and chunks policy text for embedding.

Pipeline:
    CMS raw policy text (from DB)
      → Normalize (strip artifacts, standardize whitespace)
      → Preserve section identity (tagged by section_type)
      → Chunk by semantic section boundaries
      → Attach metadata (policy_type, policy_id, version, section, dates)
      → Ready for embedding

This service does NOT do arbitrary character splitting.  NCD and LCD
models already have natural section boundaries (indication, doc_reqs,
indications_limitations, etc.) that align with the chunking strategy.
"""
from __future__ import annotations

import hashlib
import logging
import re

from app.schemas.evaluation import PolicySection

logger = logging.getLogger(__name__)

# Maximum characters per chunk — sections exceeding this are split at
# paragraph boundaries.  This is generous because policy sections are
# typically well-structured.
MAX_CHUNK_CHARS = 2000


class ChunkingService:
    """Normalizes and chunks PolicySection objects for embedding."""

    def chunk_sections(self, sections: list[PolicySection]) -> list[PolicyChunk]:
        """Normalize and chunk a list of PolicySections.

        Returns a list of ``PolicyChunk`` objects, each with a unique
        ``chunk_id`` and the original section metadata preserved.
        """
        chunks: list[PolicyChunk] = []
        for section in sections:
            normalized = self._normalize(section.content)
            if not normalized:
                continue

            if len(normalized) <= MAX_CHUNK_CHARS:
                chunks.append(self._make_chunk(section, normalized, chunk_index=0))
            else:
                # Split long sections at paragraph boundaries
                paragraphs = self._split_paragraphs(normalized)
                current_text = ""
                chunk_index = 0

                for para in paragraphs:
                    if len(current_text) + len(para) + 2 > MAX_CHUNK_CHARS and current_text:
                        chunks.append(self._make_chunk(section, current_text.strip(), chunk_index))
                        chunk_index += 1
                        current_text = ""
                    current_text += para + "\n\n"

                if current_text.strip():
                    chunks.append(self._make_chunk(section, current_text.strip(), chunk_index))

        logger.debug("Chunked %d sections into %d chunks", len(sections), len(chunks))
        return chunks

    def _normalize(self, text: str) -> str:
        """Clean raw policy text for embedding.

        - Strip HTML artifacts and formatting noise
        - Remove boilerplate headers/footers
        - Standardize whitespace
        - Preserve meaningful section structure
        """
        if not text:
            return ""

        result = text

        # Strip common HTML tags that leak from CMS data
        result = re.sub(r"<[^>]+>", " ", result)

        # Remove excessive whitespace while preserving paragraph breaks
        result = re.sub(r"[ \t]+", " ", result)
        result = re.sub(r"\n{3,}", "\n\n", result)

        # Remove common CMS boilerplate patterns
        result = re.sub(
            r"(?i)(?:group\s+\d+\s+paragraph\s+\w+|"
            r"this\s+LCD\s+was\s+developed\s+based\s+on|"
            r"^\s*N/A\s*$)",
            "",
            result,
        )

        return result.strip()

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs at double-newline boundaries."""
        paragraphs = re.split(r"\n\n+", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _make_chunk(
        self, section: PolicySection, text: str, chunk_index: int,
    ) -> "PolicyChunk":
        """Create a PolicyChunk with a deterministic chunk_id."""
        raw_id = f"{section.policy_type}_{section.policy_id}_{section.section_type}_{chunk_index}"
        chunk_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]

        return PolicyChunk(
            chunk_id=chunk_id,
            policy_type=section.policy_type,
            policy_id=section.policy_id,
            policy_version=section.policy_version,
            section_type=section.section_type,
            content=text,
            effective_date=section.effective_date,
            end_date=section.end_date,
            jurisdiction_id=section.jurisdiction_id,
            contractor_id=section.contractor_id,
        )


class PolicyChunk:
    """A single chunk of normalized policy text, ready for embedding.

    Carries all metadata needed to store in ``policy_embeddings`` table
    and to reconstruct provenance in ``CriterionSource``.
    """

    __slots__ = (
        "chunk_id",
        "policy_type",
        "policy_id",
        "policy_version",
        "section_type",
        "content",
        "effective_date",
        "end_date",
        "jurisdiction_id",
        "contractor_id",
    )

    def __init__(
        self,
        chunk_id: str,
        policy_type: str,
        policy_id: str,
        policy_version: str | None,
        section_type: str,
        content: str,
        effective_date=None,
        end_date=None,
        jurisdiction_id: str | None = None,
        contractor_id: str | None = None,
    ) -> None:
        self.chunk_id = chunk_id
        self.policy_type = policy_type
        self.policy_id = policy_id
        self.policy_version = policy_version
        self.section_type = section_type
        self.content = content
        self.effective_date = effective_date
        self.end_date = end_date
        self.jurisdiction_id = jurisdiction_id
        self.contractor_id = contractor_id

    def __repr__(self) -> str:
        return (
            f"<PolicyChunk(id={self.chunk_id!r}, "
            f"{self.policy_type}/{self.policy_id}/{self.section_type})>"
        )
