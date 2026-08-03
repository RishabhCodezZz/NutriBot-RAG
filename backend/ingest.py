import os
import re

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

import config

# === SETUP ===
embedding_fn = SentenceTransformerEmbeddingFunction(model_name=config.EMBEDDING_MODEL)
client = chromadb.PersistentClient(path=config.CHROMA_PATH)

TITLE_PATTERN = re.compile(r"^(.*?)\s+(?:is|are)\s+a food item", re.IGNORECASE)


def extract_title(item_text: str, index: int) -> str:
    match = TITLE_PATTERN.match(item_text)
    if match:
        return match.group(1).strip()
    return f"Food Item {index}"


def ingest_data():
    print("--- Starting Ingestion ---")

    if not os.path.exists(config.DATA_PATH):
        print(f"ERROR: File not found at {config.DATA_PATH}")
        return

    print(f"Loading data from {config.DATA_PATH}...")

    with open(config.DATA_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()

    food_items = [item.strip() for item in raw_text.split("\n\n") if item.strip()]

    print(f"   Found {len(food_items)} food descriptions.")

    # Reset collection
    try:
        client.delete_collection(config.COLLECTION_NAME)
        print(f"Deleted old collection '{config.COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=config.COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    documents = []
    ids = []
    metadatas = []

    print("Processing items...")
    fallback_titles = 0
    for index, item_text in enumerate(food_items):
        title = extract_title(item_text, index)
        if title == f"Food Item {index}":
            fallback_titles += 1
            print(f"   WARNING: could not extract a title for item {index}: {item_text[:60]!r}")

        documents.append(item_text)
        ids.append(f"food_{index}")
        metadatas.append({"title": title})

    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"\nSUCCESS! Ingested {len(documents)} items using '{config.EMBEDDING_MODEL}'.")
        if fallback_titles:
            print(f"   {fallback_titles} item(s) fell back to a generic 'Food Item N' title - check the data file.")
    else:
        print("\nWARNING: No data found.")


if __name__ == "__main__":
    ingest_data()
