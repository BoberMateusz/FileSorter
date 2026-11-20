import os, re, hashlib
import chromadb
import config
from embedder import get_embedder
from extractors import process_file_for_embedding as process_file   # Person 1: lista stringów


def get_collection():
    client = chromadb.PersistentClient(path=config.DB_PATH)
    tag = re.sub(r"[^a-zA-Z0-9_-]", "_", config.MODEL_NAME)[-40:]
    # inna nazwa kolekcji per model, bo różne modele mają różne wymiary wektorów
    return client.get_or_create_collection(
        name=f"chunks_{tag}", metadata={"hnsw:space": "cosine"}
    )


def index_file(path: str, col=None) -> int:
    col = col or get_collection()
    path = os.path.abspath(path)                 # jedna, stała postać ścieżki w bazie
    col.delete(where={"source": path})           # ponowne indeksowanie nie dubluje
    chunks = [c for c in process_file(path) if c and c.strip()]
    if not chunks:
        return 0
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


def prune_missing(folder: str, col=None) -> int:
    """Usuwa z bazy pliki z podanego folderu, których już nie ma na dysku
    (np. przeniesione albo skasowane). Zwraca liczbę usuniętych plików."""
    col = col or get_collection()
    root = os.path.abspath(folder) + os.sep
    sources = {m["source"] for m in col.get(include=["metadatas"])["metadatas"]}
    removed = 0
    for src in sources:
        if src.startswith(root) and not os.path.exists(src):
            col.delete(where={"source": src})
            removed += 1
    return removed


def index_folder(folder: str) -> int:
    col, total = get_collection(), 0
    prune_missing(folder, col)
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")]     # pomiń ukryte foldery
        for f in files:
            if f.startswith("."):
                continue
            try:
                total += index_file(os.path.join(root, f), col)
            except Exception as e:           # jeden zepsuty plik nie może zatrzymać całości
                print(f"[indexer] pominięto {f}: {e}")
    return total
