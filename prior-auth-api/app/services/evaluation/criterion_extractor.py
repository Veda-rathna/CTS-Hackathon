"""Extractor to parse policy chunks into distinct evaluation criteria."""
from __future__ import annotations

import re
import uuid
from app.models.policy_chunk import PolicyChunk


class CriterionExtractor:
    """Extracts criteria from unstructured policy text."""

    @staticmethod
    def extract_from_chunk(chunk: PolicyChunk) -> list[dict]:
        """
        Extract criteria list from a chunk. 
        Returns a list of dicts suitable for PolicyCriterion creation.
        """
        criteria = []
        text = chunk.chunk_text
        
        # Very simple heuristic: extract bullet points or sentences that denote rules.
        # In a real-world scenario, you might use a lightweight NLP model or regex.
        
        # Find bullet points
        bullets = re.findall(r'(?:^|\n)(?:[-*•]|\d+\.)\s+(.+)', text)
        
        if bullets:
            for b in bullets:
                b_clean = b.strip()
                if b_clean:
                    criteria.append({
                        "criterion_id": f"{chunk.policy_type}-{chunk.policy_id}-C{uuid.uuid4().hex[:6]}",
                        "criterion": b_clean,
                        "policy_type": chunk.policy_type,
                        "policy_id": chunk.policy_id,
                        "source_text": chunk.chunk_text,
                    })
        
        # Also look for explicit requirement phrases
        req_phrases = [
            r'documentation must (?:support|demonstrate|show) ([^\.]+)',
            r'patient has (?:a|an)? ([^\.]+)',
            r'must have (?:failed|tried) ([^\.]+)',
            r'is covered for ([^\.]+)'
        ]
        
        for phrase in req_phrases:
            matches = re.finditer(phrase, text, re.IGNORECASE)
            for m in matches:
                req_text = m.group(0).strip()
                if req_text:
                    criteria.append({
                        "criterion_id": f"{chunk.policy_type}-{chunk.policy_id}-C{uuid.uuid4().hex[:6]}",
                        "criterion": req_text,
                        "policy_type": chunk.policy_type,
                        "policy_id": chunk.policy_id,
                        "source_text": chunk.chunk_text,
                    })
        
        # If no explicit bullets or phrases found, fallback to the chunk as a whole if it's short,
        # or split into sentences.
        if not criteria and len(text) < 500:
            criteria.append({
                "criterion_id": f"{chunk.policy_type}-{chunk.policy_id}-C{uuid.uuid4().hex[:6]}",
                "criterion": text,
                "policy_type": chunk.policy_type,
                "policy_id": chunk.policy_id,
                "source_text": chunk.chunk_text,
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
