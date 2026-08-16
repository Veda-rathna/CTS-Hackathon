import hashlib
import json
from datetime import date, datetime
from typing import Any, Dict

from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered, LCDIcd10NonCovered
from app.models.article import Article, ArticleHcpcsCode, ArticleIcd10Covered, ArticleIcd10NonCovered
from app.models.ncd import NCD, NCDHCPCSCode

class CMSNormalizer:
    @staticmethod
    def _parse_date(date_str: str | None) -> date | None:
        if not date_str:
            return None
        try:
            return date.fromisoformat(date_str.split("T")[0])
        except ValueError:
            return None

    @staticmethod
    def _parse_datetime(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        # Sort keys to ensure deterministic hashing
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def normalize_lcd(cms_item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize an LCD document."""
        # Some LCDs are returned with 'lcd_id', others might use 'id'
        lcd_id_raw = cms_item.get("lcd_id") or cms_item.get("lcdId") or str(cms_item.get("lcd_version", {}).get("lcd_id", ""))
        lcd_id = str(lcd_id_raw) if lcd_id_raw else "UNKNOWN"
        version_raw = cms_item.get("lcd_version") or cms_item.get("version")
        version = int(version_raw) if isinstance(version_raw, (int, str)) and str(version_raw).isdigit() else 1
        
        now = datetime.utcnow()
        content_hash = CMSNormalizer._compute_hash(cms_item)

        lcd = LCD(
            lcd_id=lcd_id,
            lcd_version=version,
            display_id=cms_item.get("display_id"),
            title=cms_item.get("title") or cms_item.get("articleTitle"),
            status=cms_item.get("status"),
            cms_cov_policy=cms_item.get("cms_cov_policy"),
            indication=cms_item.get("indication"),
            diagnoses_support=cms_item.get("diagnoses_support"),
            diagnoses_dont_support=cms_item.get("diagnoses_dont_support"),
            coding_guidelines=cms_item.get("coding_guidelines"),
            doc_reqs=cms_item.get("doc_reqs"),
            summary_of_evidence=cms_item.get("summary_of_evidence"),
            analysis_of_evidence=cms_item.get("analysis_of_evidence"),
            orig_det_eff_date=CMSNormalizer._parse_date(cms_item.get("orig_det_eff_date") or cms_item.get("effectiveDate")),
            rev_eff_date=CMSNormalizer._parse_date(cms_item.get("rev_eff_date")),
            rev_end_date=CMSNormalizer._parse_date(cms_item.get("rev_end_date")),
            date_retired=CMSNormalizer._parse_date(cms_item.get("date_retired")),
            last_updated=CMSNormalizer._parse_datetime(cms_item.get("last_updated")),
            icd10_doc=str(cms_item.get("icd10_doc")).lower() == "true" if cms_item.get("icd10_doc") else None,
            associated_article_ids=cms_item.get("associated_article_ids"),
            
            
            
        )

        hcpcs_codes = []
        icd10_covered = []
        icd10_noncovered = []

        # If the API returns arrays (even though currently it might not)
        for h in cms_item.get("hcpcs_codes", []):
            hcpcs_codes.append(LCDHCPCSCode(
                lcd_id=lcd_id,
                lcd_version=version,
                hcpcs_code=h.get("code"),
                description=h.get("description")
            ))

        for icd in cms_item.get("icd10_covered", []):
            icd10_covered.append(LCDIcd10Covered(
                lcd_id=lcd_id,
                lcd_version=version,
                icd10_code=icd.get("code"),
                description=icd.get("description")
            ))

        for icd in cms_item.get("icd10_noncovered", []):
            icd10_noncovered.append(LCDIcd10NonCovered(
                lcd_id=lcd_id,
                lcd_version=version,
                icd10_code=icd.get("code"),
                description=icd.get("description")
            ))

        return {
            "policy": lcd,
            "hcpcs": hcpcs_codes,
            "icd10_covered": icd10_covered,
            "icd10_noncovered": icd10_noncovered,
            "type": "LCD"
        }

    @staticmethod
    def normalize_article(cms_item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize an Article document."""
        art_id_raw = cms_item.get("article_id") or cms_item.get("articleId")
        art_id = str(art_id_raw) if art_id_raw else "UNKNOWN"
        version_raw = cms_item.get("article_version") or cms_item.get("version")
        version = int(version_raw) if isinstance(version_raw, (int, str)) and str(version_raw).isdigit() else 1
        
        now = datetime.utcnow()
        content_hash = CMSNormalizer._compute_hash(cms_item)

        article = Article(
            article_id=art_id,
            article_version=version,
            title=cms_item.get("title") or cms_item.get("articleTitle"),
            status=cms_item.get("status"),
            description=cms_item.get("description"),
            cms_cov_policy=cms_item.get("cms_cov_policy"),
            article_eff_date=CMSNormalizer._parse_date(cms_item.get("article_eff_date") or cms_item.get("effectiveDate")),
            article_end_date=CMSNormalizer._parse_date(cms_item.get("article_end_date")),
            last_updated=CMSNormalizer._parse_datetime(cms_item.get("last_updated")),
            date_retired=CMSNormalizer._parse_date(cms_item.get("date_retired")),
            
            
            
        )

        hcpcs_codes = []
        icd10_covered = []
        icd10_noncovered = []
        
        for h in cms_item.get("hcpcs_codes", []):
            hcpcs_codes.append(ArticleHcpcsCode(
                article_id=art_id,
                article_version=version,
                hcpcs_code_id=h.get("code"),
                short_description=h.get("description")
            ))

        return {
            "policy": article,
            "hcpcs": hcpcs_codes,
            "icd10_covered": icd10_covered,
            "icd10_noncovered": icd10_noncovered,
            "type": "ARTICLE"
        }

    @staticmethod
    def normalize_document(cms_item: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        """Automatically route based on document ID prefix or keys."""
        if document_id.upper().startswith("L") or "lcd_id" in cms_item or "lcdId" in cms_item:
            return CMSNormalizer.normalize_lcd(cms_item)
        elif document_id.upper().startswith("A") or "article_id" in cms_item or "articleId" in cms_item:
            return CMSNormalizer.normalize_article(cms_item)
        else:
            # Fallback to LCD if unsure
            return CMSNormalizer.normalize_lcd(cms_item)
