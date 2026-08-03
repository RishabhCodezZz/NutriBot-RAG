"""Retrieval/prompt variants for the ablation table, all routed through the
same rag.generate() call so only the retrieval strategy or prompt differs
between rows - never the generation call itself.

LEGACY_PROMPT_TEMPLATE reproduces the original (pre-hardening) server.py
prompt verbatim (including the "halllucinate" typo) so the final ablation
row - hardened prompt vs legacy prompt, same retrieval - isolates exactly
what Phase 2's prompt hardening changed, instead of conflating it with the
retrieval-strategy comparison in the earlier rows.
"""
from rank_bm25 import BM25Okapi

import config
import rag

LEGACY_PROMPT_TEMPLATE = """
    SYSTEM INSTRUCTION:
    You are 'NutriBot', a RAG-Based Personalized Diet Assistant.

    YOUR PROJECT MANDATES:
    1. **Personalization**: Always consider the user's Age, Weight, and Goal if provided.
    2. **Explain "Why"**: You MUST explain WHY a specific food was chosen (e.g., "I chose Oats because they are high in fiber...").
    3. **Portion Sizes**: Suggest specific portion sizes (e.g., "1 cup" or "100g").
    4. **Context Aware**:
       - If Breakfast: Suggest lighter, high-fiber/energy options.
       - If Lunch/Dinner: Suggest protein-dense, filling options.
    5. **Source-Based**: Use ONLY the "Available Food Items" below. Do not halllucinate foods not in the list.

    AVAILABLE FOOD ITEMS:
    {context_text}

    CONVERSATION HISTORY:
    {history_text}

    USER QUERY:
    {query}

    YOUR ANSWER:
    """

NO_RETRIEVAL_PROMPT_TEMPLATE = """You are a diet assistant. Answer the user's nutrition question \
using your own general knowledge - no external food database is available for this test.

USER QUERY:
{query}

YOUR ANSWER:"""

VARIANTS = [
    "no_retrieval",
    "bm25",
    "dense_no_rerank",
    "dense_rerank_legacy_prompt",
    "dense_rerank_hardened",
]

_bm25_index = None
_bm25_docs = None


def _get_all_docs():
    coll = rag.get_collection()
    data = coll.get()
    return [
        rag.RetrievedDoc(doc_id=i, text=t, metadata=m)
        for i, t, m in zip(data["ids"], data["documents"], data["metadatas"])
    ]


def _bm25_retrieve(query: str, k: int):
    global _bm25_index, _bm25_docs
    if _bm25_index is None:
        _bm25_docs = _get_all_docs()
        tokenized = [d.text.lower().split() for d in _bm25_docs]
        _bm25_index = BM25Okapi(tokenized)
    scores = _bm25_index.get_scores(query.lower().split())
    ranked = sorted(zip(_bm25_docs, scores), key=lambda x: x[1], reverse=True)
    return [d for d, _ in ranked[:k]]


def _legacy_prompt(query, docs, history_text):
    context_text = "\n".join(f"- {d.text}" for d in docs)
    return LEGACY_PROMPT_TEMPLATE.format(
        context_text=context_text or "(none)",
        history_text=history_text or "(none)",
        query=query,
    )


def run_variant(variant: str, query: str, history_text: str = ""):
    """Returns (answer_text, context_docs, prompt_used)."""
    if variant == "no_retrieval":
        prompt = NO_RETRIEVAL_PROMPT_TEMPLATE.format(query=query)
        return rag.generate(prompt), [], prompt

    if variant == "bm25":
        docs = _bm25_retrieve(query, config.RERANK_K)
        return rag.generate(_legacy_prompt(query, docs, history_text)), docs, None

    if variant == "dense_no_rerank":
        docs = rag.retrieve(query, top_k=config.RERANK_K)
        return rag.generate(_legacy_prompt(query, docs, history_text)), docs, None

    if variant == "dense_rerank_legacy_prompt":
        docs = rag.rerank(query, rag.retrieve(query))
        return rag.generate(_legacy_prompt(query, docs, history_text)), docs, None

    if variant == "dense_rerank_hardened":
        docs = rag.rerank(query, rag.retrieve(query))
        prompt = rag.build_prompt(query, docs, history_text)
        return rag.generate(prompt), docs, prompt

    raise ValueError(f"unknown ablation variant: {variant}")
