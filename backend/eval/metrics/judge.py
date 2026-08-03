"""LLM-as-judge metrics: claim-level faithfulness, relevance, and an
instruction-following rubric mapped to the prompt's own mandates.

Judges with config.JUDGE_MODEL (gemini-2.5-pro by default) while generation
uses config.GEN_MODEL (gemini-2.5-flash) - using the same model for both
was the original evaluate.py's self-grading bias. Parse failures are
recorded as None ("ERROR"), never silently substituted with a fabricated
0 or mid-scale default - that was the original script's other bias.
"""
import re
import time

import google.generativeai as genai

import config

_judge_model = None


def get_judge_model():
    global _judge_model
    if _judge_model is None:
        genai.configure(api_key=config.require_gemini_key())
        _judge_model = genai.GenerativeModel(config.JUDGE_MODEL)
    return _judge_model


def _call_with_retry(prompt: str, max_retries: int = 2, backoff: float = 5.0) -> str:
    model = get_judge_model()
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return model.generate_content(prompt).text
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(backoff * (attempt + 1))
    raise last_err


def _extract_int(text: str, lo: int, hi: int):
    match = re.search(r"-?\d+", text)
    if not match:
        return None
    value = int(match.group())
    return value if lo <= value <= hi else None


def judge_faithfulness(context_text: str, answer_text: str):
    """Claim-level, not a single binary verdict: asks the judge to enumerate
    every food claim and how many are grounded in context, returns the ratio.
    Returns (ratio_or_None, raw_judge_text)."""
    prompt = (
        "You are auditing an AI diet assistant's answer for hallucination.\n"
        f"CONTEXT (the only foods it was allowed to use):\n{context_text}\n\n"
        f"ANSWER:\n{answer_text}\n\n"
        "List every distinct food the answer recommends or mentions by name, then for "
        "each state whether it appears in CONTEXT (yes/no).\n"
        "Finish your reply with a final line in EXACTLY this format:\n"
        "SCORE: <grounded_count>/<total_count>"
    )
    try:
        raw = _call_with_retry(prompt)
    except Exception as e:
        return None, f"ERROR: judge call failed: {e}"

    match = re.search(r"SCORE:\s*(\d+)\s*/\s*(\d+)", raw)
    if not match:
        return None, raw
    grounded, total = int(match.group(1)), int(match.group(2))
    if total == 0:
        return 1.0, raw
    return grounded / total, raw


def judge_relevance(question: str, answer_text: str):
    prompt = (
        f"Question: {question}\nAnswer: {answer_text}\n"
        "Score how well the answer addresses the question, from 1 (not at all) to 5 "
        "(perfectly). Reply with ONLY the digit, nothing else."
    )
    try:
        raw = _call_with_retry(prompt)
    except Exception as e:
        return None, f"ERROR: judge call failed: {e}"
    return _extract_int(raw, 1, 5), raw


INSTRUCTION_CHECKS = [
    ("portion_given",
     "Does the answer give a specific portion size (e.g. '1 cup', '100g') for "
     "at least one food? Reply YES or NO only."),
    ("why_explained",
     "Does the answer explain WHY at least one food was chosen (an actual reason, "
     "not just a name)? Reply YES or NO only."),
    ("context_appropriate",
     "Given the meal context implied by the question (breakfast/lunch/dinner/snack), "
     "are the suggested foods appropriate for that meal? Reply YES or NO only."),
    ("source_only",
     "Does the answer avoid inventing details that contradict the given context? "
     "Reply YES or NO only."),
]


def judge_instruction_following(question: str, context_text: str, answer_text: str):
    results = {}
    for key, instruction in INSTRUCTION_CHECKS:
        prompt = (
            f"Question: {question}\nContext foods: {context_text}\nAnswer: {answer_text}\n\n"
            f"{instruction}"
        )
        try:
            raw = _call_with_retry(prompt)
        except Exception:
            results[key] = None
            continue
        text = raw.strip().lower()
        if text.startswith("yes"):
            results[key] = True
        elif text.startswith("no"):
            results[key] = False
        else:
            results[key] = None
    return results
