import pytest
from app.services.cms_client import MockCMSCoverageClient
from app.services.policy_evidence_resolver import PolicyEvidenceResolver
from app.repositories.mock.policy_repository import MockPolicyRepository
from app.repositories.mock.article_repository import MockArticleRepository
from app.repositories.mock.ncd_repository import MockNCDRepository
from app.schemas.policy import PolicyMatch
from app.core.config import get_settings

def test_cms_fallback_local_hit():
    """Test 1 — Everything exists locally"""
    # Setup mock repos
    policy_repo = MockPolicyRepository()
    article_repo = MockArticleRepository()
    ncd_repo = MockNCDRepository()
    cms_client = MockCMSCoverageClient()
    
    # Inject local data
    # (assuming MockPolicyRepository finds 64483)
    resolver = PolicyEvidenceResolver(policy_repo, article_repo, ncd_repo, cms_client)
    
    result = resolver.resolve_evidence("64483", ["M54.16"])
    
    assert result["status"] == "FOUND"
    assert result["source"] == "LOCAL"
    assert result["freshness"] == "CURRENT"
    assert len(result["policies"]) > 0

def test_cms_fallback_local_miss():
    """Test 2 — HCPCS missing locally returns NOT_FOUND."""
    policy_repo = MockPolicyRepository()
    policy_repo.find_policies_for_procedure = lambda x: []
    
    article_repo = MockArticleRepository()
    ncd_repo = MockNCDRepository()
    cms_client = MockCMSCoverageClient()
    
    resolver = PolicyEvidenceResolver(policy_repo, article_repo, ncd_repo, cms_client)
    
    result = resolver.resolve_evidence("99999", ["M54.16"])
    
    assert result["status"] == "NOT_FOUND"
    assert result["reason"] == "POLICY_NOT_FOUND"
    assert result["policies"] == []

