
import time

def query_index(query_text: str, top_k: int = 5) -> tuple[list[dict], float]:
    t0 = time.perf_counter()
    results = [
        {"text": "Przykładowy fragment faktury Orange...", "source": "C:/Downloads/faktura.pdf", "filename": "faktura.pdf", "score": 0.85},
        {"text": "Notatka z wykładu o grafach...", "source": "C:/Downloads/notatki.pdf", "filename": "notatki.pdf", "score": 0.71},
    ][:top_k]
    return results, (time.perf_counter() - t0) * 1000