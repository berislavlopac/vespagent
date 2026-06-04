"""Pydantic AI role adapters — the Anti-Corruption Layer (CLAUDE.md §4, §7, §11).

The *only* place Pydantic AI is imported. Each role is its own framed call against a
versioned prompt in `prompts/`; roles are never merged into one mega-prompt. Pydantic AI
types must not leak into the core. Provider choice is handled in wiring. To be built
together.
"""
