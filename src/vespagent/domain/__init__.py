"""Domain layer — the framework-free core (CLAUDE.md §4).

The app's own ubiquitous language *is* the event-storming vocabulary, so the domain types
mirror it. `base.py` holds the parent classes; each aggregate gets its own package
(`model/` …) containing its root entity, the value objects it holds, and its repository
protocol (a `Protocol`). Imports nothing from infrastructure, presentation, or Pydantic
AI (§7 dependency rule).
"""
