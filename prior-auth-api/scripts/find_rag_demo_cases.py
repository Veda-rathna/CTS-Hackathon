"""
Find real procedure codes in Neon DB that link LCDs -> NCDs with RAG chunks.
"""
from __future__ import annotations

import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine

def main():
    with engine.connect() as conn:
        query = text("""
            SELECT h.hcpcs_code, l.lcd_id, a.ncd_id, n.title
            FROM lcd_hcpcs_codes h
            JOIN lcds l ON h.lcd_id = l.lcd_id AND h.lcd_version = l.lcd_version
            JOIN lcd_ncd_associations a ON l.lcd_id = a.lcd_id AND l.lcd_version = a.lcd_version
            JOIN ncds n ON a.ncd_id = n.document_id AND a.ncd_version = n.document_version
            JOIN policy_chunks pc ON n.document_id = pc.policy_id AND pc.policy_type = 'NCD'
            LIMIT 10
        """)
        rows = conn.execute(query).fetchall()
        print("Real DB Procedures linking LCD -> NCD with RAG Chunks:")
        for r in rows:
            print(f"  • HCPCS: {r.hcpcs_code:10s} | LCD: {r.lcd_id:10s} | NCD: {r.ncd_id:10s} | NCD Title: {r.title[:45]}")

if __name__ == "__main__":
    main()
