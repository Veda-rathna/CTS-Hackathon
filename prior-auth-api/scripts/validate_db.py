import os
import sys
from sqlalchemy import text
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import engine

def validate_db():
    tables = [
        'ncds', 'ncd_hcpcs_codes', 
        'lcds', 'lcd_hcpcs_codes', 'lcd_icd10_covered', 'lcd_icd10_noncovered', 
        'articles', 'article_hcpcs', 'article_icd10_covered', 'article_icd10_noncovered', 
        'states', 'jurisdictions', 'contractors',
        'policy_chunks'
    ]
    with engine.begin() as conn:
        for t in tables:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"Table {t} count: {res}")
            
if __name__ == "__main__":
    validate_db()
