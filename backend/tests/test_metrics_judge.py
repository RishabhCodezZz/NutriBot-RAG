from unittest.mock import MagicMock

from eval.metrics import judge


class FakeResponse:
    def __init__(self, text):
        self.text = text


def test_extract_int_parses_valid_range():
    assert judge._extract_int("4", 1, 5) == 4
    assert judge._extract_int("Score: 3 out of 5", 1, 5) == 3


def test_extract_int_rejects_out_of_range():
    assert judge._extract_int("9", 1, 5) is None


def test_extract_int_none_when_no_digit():
    assert judge._extract_int("no idea", 1, 5) is None


def test_judge_relevance_parses_valid_score(monkeypatch):
    fake_model = MagicMock()
    fake_model.generate_content.return_value = FakeResponse("4")
    monkeypatch.setattr(judge, "get_judge_model", lambda: fake_model)

    score, raw = judge.judge_relevance("q", "a")
    assert score == 4


def test_judge_relevance_returns_none_on_persistent_failure_not_a_fabricated_default(monkeypatch):
    """Regression test: the original evaluate.py used `except: relevance_score = 3`
    on any parse/API failure, silently injecting a fabricated mid-scale score.
    The rebuilt judge must return None (recorded as an error) instead."""
    fake_model = MagicMock()
    fake_model.generate_content.side_effect = Exception("quota exceeded")
    monkeypatch.setattr(judge, "get_judge_model", lambda: fake_model)
    monkeypatch.setattr(judge.time, "sleep", lambda s: None)  # skip real backoff delay in tests

    score, raw = judge.judge_relevance("q", "a")
    assert score is None
    assert raw.startswith("ERROR")


def test_judge_faithfulness_parses_score_line(monkeypatch):
    fake_model = MagicMock()
    fake_model.generate_content.return_value = FakeResponse(
        "Oats: yes, grounded.\nChicken Breast: no, not in context.\nSCORE: 1/2"
    )
    monkeypatch.setattr(judge, "get_judge_model", lambda: fake_model)

    ratio, raw = judge.judge_faithfulness("context", "answer")
    assert ratio == 0.5


def test_judge_faithfulness_none_on_unparseable_reply(monkeypatch):
    fake_model = MagicMock()
    fake_model.generate_content.return_value = FakeResponse("I'm not sure how to answer that.")
    monkeypatch.setattr(judge, "get_judge_model", lambda: fake_model)

    ratio, raw = judge.judge_faithfulness("context", "answer")
    assert ratio is None


def test_judge_instruction_following_parses_yes_no(monkeypatch):
    fake_model = MagicMock()
    fake_model.generate_content.return_value = FakeResponse("Yes, it does.")
    monkeypatch.setattr(judge, "get_judge_model", lambda: fake_model)

    results = judge.judge_instruction_following("q", "context", "answer")
    assert all(v is True for v in results.values())
    assert set(results.keys()) == {"portion_given", "why_explained", "context_appropriate", "source_only"}
