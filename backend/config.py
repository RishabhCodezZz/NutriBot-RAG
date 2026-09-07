import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def require_gemini_key() -> str:
    """Fail fast, but only for code paths that actually need Gemini. Generation
    (rag.py) no longer uses Gemini - this is now needed only by the eval
    suite's LLM-judge (backend/eval/metrics/judge.py), which deliberately
    stays on a different provider/model than generation to avoid the
    self-grading bias the original evaluate.py had."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and fill in a real key, or set the GEMINI_API_KEY environment variable. "
            "Only needed to run the eval suite's LLM-judge."
        )
    return GEMINI_API_KEY


OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com")


def require_ollama_key() -> str:
    """Fail fast, but only for code paths that actually need Ollama Cloud
    generation (rag.py) - ingest.py and retrieval-only tooling don't need a
    key and shouldn't be blocked by not having one."""
    if not OLLAMA_API_KEY:
        raise RuntimeError(
            "OLLAMA_API_KEY is not set. Get a free key from "
            "https://ollama.com/settings/keys and set it in backend/.env or as "
            "an environment variable."
        )
    return OLLAMA_API_KEY

CHROMA_PATH = str(BASE_DIR / "chroma_db")
COLLECTION_NAME = "nutrition_data"

EMBEDDING_MODEL = "all-mpnet-base-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
# Generation runs on Ollama Cloud (free tier) instead of the Gemini API - see
# rag.py. gpt-oss:120b is the largest/strongest model available on the free
# cloud tier at the time this was chosen, picked deliberately so the
# before/after eval comparison against the prior Gemini 2.5 Flash numbers is
# an honest one, not a rigged comparison against a weak baseline.
GEN_MODEL = os.environ.get("GEN_MODEL", "gpt-oss:120b")
# The judge stays on Gemini (a different provider than generation) so the
# eval methodology doesn't change when the generation backend does. Note:
# the original baseline run used gemini-2.5-pro as judge; judge-based
# numbers (faithfulness/relevance/instruction-following) against this
# default are informative but not a perfectly controlled comparison to that
# baseline, since the judge itself is now a different model too.
JUDGE_MODEL = os.environ.get("GEMINI_JUDGE_MODEL", "gemini-3.1-flash-lite")

TOP_K = int(os.environ.get("RAG_TOP_K", "10"))
RERANK_K = int(os.environ.get("RAG_RERANK_K", "6"))
# Cross-encoder raw logit threshold below which the top doc is treated as
# "not relevant enough" to answer from.
#
# This was tried twice as a real relevance gate and failed both times:
#   - first pass assumed on-topic scores run "near 0" (wrong) and set -3.0,
#     which rejected nearly every real query in production.
#   - second pass calibrated -9.0 against a small sample of short, structured
#     queries ("I am 21, 75kg, suggest X"). A live user then typed a normal
#     conversational question ("I want a light dinner, I'm tired, what do I
#     eat") that scored -10.67 - phrasing verbosity moves the score far more
#     than topic does. Off-topic queries cluster at -11.0 to -11.3, but some
#     genuinely on-topic conversational phrasing scores just as low, leaving
#     no reliable margin for a static cutoff on this reranker.
#
# The LLM itself, given the prompt's own scope-decline rule, correctly
# declines off-topic questions even when irrelevant context is injected -
# verified directly (a "what's the weather" query with 6 unrelated foods in
# context still got "I can only help with diet, nutrition, and food
# questions"). That's the real relevance gate now. This threshold is kept
# only as a defensive floor for a broken/empty collection, not as a
# semantic filter - hence the very permissive default.
RERANK_SCORE_THRESHOLD = float(os.environ.get("RAG_RERANK_SCORE_THRESHOLD", "-50.0"))

HISTORY_MAX_TURNS = int(os.environ.get("RAG_HISTORY_MAX_TURNS", "6"))
SESSION_TTL_SECONDS = int(os.environ.get("RAG_SESSION_TTL_SECONDS", str(60 * 60 * 6)))

_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

GEN_TEMPERATURE = float(os.environ.get("GEN_TEMPERATURE", "0.4"))
# gpt-oss:120b is a reasoning model - unlike Gemini Flash, it spends part of
# num_predict on an internal reasoning trace before writing the visible
# answer, and writes much longer answers besides (markdown tables, multiple
# options). Verified directly: at the old 1024-token cap (sized for Gemini
# Flash's terser style) a real answer was cut off mid-sentence. Raised to
# give the visible answer room, and GEN_THINK below caps the reasoning-trace
# overhead so it doesn't eat that budget for a task this simple.
GEN_MAX_OUTPUT_TOKENS = int(os.environ.get("GEN_MAX_OUTPUT_TOKENS", "2048"))
# gpt-oss models take a "low"/"medium"/"high" reasoning-effort control
# (not a plain on/off). Diet recommendations don't need multi-step
# reasoning, so this is kept low - it both saves tokens for the visible
# answer and keeps latency down on a shared free cloud endpoint.
GEN_THINK = os.environ.get("GEN_THINK", "low")
# The Ollama client's default timeout is None (wait forever). A shared free
# cloud endpoint can stall on a cold model start or overload, and an
# unbounded wait there would hang the whole Flask request - so this gives
# generation a finite ceiling instead of inheriting "no timeout" by default.
GEN_TIMEOUT_SECONDS = float(os.environ.get("GEN_TIMEOUT_SECONDS", "60"))

DATA_PATH = str(BASE_DIR / "data" / "nutrition_data.txt")
FOOD_VOCAB_PATH = str(BASE_DIR / "data" / "food_vocab.json")
