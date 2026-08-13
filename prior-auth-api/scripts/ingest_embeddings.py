"""Script to ingest policy text from the database, chunk it, generate embeddings, and store in the policy_embeddings table.

This script should be run after the database is seeded and the RAG/LLM
config settings are configured.
"""
from __future__ import annotations

import logging
import sys

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.policy_embedding import PolicyEmbedding
from app.repositories.postgres.article_repository import PostgresArticleRepository
from app.repositories.postgres.lcd_repository import PostgresLCDRepository
from app.repositories.postgres.ncd_repository import PostgresNCDRepository
from app.services.policy_content_service import PolicyContentService
from app.services.rag.chunking_service import ChunkingService
from app.services.rag.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def ingest_policies():
    """Ingest NCDs, LCDs, and Articles into the policy_embeddings table."""
    settings = get_settings()

    # We need actual PostgreSQL database for ingestion,
    # because the mock repository doesn't have the rich text fields.
    if settings.use_mock_repositories:
        logger.error("USE_MOCK_REPOSITORIES must be False to ingest embeddings.")
        sys.exit(1)

    logger.info("Initializing services...")
    db = SessionLocal()
    try:
        ncd_repo = PostgresNCDRepository(db)
        lcd_repo = PostgresLCDRepository(db)
        article_repo = PostgresArticleRepository(db)
        
        content_service = PolicyContentService(ncd_repo, lcd_repo, article_repo, settings)
        chunking_service = ChunkingService()
        embedding_service = EmbeddingService(settings)
        
        # Test model loading early
        embedding_service._load_model()
        
        logger.info("Emptying existing policy_embeddings table...")
        db.query(PolicyEmbedding).delete()
        db.commit()

        # Ingest NCDs
        logger.info("Ingesting NCDs...")
        ncds = db.query(ncd_repo.model_class).distinct(ncd_repo.model_class.document_id).all()
        for ncd in ncds:
            logger.info(f"Processing NCD {ncd.document_id}")
            sections = content_service.get_ncd_sections(ncd.document_id)
            chunks = chunking_service.chunk_sections(sections)
            store_chunks(db, embedding_service, chunks)

        # Ingest LCDs
        logger.info("Ingesting LCDs...")
        lcds = db.query(lcd_repo.model_class).distinct(lcd_repo.model_class.lcd_id).all()
        for lcd in lcds:
            logger.info(f"Processing LCD {lcd.lcd_id}")
            sections = content_service.get_lcd_sections(lcd.lcd_id)
            chunks = chunking_service.chunk_sections(sections)
            store_chunks(db, embedding_service, chunks)

        # Ingest Articles
        logger.info("Ingesting Articles...")
        articles = db.query(article_repo.model_class).distinct(article_repo.model_class.article_id).all()
        for article in articles:
            logger.info(f"Processing Article {article.article_id}")
            sections = content_service.get_article_sections(article.article_id)
            chunks = chunking_service.chunk_sections(sections)
            store_chunks(db, embedding_service, chunks)
            
        logger.info("Ingestion complete.")
    finally:
        db.close()


def store_chunks(db, embedding_service: EmbeddingService, chunks: list):
    """Embed chunks and store them in the database."""
    if not chunks:
        return

    texts = [chunk.content for chunk in chunks]
    try:
        embeddings = embedding_service.embed_texts(texts)
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        return

    records = []
    for chunk, embedding in zip(chunks, embeddings):
        record = PolicyEmbedding(
            policy_type=chunk.policy_type,
            policy_id=chunk.policy_id,
            policy_version=chunk.policy_version or 1,
            section=chunk.section_type,
            chunk_text=chunk.content,
            embedding=embedding,
            effective_date=chunk.effective_date,
            end_date=chunk.end_date,
            jurisdiction_id=chunk.jurisdiction_id,
            contractor_id=chunk.contractor_id,
        )
        records.append(record)

    db.add_all(records)
    db.commit()


if __name__ == "__main__":
    ingest_policies()
