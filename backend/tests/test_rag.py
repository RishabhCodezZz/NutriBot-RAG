import config
import rag


def test_retrieve_returns_retrieved_docs_within_top_k():
    docs = rag.retrieve("high protein lunch", top_k=5)
    assert 0 < len(docs) <= 5
    for d in docs:
        assert isinstance(d, rag.RetrievedDoc)
        assert d.doc_id.startswith("food_")
        assert isinstance(d.text, str) and d.text
        assert "title" in d.metadata


def test_rerank_sorts_descending_and_respects_k():
    docs = rag.retrieve("high protein lunch", top_k=10)
    reranked = rag.rerank("high protein lunch", docs, k=6)
    assert len(reranked) == 6
    scores = [d.rerank_score for d in reranked]
    assert scores == sorted(scores, reverse=True)


def test_rerank_empty_docs_returns_empty():
    assert rag.rerank("anything", [], k=6) == []


def test_default_threshold_does_not_reject_genuinely_relevant_queries():
    """Regression test, twice over. RERANK_SCORE_THRESHOLD was first set to
    -3.0 assuming on-topic scores run near 0 (wrong - rejected nearly every
    real query). Recalibrated to -9.0 against short, structured queries -
    still wrong, because a live user's ordinary conversational phrasing
    ("I want a light dinner, I'm tired, what do I eat") scored -10.67 on
    the exact same reranker. Verbosity moves the score more than topic does,
    and off-topic queries cluster at -11.0 to -11.3 with no safe margin
    below that for a static cutoff - see config.py's RERANK_SCORE_THRESHOLD
    comment. The threshold is now a defensive floor, not a relevance filter;
    this test just confirms it stays out of the way of real queries,
    conversational phrasing included. Uses the real retrieve/rerank
    pipeline (no Gemini call), not a mock - the whole point is to catch a
    bad default, not confirm mocked plumbing."""
    for query in [
        "I am 21, 75kg. Suggest a high protein lunch.",
        "I need a healthy breakfast for energy, but I am allergic to nuts.",
        "Suggest a safe, low-sugar evening snack for a diabetic.",
        "I want to have a light dinner for today as i am tired what do i eat",
        "not sure what to cook for breakfast tomorrow morning, any ideas",
    ]:
        docs = rag.rerank(query, rag.retrieve(query))
        assert docs[0].rerank_score >= config.RERANK_SCORE_THRESHOLD, (
            f"query {query!r} scored {docs[0].rerank_score} which is below "
            f"the configured threshold {config.RERANK_SCORE_THRESHOLD} - it "
            f"would incorrectly hit the fallback path in production"
        )


def test_answer_query_uses_fallback_when_below_threshold(monkeypatch):
    monkeypatch.setattr(config, "RERANK_SCORE_THRESHOLD", 999.0)  # nothing can pass this

    def _boom(prompt):
        raise AssertionError("generate() must not be called when below the rerank threshold")

    monkeypatch.setattr(rag, "generate", _boom)
    result = rag.answer_query("suggest a high protein lunch")
    assert result.used_fallback is True
    assert result.answer == rag.FALLBACK_ANSWER


def test_answer_query_calls_generate_when_above_threshold(monkeypatch):
    monkeypatch.setattr(config, "RERANK_SCORE_THRESHOLD", -999.0)  # everything passes
    monkeypatch.setattr(rag, "generate", lambda prompt: "mocked answer")
    result = rag.answer_query("suggest a high protein lunch")
    assert result.used_fallback is False
    assert result.answer == "mocked answer"


def test_build_prompt_contains_query_delimiters_and_context():
    doc = rag.RetrievedDoc(doc_id="food_35", text="Oats are a food item...", metadata={"title": "Oats"})
    prompt = rag.build_prompt("suggest breakfast", [doc], "")
    assert "<<<USER_QUERY_START>>>" in prompt
    assert "<<<USER_QUERY_END>>>" in prompt
    assert "suggest breakfast" in prompt
    assert "Oats are a food item" in prompt
    assert "hallucinate" in prompt.lower()
    assert "halllucinate" not in prompt.lower()  # regression: original prompt had a 3-l typo
