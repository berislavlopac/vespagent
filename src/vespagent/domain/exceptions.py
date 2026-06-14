"""Domain exceptions (CLAUDE.md §4).

Cross-cutting errors expressed in the language of the domain, independent of any
framework. Aggregate-specific errors (e.g. `DuplicateEventError`) live in their own
aggregate package to avoid circular imports; they all inherit from `DomainError` here.
"""


class DomainError(Exception):
    """Base for all domain-layer errors."""


class ModelNotFoundError(DomainError):
    """Raised by a `DomainModelRepository` when no model with the requested id exists."""

    def __init__(self, model_id: object) -> None:
        super().__init__(f"no domain model with id '{model_id}'")
        self.model_id = model_id
