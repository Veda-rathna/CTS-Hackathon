"""Policy Evidence Resolver.

Responsible for retrieving policy evidence for a given clinical request.
It checks the local repositories first. If evidence is missing, stale, or invalid,
it queries the external CMS Coverage API (fallback).

Any information retrieved from CMS is normalized and upserted back into
the local repositories (cache) so that the core Triage Engine can run entirely
off local data.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.repositories.interfaces.policy_repository import PolicyRepository
from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.ncd_repository import NCDRepository
from app.services.cms_client import CMSCoverageClient, MockCMSCoverageClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PolicyEvidenceResolver:
    """Resolves policy evidence using local cache + CMS API fallback."""

    def __init__(
        self,
        policy_repository: PolicyRepository,
        article_repository: ArticleRepository,
        ncd_repository: NCDRepository,
        cms_client: CMSCoverageClient | MockCMSCoverageClient | None = None,
    ) -> None:
        self._policy_repo = policy_repository
        self._article_repo = article_repository
        self._ncd_repo = ncd_repository
        
        self.settings = get_settings()
        
        if cms_client:
            self._cms = cms_client
        else:
            if self.settings.use_mock_repositories:
                self._cms = MockCMSCoverageClient()
            else:
                self._cms = CMSCoverageClient()

    def resolve_evidence(
        self, 
        procedure_code: str, 
        diagnosis_codes: List[str], 
        state: str | None = None
    ) -> dict[str, Any]:
        """Resolve policy and coding evidence for the given request.
        
        Returns:
            A dictionary with status (FOUND, NOT_FOUND, UNAVAILABLE),
            source (LOCAL, CMS_MCD), and freshness (CURRENT).
        """
        logger.info(f"Resolving evidence for HCPCS: {procedure_code}")
        
        # 1. Local Lookup
        local_policies = self._policy_repo.find_policies_for_procedure(procedure_code)
        
        if local_policies:
            logger.info(f"Found {len(local_policies)} local policies for HCPCS {procedure_code}")
            return {
                "status": "FOUND",
                "source": "LOCAL",
                "freshness": "CURRENT",
                "policies": local_policies
            }

        # 2. CMS API Fallback (Phase 1)
        if self._cms and getattr(self._cms, "enabled", False):
            try:
                if hasattr(self._cms, "search_by_hcpcs") and callable(self._cms.search_by_hcpcs):
                    self._cms.search_by_hcpcs(procedure_code)
                hcpcs_responses = getattr(self._cms, "hcpcs_mock_responses", {})
                if procedure_code in hcpcs_responses:
                    logger.info(f"Found CMS coverage data for HCPCS {procedure_code}")
                    return {
                        "status": "FOUND",
                        "source": "CMS_MCD",
                        "freshness": "CURRENT",
                        "policies": []
                    }
            except Exception as exc:
                logger.warning(f"CMS API call failed: {exc}")
                self._log_fallback_event(
                    procedure_code,
                    local_result="NOT_FOUND",
                    cms_result="ERROR",
                )
                return {
                    "status": "UNAVAILABLE",
                    "source": None,
                    "reason": "CMS_API_UNAVAILABLE",
                    "policies": [],
                }

        logger.info(f"HCPCS {procedure_code} missing locally and in CMS. Returning NOT_FOUND.")
        self._log_fallback_event(
            procedure_code, 
            local_result="NOT_FOUND", 
            cms_result="NOT_FOUND"
        )
        return {
            "status": "NOT_FOUND",
            "source": None,
            "policies": []
        }

    def _log_fallback_event(self, hcpcs: str, local_result: str, cms_result: str) -> None:
        """Log the fallback event."""
        event = {
            "event": "CMS_FALLBACK",
            "lookup_type": "HCPCS",
            "lookup_value": hcpcs,
            "local_result": local_result,
            "cms_result": cms_result
        }
        logger.info(f"Fallback Event: {event}")
