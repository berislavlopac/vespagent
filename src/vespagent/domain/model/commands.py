"""Commands and their names, within the DomainModel aggregate (CLAUDE.md §4).

In event storming, Commands are the intentions or instructions that cause domain events
to happen — named in the imperative form (`PlaceOrder`). Discovering what triggers an
event, and who issues the command, is how the causal structure of the domain emerges.
These are value objects: the mutable aggregate root (`DomainModel`) holds them and
replaces them wholesale on change.
"""

from pydantic import field_validator

from vespagent.domain.base import ValueObject


class CommandName(ValueObject):
    """The imperative-form name of a `Command`, e.g. `PlaceOrder`.

    A type of its own rather than a bare `str` to prevent a name meant for one concept
    being passed where another belongs. Validation is structural only — non-empty,
    trimmed; the imperative-form convention is the Modeler's job and an eval assertion
    (CLAUDE.md §5 L3), not something code can reliably enforce.
    """

    value: str
    """The command name itself, e.g. `PlaceOrder`."""

    @field_validator("value")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:  # noqa: F841
        """Strip surrounding whitespace and reject blank names.

        Args:
            value: The raw name supplied to the field.

        Returns:
            The trimmed name.

        Raises:
            ValueError: If the name is empty or only whitespace.
        """
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("command name must not be blank")
        return cleaned


class Command(ValueObject):
    """A command in the event-storming sense, named in the imperative form (`PlaceOrder`).

    An intention or instruction issued by an actor or triggered by a policy, which causes
    a domain event. A *value object* with no identity of its own: within a `DomainModel`
    it is keyed by its `name`, and a change (e.g. supplying the description) replaces it
    wholesale rather than mutating it.
    """

    name: CommandName
    """The command's imperative-form name; its key within the owning `DomainModel`."""

    description: str | None = None
    """What the command does, in the expert's own words. `None` until explained — the
    model is a legitimately incomplete draft mid-interview, so a description is not
    required."""
