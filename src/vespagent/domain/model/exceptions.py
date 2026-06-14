"""Exceptions specific to the DomainModel aggregate.

Kept here (not in `domain/exceptions.py`) because they carry `EventName`, which would
create a circular import if placed at the top-level domain package.
"""

from vespagent.domain.exceptions import DomainError
from vespagent.domain.model.events import EventName


class DuplicateEventError(DomainError):
    """Raised when adding an event whose name already exists in the model."""

    def __init__(self, name: EventName) -> None:
        super().__init__(f"event '{name.value}' already exists in this model")
        self.name = name


class EventNotFoundError(DomainError):
    """Raised when looking up an event name that is not in the model."""

    def __init__(self, name: EventName) -> None:
        super().__init__(f"no event named '{name.value}' in this model")
        self.name = name
