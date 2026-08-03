"""One-off script: parse nutrition_data.txt into a structured food_vocab.json.

Not used at request time - this is a derived, hand-correctable asset that the
eval suite (backend/eval) uses for deterministic metrics (hallucinated-food
rate, numeric accuracy, allergen-safety) that can't be computed from free text
alone. Re-run and re-review the ALLERGEN_TAGS / DIET_TAGS / ALIASES maps below
whenever nutrition_data.txt gains new foods.
"""
import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).parent / "nutrition_data.txt"
OUT_PATH = Path(__file__).parent / "food_vocab.json"

TITLE_RE = re.compile(r"^(.*?)\s+(?:is|are)\s+a food item", re.IGNORECASE)
CATEGORY_RE = re.compile(r"in the (\w+) category")
CALORIES_RE = re.compile(r"contains?\s+([\d.]+)\s+calories per (serving|100 g)")
PROTEIN_RE = re.compile(r"includes\s+([\d.]+)g of protein")
CARBS_RE = re.compile(r",\s*([\d.]+)g of carbohydrates")
FATS_RE = re.compile(r"and\s+([\d.]+)g of fats")

# Hand-authored - not derivable from the free-text corpus. Allergen vocabulary
# matches what test_cases.json exercises (nut, dairy, egg, seafood, soy,
# gluten) plus enough of a diet_tags split to compute vegan/vegetarian
# violations without substring matching on the answer text.
ALLERGEN_TAGS = {
    "Almonds": ["nut", "tree nut"],
    "Walnuts": ["nut", "tree nut"],
    "Peanuts": ["nut", "peanut"],
    "Cashews": ["nut", "tree nut"],
    "Paneer": ["dairy", "milk"],
    "Milk (Cow, Whole)": ["dairy", "milk"],
    "Curd (Dahi)": ["dairy", "milk"],
    "Greek Yogurt": ["dairy", "milk"],
    "Cheese (Cheddar)": ["dairy", "milk"],
    "Butter": ["dairy", "milk"],
    "Ghee": ["dairy", "milk"],
    "Egg (Whole)": ["egg"],
    "Egg White": ["egg"],
    "Fish (Rohu/Katla, Raw)": ["seafood", "fish"],
    "Salmon": ["seafood", "fish"],
    "Prawns/Shrimp": ["seafood", "shellfish"],
    "Soya Chunks": ["soy"],
    "Tofu": ["soy"],
    "Wheat Roti (Whole Wheat Flour)": ["gluten", "wheat"],
}

NON_VEGETARIAN = {
    "Chicken Breast", "Chicken Thigh", "Mutton (Goat, Lean, Cooked)",
    "Fish (Rohu/Katla, Raw)", "Salmon", "Prawns/Shrimp",
    "Egg (Whole)", "Egg White",
}
DAIRY_NAMES = {
    "Paneer", "Milk (Cow, Whole)", "Curd (Dahi)", "Greek Yogurt",
    "Cheese (Cheddar)", "Butter", "Ghee",
}

ALIASES = {
    "Chickpeas (Chole)": ["Chole", "Garbanzo Beans", "Garbanzo"],
    "Kidney Beans (Rajma)": ["Rajma"],
    "Green Peas (Matar)": ["Matar", "Peas"],
    "Bitter Gourd (Karela)": ["Karela"],
    "Bottle Gourd (Lauki)": ["Lauki"],
    "Cauliflower (Gobi)": ["Gobi"],
    "Eggplant (Brinjal)": ["Brinjal", "Aubergine"],
    "Okra (Lady Finger)": ["Lady Finger", "Bhindi"],
    "Custard Apple (Sitaphal)": ["Sitaphal"],
    "Wheat Roti (Whole Wheat Flour)": ["Roti", "Chapati", "Whole Wheat Flour"],
    "Cheese (Cheddar)": ["Cheddar", "Cheddar Cheese"],
    "Milk (Cow, Whole)": ["Whole Milk", "Cow Milk", "Milk"],
    "Curd (Dahi)": ["Dahi", "Yogurt"],
    "Fish (Rohu/Katla, Raw)": ["Rohu", "Katla"],
    "Mutton (Goat, Lean, Cooked)": ["Mutton", "Goat Meat"],
    "Prawns/Shrimp": ["Prawns", "Shrimp"],
    "Ragi (Finger Millet)": ["Ragi", "Finger Millet"],
    "Jowar (Sorghum)": ["Jowar", "Sorghum"],
    "Corn (Maize)": ["Corn", "Maize"],
    "Black Gram (Urad)": ["Urad", "Urad Dal"],
}


def parse_food(text: str, index: int) -> dict:
    title_match = TITLE_RE.match(text)
    name = title_match.group(1).strip() if title_match else f"Food Item {index}"

    category_match = CATEGORY_RE.search(text)
    calories_match = CALORIES_RE.search(text)
    protein_match = PROTEIN_RE.search(text)
    carbs_match = CARBS_RE.search(text)
    fats_match = FATS_RE.search(text)

    diet_tags = ["vegan", "vegetarian"]
    if name in NON_VEGETARIAN:
        diet_tags = ["non-vegetarian"]
    elif name in DAIRY_NAMES:
        diet_tags = ["vegetarian"]

    return {
        "name": name,
        "aliases": ALIASES.get(name, []),
        "category": category_match.group(1) if category_match else None,
        "calorie_basis": calories_match.group(2) if calories_match else None,
        "calories": float(calories_match.group(1)) if calories_match else None,
        "protein_g": float(protein_match.group(1)) if protein_match else None,
        "carbs_g": float(carbs_match.group(1)) if carbs_match else None,
        "fats_g": float(fats_match.group(1)) if fats_match else None,
        "allergen_tags": ALLERGEN_TAGS.get(name, []),
        "diet_tags": diet_tags,
    }


def build():
    raw_text = DATA_PATH.read_text(encoding="utf-8")
    items = [item.strip() for item in raw_text.split("\n\n") if item.strip()]

    vocab = [parse_food(item, i) for i, item in enumerate(items)]

    missing = [
        f["name"] for f in vocab
        if f["calories"] is None or f["protein_g"] is None
        or f["carbs_g"] is None or f["fats_g"] is None
    ]
    if missing:
        raise RuntimeError(f"Failed to parse macros for: {missing}")

    OUT_PATH.write_text(json.dumps(vocab, indent=2), encoding="utf-8")
    print(f"Wrote {len(vocab)} foods to {OUT_PATH}")


if __name__ == "__main__":
    build()
