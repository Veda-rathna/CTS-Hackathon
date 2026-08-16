"""
Unified Database Setup Script.

Performs complete database setup in one execution:
1. Installs pgvector extension & creates tables
2. Seeds database with CMS policies (NCDs, LCDs, Articles, Contractors, Jurisdictions, States)
3. Ingests NCD/LCD document chunks and embeds them into pgvector (384d vector space)
4. Validates table row counts

Usage:
    python scripts/db_setup.py
"""
from __future__ import annotations
import os
import sys
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import engine
from app.models.base import Base
import app.models  # registers ORM models
from app.models.ncd import NCD
from app.services.rag.document_processor import DocumentProcessor
from app.services.rag.embedding_service import EmbeddingService
from app.repositories.policy_chunk_repository import PolicyChunkRepository
from scripts.seed_db import main as seed_cms_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_setup")


def init_vector_db():
    print("\n[1/4] Initializing pgvector extension & database tables...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    Base.metadata.create_all(bind=engine)
    print("      [OK] Created pgvector extension and ORM tables.")


def seed_database():
    print("\n[2/4] Seeding database with CMS policies...")
    seed_cms_data()
    print("      [OK] CMS data seeded successfully.")


def ingest_rag_chunks():
    print("\n[3/4] Ingesting NCD & LCD policy chunks into pgvector...")
    embedding_service = EmbeddingService()

    with Session(engine) as session:
        repo = PolicyChunkRepository(session)
        ncds = session.query(NCD).all()
        print(f"      Found {len(ncds)} NCDs to chunk & embed.")

        all_chunks = []
        for ncd in ncds:
            chunks = DocumentProcessor.chunk_ncd(ncd)
            all_chunks.extend(chunks)

        if all_chunks:
            print(f"      Generated {len(all_chunks)} chunks. Generating embeddings...")
            texts = [c["chunk_text"] for c in all_chunks]
            embeddings = embedding_service.embed_batch(texts)

            for i, chunk_data in enumerate(all_chunks):
                chunk_data["embedding"] = embeddings[i]
                chunk_data["chunk_metadata"] = chunk_data.pop("metadata", None)

            repo.add_chunks(all_chunks)
            session.commit()
            print(f"      [OK] Successfully stored {len(all_chunks)} embedded chunks in pgvector.")
        else:
            print("      No NCD chunks to ingest.")


def validate_database():
    print("\n[4/4] Validating database table counts...")
    tables = [
        'ncds', 'ncd_hcpcs_codes',
        'lcds', 'lcd_hcpcs_codes', 'lcd_icd10_covered', 'lcd_icd10_noncovered',
        'articles', 'article_hcpcs', 'article_icd10_covered', 'article_icd10_noncovered',
        'states', 'jurisdictions', 'contractors',
        'policy_chunks'
    ]
    with engine.begin() as conn:
        for t in tables:
            try:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                print(f"      Table {t:24s} : {res:6d} rows")
            except Exception as e:
                print(f"      Table {t:24s} : Error ({e})")


def run_all():
    print("=" * 65)
    print("          UNIFIED PRIOR AUTH DATABASE SETUP")
    print("=" * 65)
    init_vector_db()
    seed_database()
    ingest_rag_chunks()
    validate_database()
    print("\n" + "=" * 65)
    print("  DB SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    run_all()
