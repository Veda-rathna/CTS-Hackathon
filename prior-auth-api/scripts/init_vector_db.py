import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from app.models.base import Base
import app.models  # This imports __init__.py which imports PolicyChunk

def init_db():
    print("Initializing vector database...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    print("Created vector extension.")
    
    # Create all tables (will only create missing ones, like policy_chunks)
    Base.metadata.create_all(bind=engine)
    print("Created policy_chunks table.")

if __name__ == "__main__":
    init_db()
