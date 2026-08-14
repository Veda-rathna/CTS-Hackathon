import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import engine

def main():
    query = text("""
    SELECT hcpcs_code 
    FROM ncd_hcpcs_codes
    WHERE ncd_id = '228';
    """)
    with Session(engine) as session:
        for row in session.execute(query).fetchall():
            print(row)

if __name__ == '__main__':
    main()
