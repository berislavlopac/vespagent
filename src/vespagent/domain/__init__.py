"""Domain layer — the framework-free core (CLAUDE.md §4).

The app's own ubiquitous language *is* the event-storming vocabulary, so the domain types
mirror it. Holds the model (entities with behaviour), the ports (Protocols) the inner
layers depend on, and domain exceptions. Imports nothing from infrastructure, presentation,
or Pydantic AI (§7 dependency rule).
"""
