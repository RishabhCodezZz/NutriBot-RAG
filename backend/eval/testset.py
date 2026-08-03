"""Load and validate backend/test_cases.json into typed TestCase objects."""
import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "test_cases.json"


@dataclass
class Turn:
    role: str
    text: str


@dataclass
class TestCase:
    id: str
    category: str
    question: str
    lang: str = "en"
    question_en_reference: str = None
    history: list = field(default_factory=list)
    must_include: list = field(default_factory=list)
    forbidden_foods: list = field(default_factory=list)
    gold_doc_ids: list = field(default_factory=list)
    expect_decline: bool = False
    is_injection: bool = False
    notes: str = ""


def load_test_cases(path=None) -> list:
    path = path or DEFAULT_PATH
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    seen_ids = set()
    cases = []
    for r in raw:
        if r["id"] in seen_ids:
            raise ValueError(f"duplicate test case id: {r['id']}")
        seen_ids.add(r["id"])
        history = [Turn(**t) for t in r.get("history", [])]
        cases.append(TestCase(
            id=r["id"],
            category=r["category"],
            question=r["question"],
            lang=r.get("lang", "en"),
            question_en_reference=r.get("question_en_reference"),
            history=history,
            must_include=r.get("must_include", []),
            forbidden_foods=r.get("forbidden_foods", []),
            gold_doc_ids=r.get("gold_doc_ids", []),
            expect_decline=r.get("expect_decline", False),
            is_injection=r.get("is_injection", False),
            notes=r.get("notes", ""),
        ))
    return cases


def history_to_text(history: list, max_turns: int) -> str:
    lines = []
    for t in history:
        prefix = "User" if t.role == "user" else "AI"
        lines.append(f"{prefix}: {t.text}")
    return "\n".join(lines[-max_turns:])
