"""Document preprocessing and chunking for RAG."""
from __future__ import annotations

import re
from bs4 import BeautifulSoup

from app.models.ncd import NCD
from app.models.lcd import LCD


class DocumentProcessor:
    """Preprocesses and chunks policies for vector embedding."""
    
    @staticmethod
    def clean_html(raw_html: str | None) -> str:
        """Decode HTML entities, strip tags, and normalize whitespace."""
        if not raw_html:
            return ""
        
        # Parse HTML
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # Get text, separating blocks with a newline
        text = soup.get_text(separator="\n", strip=True)
        
        # Normalize whitespace
        # Convert multiple newlines/spaces into single spaces or structured paragraphs
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def chunk_ncd(ncd: NCD) -> list[dict]:
        """Convert NCD sections into distinct semantic chunks."""
        chunks = []
        
        # Define semantic sections to preserve
        sections = {
            "title": ncd.title,
            "item_service_description": ncd.item_service_description,
            "indications_limitations": ncd.indications_limitations,
            "reasons_for_denial": ncd.reasons_for_denial,
            "cross_reference": ncd.cross_reference,
            "other_text": ncd.other_text,
        }
        
        for section_name, raw_content in sections.items():
            if not raw_content:
                continue
                
            clean_text = DocumentProcessor.clean_html(raw_content)
            if not clean_text:
                continue
                
            paragraphs = clean_text.split('\n\n')
            current_chunk = []
            current_length = 0
            
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                    
                if current_length + len(p) > 1500 and current_chunk:
                    chunks.append({
                        "policy_type": "NCD",
                        "policy_id": ncd.document_id,
                        "policy_version": ncd.document_version,
                        "section": section_name,
                        "chunk_text": " ".join(current_chunk),
                        "metadata": {
                            "title": ncd.title,
                        }
                    })
                    current_chunk = [p]
                    current_length = len(p)
                else:
                    current_chunk.append(p)
                    current_length += len(p)
                    
            if current_chunk:
                chunks.append({
                    "policy_type": "NCD",
                    "policy_id": ncd.document_id,
                    "policy_version": ncd.document_version,
                    "section": section_name,
                    "chunk_text": " ".join(current_chunk),
                    "metadata": {
                        "title": ncd.title,
                    }
                })
                
        return chunks

    @staticmethod
    def chunk_lcd(lcd: LCD) -> list[dict]:
        """Convert LCD sections into distinct semantic chunks."""
        chunks = []
        
        sections = {
            "indication": lcd.indication,
            "diagnoses_support": lcd.diagnoses_support,
            "diagnoses_dont_support": lcd.diagnoses_dont_support,
            "doc_reqs": lcd.doc_reqs,
            "coding_guidelines": lcd.coding_guidelines,
            "cms_cov_policy": lcd.cms_cov_policy,
            "analysis_of_evidence": lcd.analysis_of_evidence,
        }
        
        for section_name, raw_content in sections.items():
            if not raw_content:
                continue
                
            clean_text = DocumentProcessor.clean_html(raw_content)
            if not clean_text:
                continue
                
            paragraphs = clean_text.split('\n\n')
            current_chunk = []
            current_length = 0
            
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                    
                if current_length + len(p) > 1500 and current_chunk:
                    chunks.append({
                        "policy_type": "LCD",
                        "policy_id": lcd.lcd_id,
                        "policy_version": lcd.lcd_version,
                        "section": section_name,
                        "chunk_text": " ".join(current_chunk),
                        "metadata": {
                            "title": lcd.title,
                        }
                    })
                    current_chunk = [p]
                    current_length = len(p)
                else:
                    current_chunk.append(p)
                    current_length += len(p)
                    
            if current_chunk:
                chunks.append({
                    "policy_type": "LCD",
                    "policy_id": lcd.lcd_id,
                    "policy_version": lcd.lcd_version,
                    "section": section_name,
                    "chunk_text": " ".join(current_chunk),
                    "metadata": {
                        "title": lcd.title,
                    }
                })
                
        return chunks
