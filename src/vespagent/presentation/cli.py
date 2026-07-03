"""CLI adapter — chat in, model out (CLAUDE.md §3, §4, §9 step 2).

A minimal read-eval loop: ask for a domain, run the orchestrator, print the
Facilitator's questions, show the evolving model after each turn. Only the
Facilitator speaks; the Modeler works silently in the background.
"""

import asyncio

from vespagent.application.orchestration import Orchestrator
from vespagent.domain.session import Session
from vespagent.wiring.factories import create_orchestrator


def _print_model(session: Session) -> None:
    model = session.domain_model
    events = list(model.events) or ["(none yet)"]
    commands = list(model.commands) or ["(none yet)"]
    print()
    print("  ┌─ Domain model ──────────────────────────────")
    print(f"  │  Events:   {', '.join(events)}")
    print(f"  │  Commands: {', '.join(commands)}")
    print("  └─────────────────────────────────────────────")
    print()


async def _run(orchestrator: Orchestrator) -> None:
    print()
    subject = input("What domain are we exploring today? ").strip()
    if not subject:
        print("No subject given — exiting.")
        return

    print("\nStarting session…\n")
    question, session = await orchestrator.start(subject)

    while True:
        print(f"VESPA: {question}\n")
        try:
            answer = input("You: ").strip()
        except EOFError, KeyboardInterrupt:
            print("\n\nSession ended.")
            break

        if not answer:
            print("(empty response — ending session)")
            break

        question = await orchestrator.turn(answer, session)
        _print_model(session)

    print("\nFinal model:")
    _print_model(session)


def main() -> None:
    """Entry point for the `vespa` console script."""
    print("VESPA — Virtual Event Storming Practitioner Agent")
    print("─" * 50)
    orchestrator = create_orchestrator()
    try:
        asyncio.run(_run(orchestrator))
    except KeyboardInterrupt:
        print("\nBye.")
