# Evals (CLAUDE.md §5 Layer 3)

This replaces a deterministic end-to-end suite. A curated, version-controlled set of
~15–30 scenarios: described domains with known characteristics and **planted** features
(a deliberate "customer means two things" ambiguity; an obvious context seam).

Each output is scored three ways:

- **Deterministic assertions** — ≥1 bounded context produced; every event has a
  command/actor; the planted ambiguity was flagged. (Plain code.)
- **Reference overlap** — similarity to a hand-written gold-standard model.
- **Validated LLM-as-judge** — a *separate* model call scoring against a written rubric.

CI gates on **regression against a baseline score**, not absolute pass. Evals run at
**temperature 0** for stability. Stand this up in build-order step 8 with ~5 scenarios +
a baseline; grow it from production traces (Layer 4).

Planned layout: `scenarios/`, `gold/` (gold-standard models), `scorers/`, `baseline.json`.

_To be built together._