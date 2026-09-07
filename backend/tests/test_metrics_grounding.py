import pytest

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


def test_extract_mentioned_foods_plant_milk_not_mistaken_for_dairy():
    """Regression test: a real vegan test case had the model correctly
    suggest "plant-based milk" as a dairy-free substitute, and got flagged
    for recommending "Milk (Cow, Whole)" - the vocab's only "milk" entry -
    since a bare substring match can't tell the two apart. None of these
    compound items are themselves in the vocab, so they should vanish
    entirely, not resolve to the dairy entry."""
    for phrase in ["plant-based milk", "almond milk", "soy milk", "oat milk", "coconut milk"]:
        mentioned = grounding.extract_mentioned_foods(f"Mix the oats with a splash of {phrase}.", _vocab())
        assert "Milk (Cow, Whole)" not in mentioned, f"{phrase!r} was mistaken for dairy milk"
    # Plain "milk" with no qualifier is still the real dairy product.
    assert "Milk (Cow, Whole)" in grounding.extract_mentioned_foods("Add a glass of milk.", _vocab())


def test_extract_recommended_foods_excludes_bare_no_and_allergy_safe_label():
    """Regression test: a real gpt-oss:120b answer wrote "No eggs or
    egg-derived ingredients, so the meal is safe for a child with an egg
    allergy" - bare "No eggs" (no "contains") and the standalone label
    "Allergy-safe" elsewhere in the same answer, neither recognized by the
    existing negation patterns, so the egg mention was counted as a
    recommendation of the very allergen the model was warning against."""
    answer = (
        "Here's an energizing, egg-free breakfast built only from the foods you have "
        "available. Oats provide sustained energy and protein. Banana adds quick carbs "
        "and potassium. Allergy-safe: No eggs or egg-derived ingredients, so the meal "
        "is safe for a child with an egg allergy."
    )
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert "Egg (Whole)" not in recommended
    assert "Oats" in recommended


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


def test_numeric_accuracy_scales_expected_calories_to_stated_portion():
    """Regression test: a real gpt-oss:120b answer stated "150 g Chicken
    Breast ... 248 kcal". Chicken Breast's vocab baseline is 165 kcal (a
    ~100g reference), and 165 * 1.5 = 247.5 (~248) - correct math for the
    stated portion. The original comparison checked the stated number
    directly against the unscaled 100g baseline and flagged this as wrong."""
    answer = "Chicken Breast | 150 g (about 1.5 servings) | 248 kcal | 46.5 g protein"
    acc, details = grounding.numeric_accuracy(answer, _vocab())
    assert acc == 1.0
    assert details[0]["food"] == "Chicken Breast"
    assert details[0]["correct"] is True


def test_numeric_accuracy_finds_portion_even_when_a_macro_comes_first():
    """Regression test: a real gpt-oss:120b table put protein before
    calories for this food ("Banana | 1 medium (~118g) | 1.1g protein |
    89 kcal"), and taking "the gram figure closest before the calorie
    number" grabbed the 1.1g protein value instead of the 118g portion,
    producing a nonsense scaled expectation. The portion must be found
    between the food's own name and the calorie figure, not just nearest
    to the calorie figure, since column order isn't consistent."""
    answer = "Banana | 1 medium (about 118 g) | 1.1 g protein | 89 kcal | good potassium source"
    acc, details = grounding.numeric_accuracy(answer, _vocab())
    assert details[0]["food"] == "Banana"
    # Banana's vocab baseline is 89 kcal/100g. Scaled to the 118g portion,
    # expected is ~105 - close to the 89 kcal stated (a real, mild
    # under-scaling on the model's part, not this test's concern). The
    # broken version of this fix used "1.1g protein" as the portion instead,
    # scaling expected down to ~0.98 kcal - nowhere near either number.
    assert details[0]["expected"] == pytest.approx(105.0, abs=1.0)


def test_numeric_accuracy_still_flags_wrong_figure_with_portion_stated():
    """A portion is stated, but the calorie figure genuinely doesn't match
    even after scaling - this must still be flagged, not waved through just
    because a gram figure happens to be present nearby."""
    answer = "Chicken Breast | 150 g | 900 kcal | way too high"
    acc, details = grounding.numeric_accuracy(answer, _vocab())
    assert acc == 0.0
    assert details[0]["correct"] is False


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


def test_extract_recommended_foods_excludes_hyphenated_free_phrasing():
    """Regression test: a real gpt-oss:120b run wrote "egg-free" (and, with
    a Unicode non-breaking hyphen, "egg‑free") instead of a sentence
    containing one of the existing negation trigger words, so the mention
    of "egg" wasn't excluded and got counted as a recommended - i.e.
    allergy-violating - food, despite the model correctly avoiding it."""
    answer = "All ingredients here are egg‑free, so they’re safe for your allergy."
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert "Egg (Whole)" not in recommended


def test_extract_recommended_foods_excludes_contains_no_phrasing():
    """The negation sentence is separated from the recommendation by a
    buffer sentence - matching the real run's actual spacing - so this
    isolates the "contains no" pattern itself rather than also exercising
    the two-sentence forward-lookahead's own suppression radius."""
    answer = (
        "Mutton is the main protein here. It's a great source of iron and B12. "
        "It contains no eggs or seafood, so it fits your allergy restrictions."
    )
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert "Egg (Whole)" not in recommended
    assert "Mutton (Goat, Lean, Cooked)" in recommended


def test_extract_recommended_foods_excludes_cross_contamination_warning():
    """Regression test: a real run's disclaimer sentence ("please double-check
    ... to ensure no cross-contamination with shrimp or prawns") named the
    allergen only to warn against it, well after the actual recommendation -
    no negation trigger word was in that sentence's own window, so it was
    counted as a recommendation of the allergen itself. Buffer sentences
    match the real run's actual spacing between the two, so this isolates
    the cross-contamination pattern rather than the lookahead's own radius."""
    answer = (
        "Grilled Salmon is a great seafood dinner option. It is rich in omega-3 "
        "fats and high-quality protein. Since you have a shellfish allergy, please "
        "double-check ingredient labels and cooking methods to ensure no "
        "cross-contamination with shrimp or prawns."
    )
    recommended = grounding.extract_recommended_foods(answer, _vocab())
    assert "Prawns/Shrimp" not in recommended
    assert "Salmon" in recommended


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
