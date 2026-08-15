"""Abstract interface (Protocol) for the Policy repository.

The policy repository aggregates cross-entity search logic so that the
triage engine can query all relevant policy types through a single interface.
"""
from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable, Any

from app.schemas.policy import PolicyMatch


@runtime_checkable
class PolicyRepository(Protocol):
    """Cross-entity policy search operations."""

    def search(
        self,
        procedure_code: str,
        diagnosis_code: str | None = None,
        state: str | None = None,
        payer: str | None = None,
        policy_type: str | None = None,
        effective_date: date | None = None,
    ) -> list[PolicyMatch]:
        """Search for policies matching the given criteria.

        At minimum ``procedure_code`` must be supplied.
        All other parameters are optional filters.
        """
        ...

    def find_policies_for_procedure(self, procedure_code: str) -> list[PolicyMatch]:
        """Return all active policies that reference the given procedure code."""
        ...

    def is_state_in_jurisdiction(self, state: str, policy: PolicyMatch) -> bool:
        """Check if a state falls within the policy's jurisdiction."""
        ...

    def upsert_policy(self, normalized_data: dict[str, Any]) -> None:
        """Upsert normalized policy data (LCD, Article, etc.) into the repository."""
        ...
