"""Factories — build adapters from typed config (CLAUDE.md §4).

Pure construction logic: given a config, return the matching port implementation
(role adapters, store, renderer, exporter). Mirrors schematalog's `wiring/factories.py`.
To be built together.
"""
