import time
from embedder import get_embedder
from indexer import get_collection

REVIEW = "Do przejrzenia"


def query_index(query_text: str, top_k: int = 5) -> tuple[list[dict], float]:
    t0 = time.perf_counter()
    col = get_collection()
    if col.count() == 0:
        return [], (time.perf_counter() - t0) * 1000
    vec = get_embedder().encode([query_text], mode="query")[0]
    r = col.query(query_embeddings=[vec.tolist()], n_results=top_k)
    results = [
        {"text": doc, "source": meta["source"], "filename": meta["filename"],
         "score": round(1 - dist, 4)}           # cosine distance -> similarity
        for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
    ]
    return results, (time.perf_counter() - t0) * 1000


_folder_cache = {}


def _folder_vectors(folder_descriptions: dict):
    """Wektory opisów folderów - liczone raz i trzymane w cache."""
    key = repr(folder_descriptions)
    if key not in _folder_cache:
        flat, owner = [], []
        for name, descs in folder_descriptions.items():
            for d in ([descs] if isinstance(descs, str) else descs):
                flat.append(d)
                owner.append(name)
        _folder_cache[key] = (owner, get_embedder().encode(flat, mode="classify"))
    return _folder_cache[key]


def _scores_per_folder(sims_row, owner) -> dict:
    scores = {}
    for name, s in zip(owner, sims_row):              # wynik folderu = najlepszy opis
        scores[name] = max(scores.get(name, -1.0), float(s))
    return scores


def suggest_folder(text: str, folder_descriptions: dict, threshold: float = 0.30,
                   return_scores: bool = False):
    """Folder dla JEDNEGO fragmentu tekstu."""
    owner, dvecs = _folder_vectors(folder_descriptions)
    v = get_embedder().encode([text[:1000]], mode="classify")[0]
    scores = _scores_per_folder(dvecs @ v, owner)
    best = max(scores, key=scores.get)
    result = best if scores[best] >= threshold else REVIEW
    return (result, scores) if return_scores else result


def suggest_folder_for_file(chunks: list[str], folder_descriptions: dict,
                            threshold: float = 0.30, top_k: int = 3, max_chunks: int | None = None):
    """Folder dla CAŁEGO pliku.

    Koduje chunki JEDNYM wywołaniem modelu (max_chunks=None -> wszystkie;
    ustaw np. 20, jeśli długie PDF-y będą liczyć się za wolno). Wynik folderu = średnia z top_k najlepszych chunków.
    Zwraca (folder, wynik, margines, ranking).
    """
    if not chunks:
        return REVIEW, None, None, []

    owner, dvecs = _folder_vectors(folder_descriptions)
    cvecs = get_embedder().encode([c[:1000] for c in chunks[:max_chunks]], mode="classify")
    sims = cvecs @ dvecs.T                            # macierz: chunki x opisy

    per_folder = {}
    for row in sims:
        for name, s in _scores_per_folder(row, owner).items():
            per_folder.setdefault(name, []).append(s)

    avg = {name: sum(sorted(v, reverse=True)[:top_k]) / min(top_k, len(v))
           for name, v in per_folder.items()}
    ranked = sorted(avg.items(), key=lambda x: x[1], reverse=True)
    best, score = ranked[0]
    margin = score - ranked[1][1] if len(ranked) > 1 else score
    return (best if score >= threshold else REVIEW), score, margin, ranked