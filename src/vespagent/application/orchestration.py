"""Orchestration — the turn loop and next-move logic (CLAUDE.md §2, §4).

The control flow is owned by the model's reading of accumulated state, never a fixed
questionnaire (the cardinal rule, §2). Coordinates the role ports and decides the next
move (dig deeper / resolve an ambiguity / reflect back / move on). Fully testable with
stubbed ports (Layer 1, §5). To be built together.
"""
