import rag
import server


def test_health():
    client = server.app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_search_success_envelope(monkeypatch):
    fake_result = rag.RagResult(
        answer="Eat Oats (1 cup) for breakfast.",
        context_docs=[rag.RetrievedDoc(doc_id="food_35", text="...", metadata={"title": "Oats"})],
    )
    monkeypatch.setattr(server.rag, "answer_query", lambda query, history_text="": fake_result)

    resp = server.app.test_client().post("/api/search", json={"query": "suggest breakfast"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["answer"] == "Eat Oats (1 cup) for breakfast."
    assert data["sources"] == [{"title": "Oats", "text": "..."}]


def test_search_fallback_still_reports_success_true(monkeypatch):
    """Regression test: the original server.py's no-results branch omitted
    `success`, so the frontend's `if (data.success)` treated a real answer
    as an error and displayed a misleading 'database connection' message."""
    fake_result = rag.RagResult(answer=rag.FALLBACK_ANSWER, used_fallback=True)
    monkeypatch.setattr(server.rag, "answer_query", lambda query, history_text="": fake_result)

    resp = server.app.test_client().post("/api/search", json={"query": "asdkjaskjd nonsense"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["answer"] == rag.FALLBACK_ANSWER


def test_search_generation_failure_returns_502_not_200(monkeypatch):
    """Regression test: the original server.py caught Gemini errors inside
    get_gemini_response and returned them as a 200 response with
    "Gemini Error: ..." rendered as if it were the bot's answer."""
    def _boom(query, history_text=""):
        raise RuntimeError("Gemini quota exceeded")

    monkeypatch.setattr(server.rag, "answer_query", _boom)
    resp = server.app.test_client().post("/api/search", json={"query": "suggest breakfast"})
    data = resp.get_json()
    assert resp.status_code == 502
    assert data["success"] is False


def test_reset_chat_sentinel_clears_history():
    server.CHAT_HISTORY["default_user"] = ["User: hi", "AI: hello"]
    resp = server.app.test_client().post("/api/search", json={"query": "RESET_CHAT"})
    data = resp.get_json()
    assert data["success"] is True
    assert server.CHAT_HISTORY["default_user"] == []


def test_empty_query_returns_400():
    resp = server.app.test_client().post("/api/search", json={"query": "   "})
    assert resp.status_code == 400
