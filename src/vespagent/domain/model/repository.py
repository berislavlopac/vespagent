"""Repository protocol for the DomainModel aggregate (CLAUDE.md §10, 2026-06-05).

A `Protocol` (not an ABC) so infrastructure adapters satisfy it structurally, keeping
the domain free of any import from the infrastructure layer.
"""

from typing import Protocol
from uuid import UUID

from vespagent.domain.model.root import DomainModel


class DomainModelRepository(Protocol):
    """Persistence contract for the `DomainModel` aggregate.

    The infrastructure layer provides a concrete adapter (SQLite, file, in-memory for
    tests). The domain and application layers depend only on this protocol.
    """

    def save(self, model: DomainModel) -> None:  # noqa: F841
        """Persist a new model or overwrite an existing one with the same `id`.

        Args:
            model: The aggregate root to store.
        """
        ...

    def get(self, model_id: UUID) -> DomainModel:
        """Load a model by its stable identity.

        Args:
            model_id: The `UUID` assigned at creation.

        Returns:
            The stored `DomainModel`.

        Raises:
            ModelNotFoundError: If no model with that id has been saved.
        """
        ...

    def exists(self, model_id: UUID) -> bool:
        """Return whether a model with the given id has been saved.

        Args:
            model_id: The id to check.

        Returns:
            `True` if the model is present, `False` otherwise.
        """
        ...
