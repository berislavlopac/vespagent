"""Infrastructure layer — adapters implementing the domain ports (CLAUDE.md §4).

Depends on the core, never the reverse. Houses the Pydantic AI role adapters (the only
place the framework is imported), persistence, rendering, and export.
"""
