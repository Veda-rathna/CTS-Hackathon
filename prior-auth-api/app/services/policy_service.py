"""Policy service — business logic for policy search."""
from __future__ import annotations

from datetime import date

from app.repositories.interfaces.policy_repository import PolicyRepository
from app.schemas.policy import PolicyMatch, PolicySearchResponse


class PolicyService:
    """Orchestrates cross-entity policy search."""

    def __init__(self, repository: PolicyRepository) -> None:
        self._repo = repository

    def search(
        self,
        procedure_code: str,
        diagnosis_code: str | None = None,
        state: str | None = None,
        payer: str | None = None,
        policy_type: str | None = None,
        effective_date: date | None = None,
    ) -> PolicySearchResponse:
        """Search policies and return a structured response with match flags."""
        matches: list[PolicyMatch] = self._repo.search(
            procedure_code=procedure_code.strip().upper(),
            diagnosis_code=diagnosis_code.strip().upper() if diagnosis_code else None,
            state=state.strip().upper() if state else None,
            payer=payer,
            policy_type=policy_type,
            effective_date=effective_date,
        )
        return PolicySearchResponse(matches=matches, total=len(matches))
