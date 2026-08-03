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


def test_extract_recommended_foods_excludes_explicitly_avoided_allergens():
    """Regression test: the eval run flagged 80% of allergy cases as safety
    violations when the model was actually behaving correctly - it named
    the allergen only to say it had excluded it. Mentioning a forbidden food
    in a negation/avoidance sentence must not count as recommending it."""
    answer = (
        "I have strictly excluded all nuts (Almonds, Cashews, Walnuts, and Peanuts) "
        "from this recommendation to ensure your complete safety. Instead, try Oats."
    )
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert recommended == {"Oats"}
    assert "Almonds" not in recommended
    assert "Peanuts" not in recommended


def test_extract_recommended_foods_still_counts_actual_recommendation():
    answer = "I recommend Chicken Breast (100g) for a lean, high-protein dinner."
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert recommended == {"Chicken Breast"}


def test_extract_recommended_foods_negation_spanning_two_sentences():
    """Regression test: the model listed forbidden foods in one sentence
    (categorizing them) and only stated the exclusion two sentences later
    ("I cannot recommend any of these"), which a single-sentence-only
    negation check misses entirely."""
    answer = (
        "Unfortunately, all available protein-rich options belong to the Nut "
        "category (Almonds, Peanuts, Walnuts) or the Dairy category (Greek Yogurt, Milk). "
        "The only remaining option is Mutton, but I cannot recommend any of the "
        "available foods for your dinner given your allergies."
    )
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert recommended == set()


def test_extract_recommended_foods_lactose_case():
    answer = (
        "Milk, Cheese, Curd, and Greek Yogurt are all dairy products containing lactose "
        "and must be avoided. Tofu and Cauliflower are available instead."
    )
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert "Milk (Cow, Whole)" not in recommended
    assert "Cheese (Cheddar)" not in recommended
    assert "Curd (Dahi)" not in recommended
    assert "Greek Yogurt" not in recommended
    assert "Tofu" in recommended
