"""NCD service — business logic for NCD-related operations."""
from __future__ import annotations

from app.exceptions.handlers import ResourceNotFoundError
from app.repositories.interfaces.ncd_repository import NCDRepository
from app.schemas.ncd import NCDResponse


class NCDService:
    """Orchestrates NCD retrieval and delegates to the repository."""

    def __init__(self, repository: NCDRepository) -> None:
        self._repo = repository

    def get_ncd(self, ncd_id: str) -> NCDResponse:
        """Return the NCD or raise ``ResourceNotFoundError``."""
        ncd = self._repo.get_by_id(ncd_id.strip().upper())
        if ncd is None:
            raise ResourceNotFoundError(
                f"NCD '{ncd_id}' was not found.",
                details={"ncd_id": ncd_id},
            )
        return ncd
