import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def require_gemini_key() -> str:
    """Fail fast, but only for code paths that actually need Gemini (rag.py) -
    ingest.py and retrieval-only tooling don't need a key and shouldn't be
    blocked by not having one."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and fill in a real key, or set the GEMINI_API_KEY environment variable."
        )
    return GEMINI_API_KEY

CHROMA_PATH = str(BASE_DIR / "chroma_db")
COLLECTION_NAME = "nutrition_data"

EMBEDDING_MODEL = "all-mpnet-base-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEN_MODEL = os.environ.get("GEMINI_GEN_MODEL", "gemini-2.5-flash")
JUDGE_MODEL = os.environ.get("GEMINI_JUDGE_MODEL", "gemini-2.5-pro")

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
GEN_MAX_OUTPUT_TOKENS = int(os.environ.get("GEN_MAX_OUTPUT_TOKENS", "1024"))

DATA_PATH = str(BASE_DIR / "data" / "nutrition_data.txt")
FOOD_VOCAB_PATH = str(BASE_DIR / "data" / "food_vocab.json")
