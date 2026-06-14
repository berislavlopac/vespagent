"""Layer-1 tests for the Session aggregate."""

from vespagent.domain.model import DomainModel
from vespagent.domain.session import Session, SessionState, Turn


def _session() -> Session:
    return Session(domain_model=DomainModel(subject="order fulfilment"))


class TestSessionCreation:
    def test_assigns_a_uuid_id(self):
        assert _session().id is not None

    def test_each_session_gets_a_unique_id(self):
        assert _session().id != _session().id

    def test_stores_domain_model(self):
        model = DomainModel(subject="returns")
        assert Session(domain_model=model).domain_model is model

    def test_starts_active(self):
        assert _session().state == SessionState.ACTIVE

    def test_starts_with_empty_transcript(self):
        assert _session().turn_count == 0


class TestTranscript:
    def test_record_expert_turn_returns_a_turn(self):
        turn = _session().record_expert_turn("Something happened.")
        assert isinstance(turn, Turn)

    def test_expert_turn_has_correct_speaker(self):
        assert _session().record_expert_turn("text").speaker == "expert"

    def test_expert_turn_stores_content(self):
        assert _session().record_expert_turn("Something.").content == "Something."

    def test_facilitator_turn_has_correct_speaker(self):
        assert _session().record_facilitator_turn("Question?").speaker == "facilitator"

    def test_facilitator_turn_stores_content(self):
        assert _session().record_facilitator_turn("Question?").content == "Question?"

    def test_turns_accumulate_in_order(self):
        session = _session()
        session.record_facilitator_turn("First question?")
        session.record_expert_turn("First answer.")
        session.record_facilitator_turn("Second question?")
        assert session.turn_count == 3
        assert session.transcript[0].speaker == "facilitator"
        assert session.transcript[1].speaker == "expert"
        assert session.transcript[2].speaker == "facilitator"


class TestIdentity:
    def test_same_id_means_equal(self):
        session = _session()
        same = Session(id=session.id, domain_model=DomainModel(subject="other"))
        assert session == same

    def test_different_ids_means_not_equal(self):
        assert _session() != _session()

    def test_hashable_and_usable_in_a_set(self):
        session = _session()
        assert session in {session}

    def test_not_equal_to_non_session(self):
        assert _session() != "not a session"
