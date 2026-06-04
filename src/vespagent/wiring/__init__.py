"""Wiring layer — the composition root (CLAUDE.md §4).

Assembles the application from its parts: instantiates the Pydantic AI role adapters,
the store/renderer/exporter, and hands them to the orchestrator. Owns provider selection
(hosted Claude ↔ local OpenAI-compatible endpoint) and configuration. The one place that
knows about every layer.
"""
