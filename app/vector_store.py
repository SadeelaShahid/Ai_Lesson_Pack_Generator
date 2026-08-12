import os
os.environ["HF_HUB_OFFLINE"] = "0"

import chromadb
from sentence_transformers import SentenceTransformer
from pdf_loader import load_all_pdfs

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "data", "chroma_db")

_model = None
_collection = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def build_vector_store():
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection("lesson_materials")
    except Exception:
        pass

    collection = client.create_collection("lesson_materials")
    model = get_model()

    documents = load_all_pdfs()

    all_chunks = []
    all_ids = []
    all_metadatas = []

    chunk_counter = 0
    for doc in documents:
        chunks = chunk_text(doc["text"])
        for chunk in chunks:
            all_chunks.append(chunk)
            all_ids.append(f"chunk_{chunk_counter}")
            all_metadatas.append({"source": doc["source"]})
            chunk_counter += 1

    print(f"Total chunks created: {len(all_chunks)}")

    embeddings = model.encode(all_chunks).tolist()

    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        ids=all_ids,
        metadatas=all_metadatas
    )

    print("Vector store built and saved successfully.")
    return collection


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection("lesson_materials")
    return _collection


def retrieve(query, k=5):
    model = get_model()
    collection = get_collection()
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)
    return list(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ))


if __name__ == "__main__":
    build_vector_store()

    print("\n=== Test retrieval: 'Python loops for beginners' ===")
    results = retrieve("Python loops for beginners", k=3)
    for text, meta, distance in results:
        print(f"\nSource: {meta['source']} (distance: {distance:.4f})")
        print(f"Chunk: {text[:150]}...")