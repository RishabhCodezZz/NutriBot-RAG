# NutriBot – RAG Diet Assistant

A retrieval-augmented chatbot that suggests personalized diet plans from a curated nutrition dataset. It retrieves relevant food descriptions from ChromaDB, reranks them, and asks an LLM to generate context-aware, portioned recommendations with explanations.

## Features

- **Personalized answers**: Prompt enforces age/weight/goal awareness, portions, and “why” reasoning.
- **RAG stack**: ChromaDB with `all-mpnet-base-v2` embeddings; cross-encoder reranker `ms-marco-MiniLM-L-6-v2`.
- **LLM**: `gpt-oss:120b` via [Ollama Cloud](https://ollama.com/cloud) (free tier) for generation. The eval suite's LLM-judge uses Gemini `gemini-3.1-flash-lite` separately, deliberately on a different provider than generation to avoid self-grading bias.
- **Frontend UX**: Dark/light mode, speech synthesis read-aloud, a shimmer skeleton loading state, “New Chat” that fully resets history.
- **Sources**: Hovering a cited food name in an answer shows the real retrieved snippet behind it.

## Project Structure

```
Mini project/
├── backend/
│   ├── ingest.py          # Ingest nutrition_data.txt into ChromaDB
│   ├── server.py          # Flask API (RAG + Ollama Cloud)
│   ├── requirements.txt   # Backend dependencies
│   ├── data/
│   │   └── nutrition_data.txt
│   └── chroma_db/         # Generated vector store (created after ingest)
└── react-frontend/
    ├── package.json
    ├── src/
    │   ├── App.js
    │   └── components/
    │       └── ChatInterface.jsx
    └── public/
```

## Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Set your API keys
cp .env.example .env
# then edit backend/.env:
#   OLLAMA_API_KEY=your_key_here   (required - generation; get one at https://ollama.com/settings/keys)
#   GEMINI_API_KEY=your_key_here   (only needed to run the eval suite's LLM-judge)

# Build / refresh the vector store
python ingest.py

# Run the API
python server.py  # listens on http://127.0.0.1:5000
```

For a non-debug run, use `waitress-serve --host=127.0.0.1 --port=5000 server:app` instead of
`python server.py`.

## Frontend Setup

```bash
cd react-frontend
npm install
npm start  # opens http://localhost:3000
```

## Usage

1) Start backend (`python server.py`).  
2) Start frontend (`npm start`).  
3) Ask for meal guidance (e.g., “I am 21, 75kg. Suggest a high-protein lunch”).  
4) Click **New Chat** to fully reset conversation (frontend and backend history).  
5) Use the speaker button on answers to hear text-to-speech.

## Regenerating the DB

If you change `data/nutrition_data.txt`, delete `backend/chroma_db/` (or let ingest overwrite) and rerun:

```bash
cd backend
python ingest.py
```

## Notes

- API keys are read from `backend/.env` (via `python-dotenv`) or the environment - see
  `backend/config.py`. Never hardcoded in source, never commit `.env`.
- The typing indicator is a shimmer skeleton during response generation; the assistant replies after retrieval + rerank + the Ollama Cloud generation call.
- `backend/rag.py` holds the whole retrieve/rerank/prompt/generate pipeline as importable functions;
  `server.py` is a thin Flask wrapper over it, and `backend/eval` imports the same functions so
  evaluation numbers describe production rather than a separate reimplementation.
- Backend evaluation lives in `backend/eval/` (see below) - run with
  `python -m eval.run --config all --runs 3` from inside `backend/`.
