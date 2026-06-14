"""The DomainModel aggregate (CLAUDE.md §4).

Everything for one aggregate lives in its own package: the aggregate root entity, the
value objects it holds, and its repository protocol.
"""

from vespagent.domain.model.events import EventName, ModeledEvent
from vespagent.domain.model.exceptions import DuplicateEventError, EventNotFoundError
from vespagent.domain.model.repository import DomainModelRepository
from vespagent.domain.model.root import DomainModel, EventAdded, EventDescribed

__all__ = [
    "DomainModel",
    "DomainModelRepository",
    "DuplicateEventError",
    "EventAdded",
    "EventDescribed",
    "EventName",
    "EventNotFoundError",
    "ModeledEvent",
]
