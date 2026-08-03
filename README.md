# NutriBot – RAG Diet Assistant

A retrieval-augmented chatbot that suggests personalized diet plans from a curated nutrition dataset. It retrieves relevant food descriptions from ChromaDB, reranks them, and asks Gemini to generate context-aware, portioned recommendations with explanations.

## Features

- **Personalized answers**: Prompt enforces age/weight/goal awareness, portions, and “why” reasoning.
- **RAG stack**: ChromaDB with `all-mpnet-base-v2` embeddings; cross-encoder reranker `ms-marco-MiniLM-L-6-v2`.
- **LLM**: Gemini `gemini-2.5-flash` for generation.
- **Frontend UX**: Dark/light mode, speech synthesis read-aloud, bouncing typing indicator, sidebar “New Chat” that fully resets history.
- **Sources**: Returns titles of the retrieved food items for transparency.

## Project Structure

```
Mini project/
├── backend/
│   ├── ingest.py          # Ingest nutrition_data.txt into ChromaDB
│   ├── server.py          # Flask API (RAG + Gemini)
│   ├── requirements.txt   # Backend dependencies
│   ├── data/
│   │   └── nutrition_data.txt
│   └── chroma_db/         # Generated vector store (created after ingest)
└── react-frontend/
    ├── package.json
    ├── src/
    │   ├── App.js
    │   ├── components/
    │   │   ├── ChatInterface.jsx
    │   │   └── Sidebar.jsx
    │   └── lib/utils.js
    └── public/
```

## Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Set your Gemini API key
cp .env.example .env
# then edit backend/.env and set GEMINI_API_KEY=your_key_here

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
4) Click **New Chat** in the sidebar to fully reset conversation (frontend and backend history).  
5) Use the speaker button on answers to hear text-to-speech.

## Regenerating the DB

If you change `data/nutrition_data.txt`, delete `backend/chroma_db/` (or let ingest overwrite) and rerun:

```bash
cd backend
python ingest.py
```

## Notes

- The API key is read from `backend/.env` (via `python-dotenv`) or the `GEMINI_API_KEY` environment
  variable - see `backend/config.py`. It is never hardcoded in source. Never commit `.env`.
- The typing indicator uses bouncing dots during response generation; the assistant replies after retrieval + rerank + Gemini call.
- `backend/rag.py` holds the whole retrieve/rerank/prompt/generate pipeline as importable functions;
  `server.py` is a thin Flask wrapper over it, and `backend/eval` imports the same functions so
  evaluation numbers describe production rather than a separate reimplementation.
- Backend evaluation lives in `backend/eval/` (see below) - run with
  `python -m eval.run --config all --runs 3` from inside `backend/`.
