import rag
from eval.metrics import grounding


def _vocab():
    return grounding.load_vocab()


def test_hallucinated_food_rate_flags_food_outside_context():
    context_docs = [
        rag.RetrievedDoc(doc_id="food_35", text="Oats are a food item...", metadata={"title": "Oats"}),
        rag.RetrievedDoc(doc_id="food_55", text="Egg White is a food item...", metadata={"title": "Egg White"}),
    ]
    answer = "I recommend Oats (1 cup) and Chicken Breast (100g) for your breakfast."
    rate, mentioned, hallucinated = grounding.hallucinated_food_rate(answer, context_docs, _vocab())
    assert mentioned == {"Oats", "Chicken Breast"}
    assert hallucinated == {"Chicken Breast"}
    assert rate == 0.5


def test_hallucinated_food_rate_zero_when_all_grounded():
    context_docs = [rag.RetrievedDoc(doc_id="food_35", text="Oats...", metadata={"title": "Oats"})]
    rate, _, hallucinated = grounding.hallucinated_food_rate("Eat Oats for breakfast.", context_docs, _vocab())
    assert rate == 0.0
    assert hallucinated == set()


def test_hallucinated_food_rate_none_when_no_foods_mentioned():
    rate, mentioned, _ = grounding.hallucinated_food_rate("I cannot help with that request.", [], _vocab())
    assert rate is None
    assert mentioned == set()


def test_extract_mentioned_foods_does_not_false_positive_on_meatless():
    mentioned = grounding.extract_mentioned_foods(
        "This vegan dish is completely meatless and dairy-free.", _vocab()
    )
    assert mentioned == set()


def test_extract_mentioned_foods_egg_white_not_shadowed_by_egg():
    mentioned = grounding.extract_mentioned_foods("Try Egg White for a lean protein boost.", _vocab())
    assert mentioned == {"Egg White"}
    assert "Egg (Whole)" not in mentioned


def test_keyword_coverage():
    assert grounding.keyword_coverage("high protein, 100g portion, because it's lean", ["protein", "portion", "because"]) == 1.0
    assert grounding.keyword_coverage("just protein", ["protein", "portion"]) == 0.5
    assert grounding.keyword_coverage("anything", []) is None


def test_numeric_accuracy_flags_wrong_calorie_figure():
    answer = "Apple has about 52 calories, which is quite low. Banana has about 300 calories per serving."
    acc, details = grounding.numeric_accuracy(answer, _vocab())
    assert acc == 0.5
    assert any(d["food"] == "Apple" and d["correct"] for d in details)
    assert any(d["food"] == "Banana" and not d["correct"] for d in details)


def test_numeric_accuracy_none_when_no_numbers_present():
    acc, details = grounding.numeric_accuracy("Eat an apple, it's healthy.", _vocab())
    assert acc is None
    assert details == []
