"""Database seeder script.

Reads CSV files from the Filtered_Data directory, resolves relationships,
and seeds the PostgreSQL database using SQLAlchemy models supporting composite primary keys.

Run with:
    cd prior-auth-api
    .venv\Scripts\activate
    python scripts/seed_db.py
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, date

# Increase CSV field size limit to handle large CMS narrative fields
max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int / 10)

# Add the project root to sys.path so app imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import insert
from app.db.session import SessionLocal
from app.models.base import Base
from app.models.contractor import Contractor
from app.models.jurisdiction import Jurisdiction
from app.models.state import State
from app.models.article import Article, ArticleIcd10Covered, ArticleIcd10NonCovered, ArticleHcpcsCode
from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered, LCDIcd10NonCovered
from app.models.ncd import NCD, LCDNCDAssociation

# Path to the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Filtered_Data")


def clean_id(val: str) -> str:
    """Clean float-like strings (e.g. '33942.0' -> '33942')."""
    if not val:
        return ""
    val_str = val.strip()
    if val_str.endswith(".0"):
        return val_str[:-2]
    try:
        return str(int(float(val_str)))
    except ValueError:
        return val_str


def clean_int(val: str) -> int:
    """Safely parse strings to int."""
    if not val:
        return 0
    try:
        return int(float(val.strip()))
    except ValueError:
        return 0


def clean_bool(val: str) -> bool:
    """Clean boolean fields."""
    if not val:
        return False
    val_str = val.strip().upper()
    return val_str in ("Y", "YES", "TRUE", "1")


def clean_date(val: str) -> date | None:
    """Parse dates from CSV formats."""
    if not val or val.strip().upper() in ("N/A", "NULL", ""):
        return None
    val_str = val.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None


def clean_datetime(val: str) -> datetime | None:
    """Parse datetimes from CSV formats."""
    if not val or val.strip().upper() in ("N/A", "NULL", ""):
        return None
    val_str = val.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            continue
    return None


def read_csv(filename: str) -> list[dict[str, str]]:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"Error: {path} not found!")
        return []
    with open(path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def main():
    print("Starting database seeding...")
    db = SessionLocal()
    
    try:
        # 1. Clear existing database tables in correct dependency order
        print("Clearing existing tables...")
        from app.models.policy_chunk import PolicyChunk
        from app.models.ncd import NCDHCPCSCode

        db.query(PolicyChunk).delete()
        db.query(LCDNCDAssociation).delete()
        db.query(NCDHCPCSCode).delete()
        db.query(LCDHCPCSCode).delete()
        db.query(LCDIcd10Covered).delete()
        db.query(LCDIcd10NonCovered).delete()
        db.query(ArticleHcpcsCode).delete()
        db.query(ArticleIcd10Covered).delete()
        db.query(ArticleIcd10NonCovered).delete()
        db.query(LCD).delete()
        db.query(Article).delete()
        db.query(Jurisdiction).delete()
        db.query(State).delete()
        db.query(Contractor).delete()
        db.query(NCD).delete()
        db.commit()
        print("Existing data cleared.")

        # 2. Seed Contractors
        print("Seeding Contractors...")
        contractors_raw = read_csv("Contractor.csv")
        contractor_dicts = {}
        for row in contractors_raw:
            c_id = clean_id(row.get("contractor_id", ""))
            if c_id and c_id not in contractor_dicts:
                contractor_dicts[c_id] = {
                    "contractor_id": c_id,
                    "contract_type_id": clean_int(row.get("contract_type_id", "")),
                    "contract_subtype_id": clean_int(row.get("contract_subtype_id", "")),
                    "contractor_version": clean_int(row.get("contractor_version", "")),
                    "contract_number": row.get("contract_number", "").strip() or None,
                    "contractor_name": row.get("contractor_name", "").strip() or None
                }
        if contractor_dicts:
            db.execute(insert(Contractor), list(contractor_dicts.values()))
            print(f"Inserted {len(contractor_dicts)} Contractors.")

        # 3. Seed States
        print("Seeding States...")
        jur_raw = read_csv("Jurisdiction_With_States.csv")
        states_dicts = {}
        for row in jur_raw:
            s_id = clean_int(row.get("state_id", ""))
            s_code = row.get("state_code", "").strip().upper()
            s_name = row.get("state_name", "").strip()
            if s_id and s_code and s_id not in states_dicts:
                states_dicts[s_id] = {
                    "state_id": s_id,
                    "state_code": s_code,
                    "state_name": s_name
                }
        if states_dicts:
            db.execute(insert(State), list(states_dicts.values()))
            print(f"Inserted {len(states_dicts)} States.")

        # 4. Seed Jurisdictions
        print("Seeding Jurisdictions...")
        jurisdiction_inserts = []
        for row in jur_raw:
            lcd_id = clean_id(row.get("lcd_id", ""))
            lcd_ver = clean_int(row.get("lcd_version", ""))
            s_id = clean_int(row.get("state_id", ""))
            if lcd_id and lcd_ver and s_id in states_dicts:
                jurisdiction_inserts.append({
                    "lcd_id": lcd_id,
                    "lcd_version": lcd_ver,
                    "state_id": s_id,
                    "last_updated": clean_datetime(row.get("last_updated", "")),
                    "source_type": row.get("source_type", "").strip() or None,
                    "source_id": clean_id(row.get("source_id", "")) or None,
                    "article_id": clean_id(row.get("article_id", "")) or None,
                    "article_version": clean_int(row.get("article_version", "")) or None
                })
        if jurisdiction_inserts:
            db.execute(insert(Jurisdiction), jurisdiction_inserts)
            print(f"Inserted {len(jurisdiction_inserts)} Jurisdictions.")

        # 5. Seed Articles
        print("Seeding Articles...")
        articles_raw = read_csv("Article.csv")
        article_dicts = {}
        for row in articles_raw:
            art_id = clean_id(row.get("article_id", ""))
            art_ver = clean_int(row.get("article_version", ""))
            if art_id and art_ver:
                key = (art_id, art_ver)
                if key not in article_dicts:
                    article_dicts[key] = {
                        "article_id": art_id,
                        "article_version": art_ver,
                        "display_id": row.get("display_id", "").strip() or None,
                        "title": row.get("title", "").strip() or None,
                        "status": row.get("status", "").strip().upper() or None,
                        "article_type": clean_int(row.get("article_type", "")),
                        "article_type_description": row.get("article_type_description", "").strip() or None,
                        "description": row.get("description", "").strip() or None,
                        "cms_cov_policy": row.get("cms_cov_policy", "").strip() or None,
                        "icd10_doc": clean_bool(row.get("icd10_doc", "")),
                        "article_eff_date": clean_date(row.get("article_eff_date", "")),
                        "article_end_date": clean_date(row.get("article_end_date", "")),
                        "article_pub_date": clean_date(row.get("article_pub_date", "")),
                        "last_updated": clean_datetime(row.get("last_updated", "")),
                        "date_retired": clean_date(row.get("date_retired", "")),
                        "reference_article": clean_bool(row.get("reference_article", ""))
                    }
        if article_dicts:
            art_list = list(article_dicts.values())
            for i in range(0, len(art_list), 50):
                db.execute(insert(Article), art_list[i:i+50])
            print(f"Inserted {len(article_dicts)} Articles.")

        # 6. Seed Article HCPCS Codes
        print("Seeding Article HCPCS Codes...")
        art_hcpcs_raw = read_csv("Article_HCPCS.csv")
        hcpcs_inserts = []
        seen_hcpcs = set()
        for row in art_hcpcs_raw:
            art_id = clean_id(row.get("article_id", ""))
            art_ver = clean_int(row.get("article_version", ""))
            code = row.get("hcpc_code_id", "").strip().upper()
            if (art_id, art_ver) in article_dicts and code:
                key = (art_id, art_ver, code)
                if key not in seen_hcpcs:
                    seen_hcpcs.add(key)
                    hcpcs_inserts.append({
                        "article_id": art_id,
                        "article_version": art_ver,
                        "hcpcs_code_id": code,
                        "hcpcs_code_version": clean_int(row.get("hcpc_code_version", "")),
                        "code_group": clean_int(row.get("hcpc_code_group", "")),
                        "long_description": row.get("long_description", "").strip() or None,
                        "short_description": row.get("short_description", "").strip() or None,
                        "range_flag": row.get("range", "").strip() or None,
                        "last_updated": clean_datetime(row.get("last_updated", ""))
                    })
        for i in range(0, len(hcpcs_inserts), 5000):
            db.execute(insert(ArticleHcpcsCode), hcpcs_inserts[i:i+5000])
        print(f"Inserted {len(hcpcs_inserts)} Article HCPCS codes.")

        # 7. Seed Article Covered ICD-10 Codes
        print("Seeding Article Covered ICD-10 Codes...")
        cov_raw = read_csv("ICD10_Covered_MEJ.csv")
        cov_inserts = []
        seen_cov = set()
        for row in cov_raw:
            art_id = clean_id(row.get("article_id", ""))
            art_ver = clean_int(row.get("article_version", ""))
            dx = row.get("icd10_code_id", "").strip().upper()
            if (art_id, art_ver) in article_dicts and dx:
                key = (art_id, art_ver, dx)
                if key not in seen_cov:
                    seen_cov.add(key)
                    cov_inserts.append({
                        "article_id": art_id,
                        "article_version": art_ver,
                        "icd10_code_id": dx,
                        "icd10_code_version": clean_int(row.get("icd10_code_version", "")),
                        "coverage_group": clean_int(row.get("icd10_covered_group", "")),
                        "range_flag": row.get("range", "").strip() or None,
                        "sort_order": clean_int(row.get("sort_order", "")),
                        "description": row.get("description", "").strip() or None,
                        "asterisk": row.get("asterisk", "").strip() or None,
                        "last_updated": clean_datetime(row.get("last_updated", ""))
                    })
        for i in range(0, len(cov_inserts), 5000):
            db.execute(insert(ArticleIcd10Covered), cov_inserts[i:i+5000])
        print(f"Inserted {len(cov_inserts)} Covered ICD-10 codes.")

        # 8. Seed Article Non-Covered ICD-10 Codes
        print("Seeding Article Non-Covered ICD-10 Codes...")
        noncov_raw = read_csv("ICD10_NonCovered_MEJ.csv")
        noncov_inserts = []
        seen_noncov = set()
        for row in noncov_raw:
            art_id = clean_id(row.get("article_id", ""))
            art_ver = clean_int(row.get("article_version", ""))
            dx = row.get("icd10_code_id", "").strip().upper()
            if (art_id, art_ver) in article_dicts and dx:
                key = (art_id, art_ver, dx)
                if key not in seen_noncov:
                    seen_noncov.add(key)
                    noncov_inserts.append({
                        "article_id": art_id,
                        "article_version": art_ver,
                        "icd10_code_id": dx,
                        "icd10_code_version": clean_int(row.get("icd10_code_version", "")),
                        "noncovered_group": clean_int(row.get("icd10_noncovered_group", "")),
                        "range_flag": row.get("range", "").strip() or None,
                        "sort_order": clean_int(row.get("sort_order", "")),
                        "description": row.get("description", "").strip() or None,
                        "asterisk": row.get("asterisk", "").strip() or None,
                        "last_updated": clean_datetime(row.get("last_updated", ""))
                    })
        for i in range(0, len(noncov_inserts), 5000):
            db.execute(insert(ArticleIcd10NonCovered), noncov_inserts[i:i+5000])
        print(f"Inserted {len(noncov_inserts)} Non-Covered ICD-10 codes.")

        # 9. Map LCD relationships
        print("Mapping LCD metadata relationships...")
        rel_docs = read_csv("Related_Documents.csv")
        lcd_to_articles: dict[tuple[str, int], set[str]] = {}
        lcd_to_contractor: dict[tuple[str, int], str] = {}
        for row in rel_docs:
            l_id = clean_id(row.get("lcd_id", ""))
            l_ver = clean_int(row.get("lcd_version", ""))
            art_id = clean_id(row.get("r_article_id", ""))
            cont_id = clean_id(row.get("r_contractor_id", ""))
            if l_id and l_ver:
                key = (l_id, l_ver)
                if art_id:
                    lcd_to_articles.setdefault(key, set()).add(art_id)
                if cont_id and cont_id in contractor_dicts:
                    lcd_to_contractor[key] = cont_id
                    
        # Group jurisdiction codes to LCDs
        lcd_to_jurisdiction: dict[tuple[str, int], str] = {}
        for row in jur_raw:
            l_id = clean_id(row.get("lcd_id", ""))
            l_ver = clean_int(row.get("lcd_version", ""))
            jur_code = row.get("jurisdiction", "").strip().upper()
            if l_id and l_ver and jur_code:
                lcd_to_jurisdiction[(l_id, l_ver)] = jur_code

        # 10. Seed LCDs
        print("Seeding LCDs...")
        lcds_raw = read_csv("LCD.csv")
        lcd_dicts = {}
        for row in lcds_raw:
            lcd_id = clean_id(row.get("lcd_id", ""))
            lcd_ver = clean_int(row.get("lcd_version", ""))
            if lcd_id and lcd_ver:
                key = (lcd_id, lcd_ver)
                if key not in lcd_dicts:
                    articles_list = sorted(list(lcd_to_articles.get(key, set())))
                    articles_str = ",".join(articles_list) if articles_list else None
                    
                    lcd_dicts[key] = {
                        "lcd_id": lcd_id,
                        "lcd_version": lcd_ver,
                        "display_id": row.get("display_id", "").strip() or None,
                        "title": row.get("title", "").strip() or None,
                        "status": row.get("status", "").strip() or None,
                        "cms_cov_policy": row.get("cms_cov_policy", "").strip() or None,
                        "indication": row.get("indication", "").strip() or None,
                        "diagnoses_support": row.get("diagnoses_support", "").strip() or None,
                        "diagnoses_dont_support": row.get("diagnoses_dont_support", "").strip() or None,
                        "coding_guidelines": row.get("coding_guidelines", "").strip() or None,
                        "doc_reqs": row.get("doc_reqs", "").strip() or None,
                        "summary_of_evidence": row.get("summary_of_evidence", "").strip() or None,
                        "analysis_of_evidence": row.get("analysis_of_evidence", "").strip() or None,
                        "associated_info": row.get("associated_info", "").strip() or None,
                        "bibliography": row.get("bibliography", "").strip() or None,
                        "appendices": row.get("appendices", "").strip() or None,
                        "util_guide": row.get("util_guide", "").strip() or None,
                        "orig_det_eff_date": clean_date(row.get("orig_det_eff_date", "")),
                        "rev_eff_date": clean_date(row.get("rev_eff_date", "")),
                        "rev_end_date": clean_date(row.get("rev_end_date", "")),
                        "date_retired": clean_date(row.get("date_retired", "")),
                        "last_updated": clean_datetime(row.get("last_updated", "")),
                        "icd10_doc": clean_bool(row.get("icd10_doc", "")),
                        "keywords": row.get("keywords", "").strip() or None,
                        "jurisdiction_id": lcd_to_jurisdiction.get(key),
                        "contractor_id": lcd_to_contractor.get(key),
                        "associated_article_ids": articles_str
                    }
        if lcd_dicts:
            lcd_list = list(lcd_dicts.values())
            for i in range(0, len(lcd_list), 50):
                db.execute(insert(LCD), lcd_list[i:i+50])
            print(f"Inserted {len(lcd_dicts)} LCD versions.")

        # 11. Populate LCD-level code tables from associated articles
        print("Populating LCD-level code tables from associated articles...")
        lcd_hcpcs = []
        lcd_cov = []
        lcd_noncov = []

        # Map article codes for fast in-memory lookup
        art_hcpcs_map: dict[str, list[dict]] = {}
        for item in hcpcs_inserts:
            art_hcpcs_map.setdefault(item["article_id"], []).append(item)
            
        art_cov_map: dict[str, list[dict]] = {}
        for item in cov_inserts:
            art_cov_map.setdefault(item["article_id"], []).append(item)
            
        art_noncov_map: dict[str, list[dict]] = {}
        for item in noncov_inserts:
            art_noncov_map.setdefault(item["article_id"], []).append(item)

        for (lcd_id, lcd_ver), art_ids in lcd_to_articles.items():
            if (lcd_id, lcd_ver) not in lcd_dicts:
                continue
            seen_lcd_hcpcs = set()
            seen_lcd_cov = set()
            seen_lcd_noncov = set()
            
            for art_id in art_ids:
                # Add HCPCS
                for code_item in art_hcpcs_map.get(art_id, []):
                    code = code_item["hcpcs_code_id"]
                    if code not in seen_lcd_hcpcs:
                        seen_lcd_hcpcs.add(code)
                        lcd_hcpcs.append({
                            "lcd_id": lcd_id,
                            "lcd_version": lcd_ver,
                            "hcpcs_code": code,
                            "description": code_item["long_description"] or code_item["short_description"]
                        })
                # Add Covered
                for dx_item in art_cov_map.get(art_id, []):
                    dx = dx_item["icd10_code_id"]
                    if dx not in seen_lcd_cov:
                        seen_lcd_cov.add(dx)
                        lcd_cov.append({
                            "lcd_id": lcd_id,
                            "lcd_version": lcd_ver,
                            "icd10_code": dx,
                            "description": dx_item["description"]
                        })
                # Add Non-covered
                for dx_item in art_noncov_map.get(art_id, []):
                    dx = dx_item["icd10_code_id"]
                    if dx not in seen_lcd_noncov:
                        seen_lcd_noncov.add(dx)
                        lcd_noncov.append({
                            "lcd_id": lcd_id,
                            "lcd_version": lcd_ver,
                            "icd10_code": dx,
                            "description": dx_item["description"]
                        })

        if lcd_hcpcs:
            for i in range(0, len(lcd_hcpcs), 5000):
                db.execute(insert(LCDHCPCSCode), lcd_hcpcs[i:i+5000])
            print(f"Inserted {len(lcd_hcpcs)} LCD HCPCS codes.")
        if lcd_cov:
            for i in range(0, len(lcd_cov), 5000):
                db.execute(insert(LCDIcd10Covered), lcd_cov[i:i+5000])
            print(f"Inserted {len(lcd_cov)} LCD covered ICD-10 codes.")
        if lcd_noncov:
            for i in range(0, len(lcd_noncov), 5000):
                db.execute(insert(LCDIcd10NonCovered), lcd_noncov[i:i+5000])
            print(f"Inserted {len(lcd_noncov)} LCD non-covered ICD-10 codes.")

        # 12. Seed NCDs
        print("Seeding NCDs...")
        ncd_raw = read_csv("NCD.csv")
        ncd_dicts = {}
        for row in ncd_raw:
            n_id = clean_id(row.get("document_id", ""))
            n_ver = clean_int(row.get("document_version", ""))
            if n_id and n_ver:
                key = (n_id, n_ver)
                if key not in ncd_dicts:
                    desc = row.get("item_service_description", "").strip()
                    ind = row.get("indications_limitations", "").strip().upper()
                    
                    decision = "COVERED"
                    if "NOT COVERED" in ind or "NON-COVERED" in ind or "EXCLUDED" in ind:
                        decision = "EXCLUDED"
                    elif "COVERED WITH CONDITIONS" in ind or "CONDITIONS" in ind:
                        decision = "COVERED_WITH_CONDITIONS"
                    
                    ncd_dicts[key] = {
                        "document_id": n_id,
                        "document_version": n_ver,
                        "document_display_id": row.get("document_display_id", "").strip() or None,
                        "title": row.get("title", "").strip() or None,
                        "publication_number": row.get("publication_number", "").strip() or None,
                        "benefit_category": row.get("benefit_category", "").strip() or None,
                        "item_service_description": desc or None,
                        "indications_limitations": row.get("indications_limitations", "").strip() or None,
                        "reasons_for_denial": row.get("reasons_for_denial", "").strip() or None,
                        "cross_reference": row.get("cross_reference", "").strip() or None,
                        "effective_date": clean_date(row.get("effective_date", "")),
                        "effective_end_date": clean_date(row.get("effective_end_date", "")),
                        "implementation_date": clean_date(row.get("implementation_date", "")),
                        "revision_history": row.get("revision_history", "").strip() or None,
                        "other_text": row.get("other_text", "").strip() or None,
                        "decision": decision
                    }
        if ncd_dicts:
            ncd_list = list(ncd_dicts.values())
            for i in range(0, len(ncd_list), 50):
                db.execute(insert(NCD), ncd_list[i:i+50])
            print(f"Inserted {len(ncd_dicts)} NCD versions.")

        # 13. Seed LCD NCD Associations
        print("Seeding LCD NCD Associations...")
        rel_ncds = read_csv("Related_NCD.csv")
        ncd_association_inserts = []
        seen_ncd_assoc = set()
        for row in rel_ncds:
            lcd_id = clean_id(row.get("lcd_id", ""))
            lcd_ver = clean_int(row.get("lcd_version", ""))
            ncd_id = clean_id(row.get("r_ncd_id", ""))
            ncd_ver = clean_int(row.get("r_ncd_version", ""))
            # Ensure both the LCD and NCD target records exist
            if (lcd_id, lcd_ver) in lcd_dicts and (ncd_id, ncd_ver) in ncd_dicts:
                key = (lcd_id, lcd_ver, ncd_id, ncd_ver)
                if key not in seen_ncd_assoc:
                    seen_ncd_assoc.add(key)
                    ncd_association_inserts.append({
                        "lcd_id": lcd_id,
                        "lcd_version": lcd_ver,
                        "ncd_id": ncd_id,
                        "ncd_version": ncd_ver
                    })
        if ncd_association_inserts:
            db.execute(insert(LCDNCDAssociation), ncd_association_inserts)
            print(f"Inserted {len(ncd_association_inserts)} LCD-NCD Associations.")

        # Commit all transactions
        db.commit()
        print("Seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error occurred during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    main()
