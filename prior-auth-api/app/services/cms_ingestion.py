import logging
from typing import Any, Dict

from app.services.cms_client import CMSCoverageClient
from app.services.cms_normalizer import CMSNormalizer
from app.repositories.interfaces.policy_repository import PolicyRepository

logger = logging.getLogger(__name__)

class CMSIngestionService:
    def __init__(self, cms_client: CMSCoverageClient, policy_repo: PolicyRepository) -> None:
        self.cms_client = cms_client
        self.policy_repo = policy_repo

    def ingest_document(self, document_id: str) -> bool:
        """
        Fetch a document from CMS, normalize it, and persist it to PostgreSQL.
        Returns True if successful, False otherwise.
        """
        logger.info(f"Ingesting CMS document: {document_id}")
        
        try:
            raw_response = self.cms_client.get_document(document_id)
            if not raw_response or not raw_response.get("data"):
                logger.warning(f"No data returned from CMS for document {document_id}")
                return False
                
            # CMS API usually returns a list of items; we process the first one for the requested document
            cms_item = raw_response["data"][0]
            
            normalized_data = CMSNormalizer.normalize_document(cms_item, document_id)
            
            logger.info(f"Successfully normalized {document_id} into {normalized_data['type']} model.")
            
            self.policy_repo.upsert_policy(normalized_data)
            
            logger.info(f"Successfully persisted {document_id} to PostgreSQL.")
            return True
            
        except Exception as e:
            logger.error(f"Error during ingestion of {document_id}: {e}", exc_info=True)
            return False
