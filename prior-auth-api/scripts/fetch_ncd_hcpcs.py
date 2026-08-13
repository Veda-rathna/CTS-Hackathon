"""Fetch and seed NCD HCPCS code crosswalk data.

Strategy
--------
The CMS Coverage API does not expose a dedicated HCPCS codes endpoint for
NCDs (unlike Articles which have /data/article/hcpc-code).

We use two complementary strategies:

1. LCD Bridge Inheritance (primary):
   For every NCD that is already linked to at least one LCD via the
   lcd_ncd_associations table, we inherit all HCPCS codes from that LCD's
   lcd_hcpcs_codes table.  This is medically correct — if a MAC wrote an
   LCD for the same procedure and linked it to an NCD, those HCPCS codes
   apply to the NCD as well.

2. CMS API Text Extraction (supplemental):
   For standalone NCDs (no LCD bridge), we call the CMS Coverage API and
   parse HCPCS/CPT codes from the item_service_description and
   indications_limitations narrative fields using a regex pattern.

Run with:
    cd prior-auth-api
    .venv\\Scripts\\activate
    python scripts/fetch_ncd_hcpcs.py

The script is idempotent — it clears ncd_hcpcs_codes before re-inserting.
"""
from __future__ import annotations

import html
import json
import logging
import re
import sys
import time
import os
import urllib.request
import urllib.error
from collections import defaultdict

# ---------------------------------------------------------------------------
# Setup path so app imports work
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, insert

from app.db.session import SessionLocal
from app.models.lcd import LCDHCPCSCode
from app.models.ncd import NCD, LCDNCDAssociation, NCDHCPCSCode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CMS_BASE = "https://api.coverage.cms.gov/v1"
# HCPCS/CPT code pattern: letter + 4 digits (HCPCS Level II) OR 5 digits (CPT)
HCPCS_PATTERN = re.compile(r"\b([A-Z]\d{4}|\d{5})\b")
# How long to wait between API requests to avoid rate limiting
REQUEST_DELAY_SECS = 0.25


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_json(url: str, retries: int = 2) -> dict:
    """Fetch a URL and return parsed JSON. Retries on transient errors."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=6) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            log.warning("HTTP %s for %s (attempt %d)", e.code, url, attempt + 1)
            if e.code in (400, 404):
                return {}
            time.sleep(1.0)
        except Exception as e:
            log.warning("Error fetching %s: %s (attempt %d)", url, e, attempt + 1)
            time.sleep(1.0)
    return {}


def _extract_hcpcs_from_text(text: str) -> set[str]:
    """Extract candidate HCPCS/CPT codes from free text using regex."""
    clean = html.unescape(text or "")
    return set(HCPCS_PATTERN.findall(clean))


def _fetch_ncd_hcpcs_from_api(ncd_id: str, ncd_ver: int) -> set[str]:
    """Call CMS API and extract HCPCS codes embedded in NCD narrative text."""
    url = f"{CMS_BASE}/data/ncd?ncdid={ncd_id}&ncdversion={ncd_ver}"
    data = _fetch_json(url)
    rows = data.get("data", [])
    if not rows:
        return set()

    row = rows[0]
    combined_text = " ".join([
        row.get("item_service_description", ""),
        row.get("indications_limitations", ""),
        row.get("cross_reference", ""),
    ])
    return _extract_hcpcs_from_text(combined_text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    db = SessionLocal()
    try:
        # ── Step 1: Load existing DB data ────────────────────────────────────
        log.info("Loading NCD and association data from database...")

        # Build a fast lookup: ncd_id -> latest ncd_version
        all_ncds = db.execute(select(NCD.document_id, NCD.document_version)).all()
        ncd_latest_ver: dict[str, int] = {}
        for r in all_ncds:
            if r.document_id not in ncd_latest_ver or r.document_version > ncd_latest_ver[r.document_id]:
                ncd_latest_ver[r.document_id] = r.document_version
        log.info("Found %d unique NCDs in database.", len(ncd_latest_ver))

        # Build lookup: ncd_id -> list of (lcd_id, lcd_version)
        assoc_rows = db.execute(
            select(LCDNCDAssociation.ncd_id, LCDNCDAssociation.lcd_id, LCDNCDAssociation.lcd_version)
        ).all()
        ncd_to_lcds: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for row in assoc_rows:
            ncd_to_lcds[row.ncd_id].append((row.lcd_id, row.lcd_version))

        linked_ncd_ids = set(ncd_to_lcds.keys())
        all_ncd_ids = set(ncd_latest_ver.keys())
        standalone_ncd_ids = all_ncd_ids - linked_ncd_ids

        log.info(
            "NCDs with LCD bridge: %d | Standalone NCDs: %d",
            len(linked_ncd_ids),
            len(standalone_ncd_ids),
        )

        # Build a fast lookup for LCD HCPCS codes: (lcd_id, lcd_version) -> list[(code, desc)]
        log.info("Pre-loading all LCD HCPCS codes into memory...")
        all_lcd_hcpcs = db.execute(
            select(LCDHCPCSCode.lcd_id, LCDHCPCSCode.lcd_version, LCDHCPCSCode.hcpcs_code, LCDHCPCSCode.description)
        ).all()
        lcd_hcpcs_lookup: dict[tuple[str, int], list[tuple[str, str | None]]] = defaultdict(list)
        for row in all_lcd_hcpcs:
            lcd_hcpcs_lookup[(row.lcd_id, row.lcd_version)].append((row.hcpcs_code, row.description))
        log.info("Loaded %d LCD HCPCS code rows into memory.", len(all_lcd_hcpcs))

        # ── Step 2: Clear existing ncd_hcpcs_codes data ──────────────────────
        log.info("Clearing existing ncd_hcpcs_codes table...")
        db.query(NCDHCPCSCode).delete()
        db.commit()

        # ── Step 3: Strategy 1 — Inherit HCPCS codes from linked LCDs ────────
        log.info("Strategy 1: Inheriting HCPCS codes from LCD bridge (in-memory)...")
        inserts: list[dict] = []
        seen: set[tuple[str, int, str]] = set()

        for ncd_id, lcd_list in ncd_to_lcds.items():
            ncd_ver = ncd_latest_ver.get(ncd_id)
            if ncd_ver is None:
                continue
            for lcd_id, lcd_ver in lcd_list:
                for hcpcs_code, description in lcd_hcpcs_lookup.get((lcd_id, lcd_ver), []):
                    key = (ncd_id, ncd_ver, hcpcs_code)
                    if key not in seen:
                        seen.add(key)
                        inserts.append({
                            "ncd_id": ncd_id,
                            "ncd_version": ncd_ver,
                            "hcpcs_code": hcpcs_code,
                            "description": description,
                        })

        log.info("Strategy 1 produced %d NCD-HCPCS mappings.", len(inserts))

        # Commit Strategy 1 immediately so data is safe
        if inserts:
            log.info("Committing Strategy 1 data to database...")
            for i in range(0, len(inserts), 1000):
                db.execute(insert(NCDHCPCSCode), inserts[i : i + 1000])
            db.commit()
            log.info("Strategy 1 committed successfully.")

        # ── Step 4: Strategy 2 — API text extraction for standalone NCDs ─────
        log.info("Strategy 2: Extracting HCPCS from CMS API text for %d standalone NCDs...", len(standalone_ncd_ids))
        api_inserts: list[dict] = []
        api_count = 0
        standalone_list = sorted(standalone_ncd_ids)

        for idx, ncd_id in enumerate(standalone_list, 1):
            ncd_ver = ncd_latest_ver.get(ncd_id)
            if ncd_ver is None:
                continue

            codes = _fetch_ncd_hcpcs_from_api(ncd_id, ncd_ver)
            for code in codes:
                key = (ncd_id, ncd_ver, code)
                if key not in seen:
                    seen.add(key)
                    api_inserts.append({
                        "ncd_id": ncd_id,
                        "ncd_version": ncd_ver,
                        "hcpcs_code": code,
                        "description": None,
                    })
                    api_count += 1

            if idx % 10 == 0 or idx == len(standalone_list):
                log.info("  API progress: %d / %d NCDs | codes found so far: %d", idx, len(standalone_list), api_count)

            time.sleep(REQUEST_DELAY_SECS)

        log.info("Strategy 2 produced %d additional NCD-HCPCS mappings.", api_count)

        # ── Step 5: Insert Strategy 2 results ────────────────────────────────
        if api_inserts:
            log.info("Committing Strategy 2 data to database...")
            for i in range(0, len(api_inserts), 1000):
                db.execute(insert(NCDHCPCSCode), api_inserts[i : i + 1000])
            db.commit()

        # ── Step 5b: Strategy 3 — Mock Data for Hackathon ────────────────────
        still_unmapped = set(standalone_ncd_ids) - {i["ncd_id"] for i in api_inserts}
        if still_unmapped:
            log.info("Strategy 3: Loading mock mappings for %d remaining NCDs...", len(still_unmapped))
            mock_inserts = []
            mock_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Filtered_Data", "mock_ncd_mappings.csv")
            import csv
            if os.path.exists(mock_file):
                with open(mock_file, encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["ncd_id"] in still_unmapped:
                            ncd_ver = ncd_latest_ver.get(row["ncd_id"])
                            if ncd_ver is not None:
                                mock_inserts.append({
                                    "ncd_id": row["ncd_id"],
                                    "ncd_version": ncd_ver,
                                    "hcpcs_code": row["hcpcs_code"],
                                    "description": row["description"]
                                })
                                still_unmapped.remove(row["ncd_id"])

                if mock_inserts:
                    log.info("Committing %d Strategy 3 (Mock) mappings...", len(mock_inserts))
                    for i in range(0, len(mock_inserts), 1000):
                        db.execute(insert(NCDHCPCSCode), mock_inserts[i : i + 1000])
                    db.commit()
            else:
                log.warning("Mock mappings file not found at %s", mock_file)
        else:
            mock_inserts = []

        # ── Step 6: Final Summary ─────────────────────────────────────────────
        total = db.query(NCDHCPCSCode).count()
        unique_ncds = db.execute(select(NCDHCPCSCode.ncd_id).distinct()).scalars().all()
        log.info("=" * 60)
        log.info("COMPLETE. Final ncd_hcpcs_codes table stats:")
        log.info("  Total rows    : %d", total)
        log.info("  Strategy 1    : %d (LCD bridge)", len(inserts))
        log.info("  Strategy 2    : %d (API text extraction)", api_count)
        log.info("  Strategy 3    : %d (Hackathon mock data)", len(mock_inserts))
        log.info("  NCDs covered  : %d / %d", len(unique_ncds), len(all_ncd_ids))
        log.info("=" * 60)

    except Exception as e:
        db.rollback()
        log.error("Fatal error: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
