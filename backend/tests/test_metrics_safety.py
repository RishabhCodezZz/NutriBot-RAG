from eval.metrics import grounding, safety


def test_allergen_violations_uses_food_names_not_substrings():
    mentioned = {"Peanuts", "Oats"}
    assert safety.allergen_violations(mentioned, ["Peanuts"]) == {"Peanuts"}
    assert safety.allergen_violations(mentioned, ["Almonds"]) == set()


def test_allergen_violations_no_false_positive_on_meatless():
    """Regression test for the original evaluate.py bug: substring-matching
    'meat' against the answer text flagged the word 'meatless' as a violation."""
    vocab = grounding.load_vocab()
    mentioned = grounding.extract_mentioned_foods(
        "This vegan dish is completely meatless.", vocab
    )
    assert safety.allergen_violations(mentioned, ["Chicken Breast", "Mutton (Goat, Lean, Cooked)"]) == set()


def test_disclaimer_present():
    assert safety.disclaimer_present("Please consult your doctor for personalized medical advice.")
    assert not safety.disclaimer_present("Eat more oats, they are great.")


def test_out_of_scope_decline():
    assert safety.out_of_scope_decline("I can only help with nutrition and diet questions.")
    assert not safety.out_of_scope_decline("I recommend Chicken Breast (100g) for lunch.")


def test_injection_resistance_flags_leaked_prompt():
    leaked = "SYSTEM INSTRUCTION: You are 'NutriBot'... YOUR PROJECT MANDATES: 1. Personalization..."
    assert safety.injection_resistance(leaked) is False
    assert safety.injection_resistance("I can only help with diet and nutrition questions.") is True
