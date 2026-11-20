import time
from embedder import get_embedder
from indexer import get_collection

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

def suggest_folder(text: str, folder_descriptions: dict, threshold: float = 0.30,
                   return_scores: bool = False):
    emb = get_embedder()
    key = repr(folder_descriptions)
    if key not in _folder_cache:                      # opisy liczysz raz
        flat, owner = [], []
        for name, descs in folder_descriptions.items():
            for d in ([descs] if isinstance(descs, str) else descs):
                flat.append(d)
                owner.append(name)
        _folder_cache[key] = (owner, emb.encode(flat, mode="classify"))
    owner, dvecs = _folder_cache[key]

    v = emb.encode([text[:1000]], mode="classify")[0]
    sims = dvecs @ v
    scores = {}
    for name, s in zip(owner, sims):                  # wynik folderu = najlepszy opis
        scores[name] = max(scores.get(name, -1.0), float(s))
    best = max(scores, key=scores.get)
    result = best if scores[best] >= threshold else "Do przejrzenia"
    return (result, scores) if return_scores else result