# VESPA — Virtual Event Storming Practitioner Agent

VESPA interviews a domain expert and, through **adaptive** conversation, builds a
structured DDD domain model — domain events, commands, actors, aggregates, policies,
external systems, candidate bounded contexts — plus a ubiquitous-language glossary.

It is a multi-role agent (Facilitator, Modeler, Language Guardian, Boundary Spotter,
optional Challenger) where **only the Facilitator speaks to the human**. Its honest
output is a *domain-validated first draft* that still needs a DDD practitioner's review —
not a verified-correct model.

See [CLAUDE.md](CLAUDE.md) for the full design: the cardinal rule (elicitation must be
adaptive, never a scripted questionnaire), the hexagonal architecture, the testing
strategy, and the build order.

## Architecture

Hexagonal / ports-and-adapters with a framework-free core, laid out as DDD layers:

```
src/vespagent/
├── domain/          # event-storming types + behaviour, ports (Protocols), exceptions
├── application/     # orchestration: the adaptive turn loop / use cases
├── infrastructure/  # adapters: Pydantic AI role agents (ACL), store, render, export
├── presentation/    # CLI now; web board later behind the same ports
├── wiring/          # composition root, config, provider selection
└── common/          # shared, layer-neutral helpers
prompts/             # one versioned prompt file per role
evals/               # scenarios + gold-standard models + scorers + baseline
tests/               # Layer 1 (stubbed-port unit) & Layer 2 (schema) tests
```

The dependency rule: `domain` and `application` import nothing from infrastructure,
presentation, or Pydantic AI. Pydantic AI lives only in `infrastructure/agents` as an
Anti-Corruption Layer.

## Development

Requires Python 3.14, [`uv`](https://docs.astral.sh/uv/), and [`just`](https://github.com/casey/just).

```shell
uv sync          # create the venv and install deps
just             # list available recipes
just check       # lint + safety + type checks
just test        # unit tests with coverage
just ready       # everything (checks + tests)
just chat        # run the VESPA interview (CLI)
```