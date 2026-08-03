from flask import Flask, request, jsonify
from flask_cors import CORS

import config
import rag

print("Connecting to Gemini & Database...")
print(f"System ready using {config.GEN_MODEL}.")

CHAT_HISTORY = {"default_user": []}

app = Flask(__name__)
CORS(app, origins=config.ALLOWED_ORIGINS)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/reset", methods=["POST"])
def reset():
    CHAT_HISTORY["default_user"] = []
    return jsonify({"success": True, "answer": "Chat history cleared."})


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")

    # Backwards-compatible with the old sentinel-string reset command.
    if query == "RESET_CHAT":
        return reset()

    if not query.strip():
        return jsonify({"error": "query must not be empty"}), 400

    print(f"\nReceived: {query}")

    history = CHAT_HISTORY["default_user"]
    history_text = "\n".join(history[-config.HISTORY_MAX_TURNS :])

    try:
        result = rag.answer_query(query, history_text=history_text)
    except Exception as e:
        print(f"Gemini generation failed: {e}")
        return jsonify({"success": False, "error": f"Generation failed: {e}"}), 502

    if not result.used_fallback:
        history.append(f"User: {query}")
        history.append(f"AI: {result.answer}")
        history[:] = history[-(config.HISTORY_MAX_TURNS * 4) :]

    sources = [{"title": d.metadata.get("title", "Food")} for d in result.context_docs]
    return jsonify({"success": True, "answer": result.answer, "sources": sources})


@app.errorhandler(Exception)
def handle_unexpected(e):
    print(f"Unhandled error: {e}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    # use_reloader=False prevents the WinError 10038 crash on Windows.
    app.run(debug=False, use_reloader=False, host="127.0.0.1", port=5000)
