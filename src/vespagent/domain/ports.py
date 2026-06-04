"""Ports — the Protocols the inner layers depend on (CLAUDE.md §4, §7).

`Protocol` over ABC for every port (structural typing, swappable, testable). Role ports:
Facilitator, Modeler, LanguageGuardian, BoundarySpotter, Challenger. Infrastructure
ports: ModelRenderer, ModelStore, ModelExporter. The application orchestrator depends only
on these abstractions, never on Pydantic AI. Defined in the domain so the dependency arrows
point inward (ports owned by the core, implementations in infrastructure). To be built
together.
"""
