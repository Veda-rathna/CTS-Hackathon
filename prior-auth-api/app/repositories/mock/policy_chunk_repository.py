from typing import List
from app.models.policy_chunk import PolicyChunk

class MockPolicyChunkRepository:
    def search_similar(self, query_embedding: List[float], policy_type: str, candidate_policy_ids: List[str], top_k: int = 5, threshold: float = 0.5) -> List[PolicyChunk]:
        return []
