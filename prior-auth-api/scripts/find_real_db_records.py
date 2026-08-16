"""
Query real Neon PostgreSQL database to discover available HCPCS, LCD, Articles, Contractor, and ICD-10 data.
"""
from __future__ import annotations

import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine

def main():
    print("=" * 60)
    print("  NEON POSTGRESQL REAL DATABASE INSPECTION")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. Sample HCPCS codes in LCDs
        hcpcs_sample = conn.execute(text("SELECT hcpcs_code, COUNT(*) FROM lcd_hcpcs_codes GROUP BY hcpcs_code ORDER BY COUNT(*) DESC LIMIT 10")).fetchall()
        print("\nTop HCPCS Codes in LCDs:")
        for h, c in hcpcs_sample:
            print(f"  • HCPCS Code: {h:10s} (in {c} LCDs)")

        # 2. Sample LCDs with HCPCS and ICD10
        lcd_sample = conn.execute(text(
            "SELECT l.lcd_id, l.title, h.hcpcs_code, i.icd10_code "
            "FROM lcds l "
            "JOIN lcd_hcpcs_codes h ON l.lcd_id = h.lcd_id AND l.lcd_version = h.lcd_version "
            "JOIN lcd_icd10_covered i ON l.lcd_id = i.lcd_id AND l.lcd_version = i.lcd_version "
            "LIMIT 5"
        )).fetchall()
        print("\nSample LCD + HCPCS + Covered ICD-10 combinations:")
        for row in lcd_sample:
            print(f"  • LCD {row.lcd_id} | HCPCS: {row.hcpcs_code} | ICD-10: {row.icd10_code} | Title: {row.title[:40]}")

        # 3. Non-covered ICD-10 sample
        noncov_sample = conn.execute(text(
            "SELECT l.lcd_id, h.hcpcs_code, i.icd10_code "
            "FROM lcds l "
            "JOIN lcd_hcpcs_codes h ON l.lcd_id = h.lcd_id AND l.lcd_version = h.lcd_version "
            "JOIN lcd_icd10_noncovered i ON l.lcd_id = i.lcd_id AND l.lcd_version = i.lcd_version "
            "LIMIT 5"
        )).fetchall()
        print("\nSample LCD + HCPCS + Non-Covered ICD-10 combinations:")
        for row in noncov_sample:
            print(f"  • LCD {row.lcd_id} | HCPCS: {row.hcpcs_code} | ICD-10 Non-Covered: {row.icd10_code}")

        # 4. Contractors and jurisdictions
        contractors = conn.execute(text("SELECT contractor_id, contractor_name FROM contractors LIMIT 5")).fetchall()
        print("\nSample Contractors:")
        for c_id, c_name in contractors:
            print(f"  • Contractor ID: {c_id:10s} | Name: {c_name}")

if __name__ == "__main__":
    main()
