import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import engine

def get_combinations(prefix, limit=5):
    query = f"""
    SELECT h.hcpcs_code_id, i.icd10_code_id, s.state_code, a.article_id, l.lcd_id
    FROM article_icd10_covered i
    JOIN article_hcpcs h ON i.article_id = h.article_id
    JOIN articles a ON a.article_id = i.article_id
    LEFT JOIN lcds l ON l.associated_article_ids LIKE '%' || a.article_id || '%'
    LEFT JOIN jurisdictions j ON l.lcd_id = j.lcd_id
    LEFT JOIN states s ON j.state_id = s.state_id
    WHERE i.icd10_code_id LIKE '{prefix}%'
    AND s.state_code IS NOT NULL
    AND LENGTH(s.state_code) = 2
    AND s.state_code NOT IN ('52', '53', '58', '59')
    GROUP BY i.icd10_code_id, h.hcpcs_code_id, s.state_code, a.article_id, l.lcd_id
    LIMIT {limit};
    """
    with Session(engine) as session:
        return session.execute(text(query)).fetchall()

if __name__ == '__main__':
    print("M:", get_combinations("M", 5))
    print("E:", get_combinations("E", 5))
    print("J:", get_combinations("J", 5))
