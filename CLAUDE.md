# CLAUDE.md — VESPA (Virtual Event Storming Practitioner Agent)

> Living guide for this project. It records what we're building, how it's
> architected, the engineering rules, and the testing strategy — and it **evolves**:
> append new conventions and decisions to §10 as we make them, ADR-style.

---

## 1. What this is

**VESPA** — a **virtual event-storming practitioner**: an agent that interviews a domain expert
and, through adaptive conversation, builds a structured domain model — domain events,
commands, actors, aggregates, policies, external systems, candidate **bounded
contexts**, and a **ubiquitous language** glossary.

Two goals, in priority order:

1. **A learning vehicle** — to practise building a real agent (not a workflow),
   under strict DDD + testing discipline. Rigor matters more than feature count.
2. **A specialised tool** — more focused than a general coding agent, producing an
   artifact (a domain model + glossary) that can later feed downstream schema/codegen
   tooling.

It is **not** an oracle. Its honest output is a *domain-validated first draft* that
still needs a DDD practitioner's review (see §6, the verifier split).

---

## 2. The cardinal rule (do not violate)

**Elicitation must be adaptive, never a fixed questionnaire.** The next question must
depend on what the expert just said — pulling on a thread, probing an ambiguity,
challenging a term. A scripted "now list your events, now your commands" sequence is a
*workflow wearing a DDD costume*, not an agent, and defeats the entire purpose. If a
step can be drawn on a flowchart in advance, it's wrong here.

This is the property that makes the project agentic: the **control flow is owned by
the model's reading of accumulated state**, not pre-scripted.

---

## 3. Functionality

- **Multi-role, single interface.** Several specialist roles operate, but **only the
  Facilitator speaks to the human.** The others work behind the scenes and surface
  findings *to the Facilitator*, which decides whether/when to raise them. Never make
  the expert field multiple chatbots at once.
- **Roles** (each a distinct, separately-framed model call — see §4):
  - **Facilitator** — drives the conversation, decides the next move (dig deeper /
    resolve a flagged ambiguity / reflect back / move to a new area), asks the single
    next question.
  - **Modeler** — extracts and updates structured artifacts from the expert's answers.
  - **Language Guardian** — watches the ubiquitous language; flags where one term
    means two things (e.g. "customer" in sales vs. billing) or two terms mean one.
  - **Boundary Spotter** — watches for emerging bounded-context seams and coupling.
  - **Challenger** *(optional, later)* — probes edge cases and contradictions; partly
    compensates for the missing cross-examination of a single-expert session; acts as
    a soft verifier.
- **Reflect-and-confirm loop.** Periodically the Facilitator shows the current model
  back to the expert and asks "have I got this right?" This is both UX and the primary
  correctness check (§6).
- **Live model rendering.** The evolving model is rendered as a diagram (Mermaid to
  start) so the expert can *see* it. Event storming is spatial; this is core, not
  decoration.
- **Persistence & export.** Sessions and models persist (resume a session). The model
  exports as structured JSON intended to feed downstream schema/codegen tooling.

---

## 4. Architecture

**Hexagonal / ports-and-adapters, with a framework-free domain core.** The project is
*about* DDD, so it is built with DDD.

### The core is a model of event storming itself

The app's own ubiquitous language **is** the event-storming vocabulary. Core domain
types (Pydantic v2), roughly:

- `ModeledEvent` (past-tense domain event, e.g. `OrderPlaced`) — named to avoid
  collision with messaging "domain events".
- `Command`, `Actor`, `Aggregate`, `Policy` (reactive "whenever X then Y"),
  `ExternalSystem`, optional `ReadModel`.
- `BoundedContext` (a cluster + its boundary + rationale).
- `GlossaryTerm` (term → definition, owning context, ambiguity flags) and the
  `UbiquitousLanguage` collection.
- `Ambiguity` / `Inconsistency` (flagged issues awaiting resolution).
- `DomainModel` — the aggregate root holding all of the above; the evolving artifact.
- `Session` — an interview session: transcript, state, link to its `DomainModel`.

Domain entities **carry behaviour** (methods that enforce invariants). Avoid anemic
models — this is doubly important because the app teaches the opposite.

### Ports (Protocols — the core depends only on these)

- Role ports: `Facilitator`, `Modeler`, `LanguageGuardian`, `BoundarySpotter`,
  `Challenger`. The orchestrator depends on these abstractions, **not** on Pydantic AI.
- `ModelRenderer` — render a `DomainModel` to a view (Mermaid now; **web board later**
  via a second adapter — keep this port stable so the UI can change without touching
  core).
- `ModelStore` — persist/load `Session` and `DomainModel`.
- `ModelExporter` — emit JSON / downstream formats.

### Adapters (depend on core; never the reverse)

- **Pydantic AI agents** implement the role ports. This is the only place the
  framework is imported. Treat it as an Anti-Corruption Layer: Pydantic AI types do not
  leak into the core.
- **CLI** adapter — the interface for now (chat in, model + diagram out).
- **Mermaid renderer** adapter.
- **SQLite / file** store adapter.
- **JSON exporter** adapter.

### Provider-agnostic LLM access

Pydantic AI already abstracts model providers, so "both behind a protocol" is honoured
at two levels: (1) provider swap (**hosted Claude** ↔ **local model** via an
OpenAI-compatible endpoint such as Ollama/vLLM) is configuration inside the Pydantic AI
adapter; (2) the **role-port boundary** keeps the domain clean of framework types and
is what enables deterministic testing (§5). Default config selects the provider; the
core neither knows nor cares which model answered.

### The model is the memory

The evolving `DomainModel` is the primary durable state and is *itself a compression*
of the conversation. So context management leans on "current structured model + recent
turns + open ambiguities", not on heavy transcript summarisation. Don't over-engineer
transcript compaction; the artifact already holds the distilled state.

---

## 5. Testing strategy & boundaries

We **do not** recover deterministic end-to-end assurance — the model is
non-deterministic by construction. Instead we **partition** the system so determinism
survives where it can and is replaced by the right non-deterministic instrument where
it can't.

### The boundary

- **Deterministic side (≈70–80% of the code):** orchestrator logic, state transitions,
  context/compaction policy, retry-on-validation-failure, persistence, rendering,
  export. Test exactly as normal — fast unit tests in CI. Stub the **role ports** with
  canned outputs; the orchestrator never needs a real model to be tested.
- **Model-shaped side:** the role adapters' actual judgement. Tested with the three
  instruments below, none of which assert "correct".

### Layer 1 — Deterministic unit tests (plumbing)
Stub the role-port Protocols with fixtures. Assert the loop advances state correctly,
retries on a `ValidationError`, compacts at the right threshold, persists/loads
round-trip, renders, exports. This is where your engineering instinct fully applies.

### Layer 2 — Schema-level validation (free determinism)
Every role output is a Pydantic model, so "did it parse and validate" is a
deterministic check even though content varies. Test the Pydantic AI adapters using
**Pydantic AI's built-in test models** (e.g. `TestModel` / `FunctionModel` and
`Agent.override()` — verify exact API against current Pydantic AI docs) to return
canned and edge-case structures without real LLM calls.

### Layer 3 — Evals (this replaces the deterministic E2E suite)
A curated, version-controlled set of ~15–30 scenarios: described domains with known
characteristics and **planted** features (a deliberate "customer means two things"
ambiguity; an obvious context seam). Score each output three ways:
- **Deterministic assertions** — ≥1 bounded context produced; every event has a
  command/actor; the planted ambiguity was flagged. (Plain code.)
- **Reference overlap** — similarity to a hand-written gold-standard model.
- **Validated LLM-as-judge** — a *separate* model call scoring against a written rubric
  (e.g. "rate 1–5 whether bounded contexts are cohesive and boundaries justified").

**CI gates on regression against a baseline score, not absolute pass.** Establish a
baseline; fail the build when a prompt/model change drops the suite materially (e.g.
82% → 71%). Run evals at **temperature 0** for stability.

### Layer 4 — Production tracing feeds the eval set
Wire tracing (Logfire) from the start. Failures and weird cases found in real runs
become **new eval scenarios**. The eval suite is a living artifact that grows from
production — that becomes the real regression net over time.

### Layer 5 — Human-in-the-loop as runtime verifier
The reflect-and-confirm step is a continuous correctness check executed by the one
verifier who knows the domain. See §6 for what it can and cannot verify.

### LLM-as-judge discipline
Before trusting a judge: hand-score ~20 outputs, have the judge score the same 20, and
only trust it on the axes where it agrees with you. The judge is a **tested component**,
not an authority.

---

## 6. The verifier split (read before believing any output)

- **Domain facts** — the expert is a genuine, *native* verifier ("no, the warehouse can
  reject after acceptance"). Reliable; built into the technique.
- **Modeling quality** — **no automatic oracle exists**, and the domain expert (not a
  software modeler) cannot judge whether a bounded context is well-drawn or an aggregate
  cohesive. The only real check is a DDD practitioner reviewing the output.

Therefore **definition of done = a domain-fact-validated draft, reviewed by a DDD
practitioner for modeling soundness** — never "a verified-correct model".

---

## 7. Engineering conventions

- **Python 3.14**; `uv` for deps/run; `just` for tasks; `ruff` for lint/format.
- **Full type hints**; strict type checking (`pyright`/`mypy --strict` or `ty`/`pyrefly`).
- **`Protocol` over ABC** for every port (structural typing, swappable, testable).
- **Pydantic v2** for all domain types and role I/O — the model is contract +
  validator + type.
- **Dependency rule:** `core` (domain + ports) imports nothing from adapters, the CLI,
  or Pydantic AI. Adapters depend on core, never the reverse.
- **Prompts live in versioned files** at `src/vespagent/prompts/`, one per role; treat as
  source. Loaded at import time via `importlib.resources` so they are always co-located
  with the package and included in the build automatically.
- **Each role is its own framed call.** Never merge roles into one mega-prompt — the
  separation is what keeps the Language Guardian's vigilance from being diluted.
- **Role context scoping is deliberate.** Give each role only what it needs; do not
  "helpfully" widen a role's context. Comment why a context is intentionally narrow.
- **Commits carry no AI authorship trailer.** Do not add `Co-Authored-By` or any
  "authored by" / "generated with" line to commit messages.

---

## 8. Suggested project structure

```
vespagent/
├── pyproject.toml           # Python 3.14; uv-managed
├── justfile
├── src/vespagent/
│   ├── domain/              # base classes + one package per aggregate (model/, …)
│   ├── application/         # orchestration: the adaptive turn loop / use cases
│   ├── infrastructure/
│   │   ├── agents/          # Pydantic AI role adapters (ACL — only place PA is imported)
│   │   ├── store/           # SQLite/file persistence
│   │   ├── render/          # Mermaid renderer
│   │   └── export/          # JSON exporter
│   ├── presentation/        # CLI now; web board later behind the same protocols
│   ├── prompts/             # one versioned prompt file per role (loaded via importlib.resources)
│   ├── common/              # shared utilities
│   └── wiring/              # composition root + config + provider selection
├── evals/                   # scenarios + gold-standard models + scorers + baseline
└── tests/                   # Layer 1 & 2
```

---

## 9. Build order (thin vertical slice first)

1. Core types + ports + an orchestrator driven by **stubbed** role ports → Layer-1
   tests green. No LLM yet.
2. **Facilitator + Modeler** as Pydantic AI agents; everything in context; no other
   roles. One good interview turn: ask → answer → model updates; CLI prints the model.
   Stop and judge quality before going on.
3. **Reflect-and-confirm** loop (human verifier).
4. **Loop it** — multi-turn, adaptive next-question (the agentic core). Watch it pull
   on threads rather than march a script.
5. Add **Language Guardian + Boundary Spotter** (behind the scenes → Facilitator).
6. Add **diagram rendering** (Mermaid).
7. Add **persistence + export**.
8. Stand up the **eval harness** (§5 Layer 3) with ~5 scenarios + baseline; wire CI.
9. Add **tracing** (Layer 4); optional **Challenger**.
10. *(Future)* web-board interface adapter via the existing `ModelRenderer`/interface
    ports — no core changes.

---

## 10. Conventions & decisions log (append here as we go)

> Format: `YYYY-MM-DD — decision — rationale`.

- (init) — Name: **VESPA** = **V**irtual **E**vent **S**torming **P**ractitioner
  **A**gent. "Practitioner" deliberately echoes the DDD sense (and the magic
  practitioners of *Rivers of London*): skilled at the craft, not an unquestioned
  authority — consistent with the §6 verifier ceiling. PyPI/import name `vespagent`
  (bare `vespa` is taken; `vespagent` is a vespa+agent portmanteau, single token,
  no clash with `pyvespa`).
- (init) — Orchestration on **Pydantic AI** — typed agents, less plumbing; kept behind
  role-port ACL so the core stays framework-free.
- (init) — Interface: **CLI + Mermaid** first, web board deferred behind a stable
  renderer/interface port.
- (init) — **Provider-agnostic** from day one (hosted Claude ↔ local GPU model) via
  Pydantic AI model config.
- (init) — Testing gates on **eval regression vs. baseline**, not absolute correctness.
- 2026-06-04 — **Layered package layout** (refines §8): adopt explicit DDD layers —
  `domain/` (model + ports + exceptions), `application/` (orchestration/use cases),
  `infrastructure/{agents,store,render,export}/`, `presentation/` (CLI), `wiring/`
  (composition root + config + provider selection), `common/` — instead of §8's flatter
  `core/ + sibling adapters`. Rationale: same hexagonal mandate as §4, but consistent
  with the sibling `schematalog` project, and adds an explicit `application`/`domain`
  split and a composition root the agent app needs. Ports stay **Protocols** (§7), placed
  in `domain/` so dependency arrows point inward. `src/` layout; installable package
  (hatchling) with a `vespa` console script.
- 2026-06-04 — **Tooling** mirrored from `schematalog`: `uv` + `just`; `ruff` (lint +
  format), `pyrefly` (types), `deptry` (deps), `pytest` + `pytest-cov` + `pytest-spec`;
  `uvx vulture/radon/complexipy` for safety. Recipes: `just check` / `test` / `ready`.
- 2026-06-05 — **Domain code organisation**: the base classes
  (`DomainObject` → `ValueObject`, `Entity`, `DomainEvent`) live in `domain/base.py`. Each
  aggregate is its own package under `domain/` (e.g. `domain/model/` for the `DomainModel`
  aggregate), holding its root entity, the value objects it owns, and its **repository**
  protocol. **Drop the word "port"**: persistence protocols are per-aggregate
  `<Aggregate>Repository` `Protocol`s defined in the aggregate's package; role / renderer /
  exporter protocols keep concrete names (role-protocol home still TBD). "Sticky note" is
  not a domain term. Names are single-field `ValueObject`s — no `RootModel`.
- 2026-06-05 — **Lint conventions**: ignore `TRY003` (contextual messages in Pydantic
  validators / domain errors are intentional). Silence vulture false-positives with an
  inline `# noqa: F841` (ruff lists `F841` under `external`), never a `[tool.vulture]` block.
- 2026-06-14 — **Role protocols** are named with a `Role` suffix: `FacilitatorRole`,
  `ModelerRole`, `LanguageGuardianRole`, `BoundarySpotterRole`, `ChallengerRole`. The
  suffix makes the protocol nature explicit at the call site without requiring the reader
  to know which module they came from.
- 2026-06-14 — **Spelling**: US spelling throughout (code *and* docs), including domain
  terms that become identifiers (e.g. `Modeler`, not `Modeller`). The usual UK/US
  code-vs-prose split breaks down when domain vocabulary is simultaneously identifiers and
  documentation — the code spelling wins everywhere for consistency.
- 2026-06-14 — **Aggregate-specific exceptions** live in their aggregate package
  (e.g. `domain/model/exceptions.py`), not in the top-level `domain/exceptions.py`.
  Reason: exceptions that carry aggregate value objects (e.g. `EventName`) would create a
  circular import if placed at the top level, because `domain/exceptions.py` would import
  from `domain/model/`, which in turn imports from `domain/exceptions.py`. Top-level
  `domain/exceptions.py` is reserved for cross-cutting errors (`DomainError` base,
  `ModelNotFoundError`) that carry no aggregate-specific types.
- 2026-06-14 — **Prompts moved inside the package** to `src/vespagent/prompts/`, loaded
  via `importlib.resources.files("vespagent.prompts").joinpath("role.md").read_text()`.
  Rationale: prompts are package data, not repository-level artefacts — they should be
  co-located with the code that uses them, versioned together, and included in the build
  automatically without extra `[tool.hatchling]` config.
- …add new rules here as they emerge…

---

## 11. For the next agent working on this repo

Context you need that isn't obvious, and mistakes you'll make without it:

- **You will be tempted to build a scripted DDD questionnaire. Don't** — see §2. The
  value is adaptive elicitation; a fixed sequence silently turns this into a workflow.
- **Don't let `core` import Pydantic AI** (or the CLI). The framework is an adapter
  behind the role ports — that ACL is the point, and it's what makes testing possible.
- **Don't collapse the roles into one prompt.** The Language Guardian and Boundary
  Spotter exist as separate calls so their vigilance is structural, not optional.
- **Don't write deterministic assertions on model *content*** and expect them to pass —
  that way lies frustration. Content correctness lives in the eval suite (§5 L3); only
  *structure* is deterministically checkable (§5 L2).
- **Don't produce anemic domain models.** Behaviour goes on entities. The app teaches
  DDD; the codebase must embody it.
- **Don't surface every role's output to the human.** One voice (Facilitator) only.
- **Don't over-engineer transcript summarisation** — the `DomainModel` artifact is the
  memory (§4).
- **Don't claim the output is correct.** It's a domain-validated draft pending DDD
  review (§6).
