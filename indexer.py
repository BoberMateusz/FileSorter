import os, re, hashlib
import chromadb
import config
from embedder import get_embedder
from file_processor import process_file   # Person 1 (dopasuj nazwę modułu)

def get_collection():
    client = chromadb.PersistentClient(path=config.DB_PATH)
    tag = re.sub(r"[^a-zA-Z0-9_-]", "_", config.MODEL_NAME)[-40:]
    # inna nazwa kolekcji per model, bo różne modele mają różne wymiary wektorów
    return client.get_or_create_collection(
        name=f"chunks_{tag}", metadata={"hnsw:space": "cosine"}
    )

def index_file(path: str, col=None) -> int:
    col = col or get_collection()
    chunks = [c for c in process_file(path) if c and c.strip()]
    if not chunks:
        return 0
    col.delete(where={"source": path})          # ponowne indeksowanie nie dubluje
    vecs = get_embedder().encode(chunks, mode="document")
    ids = [hashlib.md5(f"{path}::{i}".encode()).hexdigest() for i in range(len(chunks))]
    col.upsert(
        ids=ids,
        documents=chunks,
        embeddings=vecs.tolist(),
        metadatas=[{"source": path, "filename": os.path.basename(path), "chunk": i}
                   for i in range(len(chunks))],
    )
    return len(chunks)

def index_folder(folder: str) -> int:
    col, total = get_collection(), 0
    for root, _, files in os.walk(folder):
        for f in files:
            try:
                total += index_file(os.path.join(root, f), col)
            except Exception as e:           # jeden zepsuty plik nie może zatrzymać całości
                print(f"[indexer] pominięto {f}: {e}")
    return total