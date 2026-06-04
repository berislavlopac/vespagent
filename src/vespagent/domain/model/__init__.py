"""The DomainModel aggregate (CLAUDE.md §4).

Everything for one aggregate lives in its own package: the aggregate root entity, the
value objects it holds, and its repository protocol. Built thin first (CLAUDE.md §9):
so far the event value objects; the `DomainModel` root and its repository follow.
"""

from vespagent.domain.model.events import EventName, ModeledEvent

__all__ = ["EventName", "ModeledEvent"]
