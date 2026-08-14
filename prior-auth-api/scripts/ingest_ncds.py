import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.ncd import NCD
from app.services.rag.document_processor import DocumentProcessor
from app.services.rag.embedding_service import EmbeddingService
from app.repositories.policy_chunk_repository import PolicyChunkRepository

def ingest_ncds():
    print("Starting NCD ingestion...")
    embedding_service = EmbeddingService()
    
    with Session(engine) as session:
        repo = PolicyChunkRepository(session)
        ncds = session.query(NCD).all()
        print(f"Found {len(ncds)} NCDs to ingest.")
        
        all_chunks = []
        for ncd in ncds:
            chunks = DocumentProcessor.chunk_ncd(ncd)
            all_chunks.extend(chunks)
            
        print(f"Generated {len(all_chunks)} chunks. Embedding now...")
        
        texts = [c["chunk_text"] for c in all_chunks]
        embeddings = embedding_service.embed_batch(texts)
        
        for i, chunk_data in enumerate(all_chunks):
            chunk_data["embedding"] = embeddings[i]
            chunk_data["chunk_metadata"] = chunk_data.pop("metadata", None)
            
        print(f"Adding {len(all_chunks)} chunks to DB...")
        repo.add_chunks(all_chunks)
        session.commit()
        print("Done!")

if __name__ == "__main__":
    ingest_ncds()
