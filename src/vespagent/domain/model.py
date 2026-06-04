"""Domain model — the event-storming vocabulary as Pydantic v2 types (CLAUDE.md §4).

ModeledEvent, Command, Actor, Aggregate, Policy, ExternalSystem, ReadModel,
BoundedContext, GlossaryTerm / UbiquitousLanguage, Ambiguity / Inconsistency, the
DomainModel aggregate root, and Session.

Entities must carry behaviour (methods that enforce invariants) — no anemic models
(CLAUDE.md §7, §11). To be built together.
"""
