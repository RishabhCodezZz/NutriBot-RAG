from ingest import extract_title


def test_singular_title():
    text = "Apple is a food item in the Fruit category. It contains 52 calories..."
    assert extract_title(text, 0) == "Apple"


def test_plural_title_regression():
    """Regression test for the original bug: split(' is ') failed on plural
    foods ("Grapes are a food item"), producing 15 corrupted 'Food Item N'
    titles in the shipped database."""
    text = "Grapes are a food item in the Fruit category. They contain 69 calories..."
    assert extract_title(text, 4) == "Grapes"


def test_parenthetical_title():
    text = "Custard Apple (Sitaphal) is a food item in the Fruit category. It contains 94 calories..."
    assert extract_title(text, 9) == "Custard Apple (Sitaphal)"


def test_fallback_when_no_match():
    text = "Some malformed entry without the expected phrase."
    assert extract_title(text, 42) == "Food Item 42"
