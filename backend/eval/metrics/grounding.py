"""Deterministic, judge-free metrics: hallucinated-food rate, numeric
accuracy, keyword coverage. These need no LLM call and no rate limiting,
so they're the cheapest and most reproducible signal the harness has.
"""
import json
import re

import config

_vocab_cache = None


def load_vocab():
    global _vocab_cache
    if _vocab_cache is None:
        with open(config.FOOD_VOCAB_PATH, encoding="utf-8") as f:
            _vocab_cache = json.load(f)
    return _vocab_cache


def build_name_index(vocab):
    """lowercase name/base-name/alias -> canonical name."""
    index = {}
    for f in vocab:
        index[f["name"].lower()] = f["name"]
        base = re.sub(r"\s*\(.*?\)", "", f["name"]).strip().lower()
        index.setdefault(base, f["name"])
        for alias in f["aliases"]:
            index[alias.lower()] = f["name"]
    return index


def extract_mentioned_foods(answer_text: str, vocab: list) -> set:
    """Substring match against the closed 74-food vocabulary (+ aliases),
    longest key first, consuming matched character spans so a longer match
    (e.g. 'Egg White') blocks a shorter one that overlaps it (e.g. the bare
    'egg' derived from 'Egg (Whole)') from also firing on the same text."""
    name_index = build_name_index(vocab)
    text_lower = answer_text.lower()
    consumed = [False] * len(text_lower)
    mentioned = set()
    for key in sorted(name_index, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(key) + r"\b", text_lower):
            start, end = m.span()
            if any(consumed[start:end]):
                continue
            mentioned.add(name_index[key])
            for i in range(start, end):
                consumed[i] = True
    return mentioned


def hallucinated_food_rate(answer_text: str, context_docs: list, vocab: list):
    """Fraction of vocabulary foods mentioned in the answer that were NOT in
    the retrieved context - foods the model pulled in from outside what it
    was given, violating the prompt's 'source-only' mandate.

    Returns (rate_or_None, mentioned_set, hallucinated_set). rate is None
    when the answer mentions no vocabulary foods at all (nothing to check).
    """
    mentioned = extract_mentioned_foods(answer_text, vocab)
    if not mentioned:
        return None, mentioned, set()
    context_titles = {d.metadata.get("title") for d in context_docs}
    hallucinated = mentioned - context_titles
    return len(hallucinated) / len(mentioned), mentioned, hallucinated


def keyword_coverage(answer_text: str, must_include: list):
    if not must_include:
        return None
    text_lower = answer_text.lower()
    hits = sum(1 for kw in must_include if kw.lower() in text_lower)
    return hits / len(must_include)


def numeric_accuracy(answer_text: str, vocab: list, tolerance: float = 0.15):
    """Sentence-scoped check: for each sentence that names a vocabulary food
    AND states a calorie figure, compare that figure to the vocab value.
    Sentence-scoping avoids the false correspondences a fully global
    food-x-number cross product would produce; it's still an approximation,
    not real span-level attribution.
    """
    name_index = build_name_index(vocab)
    vocab_by_name = {f["name"]: f for f in vocab}
    sentences = re.split(r"(?<=[.!?])\s+", answer_text)

    checked = 0
    correct = 0
    details = []
    for sent in sentences:
        sent_lower = sent.lower()
        cal_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kcal|calories)", sent_lower)
        if not cal_match:
            continue
        for key in sorted(name_index, key=len, reverse=True):
            if re.search(r"\b" + re.escape(key) + r"\b", sent_lower):
                food_name = name_index[key]
                expected = vocab_by_name[food_name]["calories"]
                if expected is None:
                    continue
                value = float(cal_match.group(1))
                checked += 1
                is_correct = abs(value - expected) / expected <= tolerance
                correct += int(is_correct)
                details.append({
                    "food": food_name, "stated": value,
                    "expected": expected, "correct": is_correct,
                })
                break

    if checked == 0:
        return None, details
    return correct / checked, details
