import numpy as np
import config

class Embedder:
    def __init__(self):
        self.backend = getattr(config, "EMBED_BACKEND", "fastembed")  # "fastembed" | "ollama"
        if self.backend == "fastembed":
            from fastembed import TextEmbedding
            self.model = TextEmbedding(model_name=config.MODEL_NAME)
        else:
            import ollama
            self.ollama = ollama

    def _prep(self, texts, mode):
        # prefiksy tylko dla EmbeddingGemma (Ollama)
        if self.backend != "ollama":
            return texts
        if mode == "query":
            return [f"task: search result | query: {t}" for t in texts]
        if mode == "classify":
            return [f"task: classification | query: {t}" for t in texts]
        return [f"title: none | text: {t}" for t in texts]   # mode == "document"

    def encode(self, texts: list[str], mode: str = "document") -> np.ndarray:
        texts = self._prep(texts, mode)
        if self.backend == "fastembed":
            vecs = list(self.model.embed(texts))
        else:
            vecs = self.ollama.embed(model=config.MODEL_NAME, input=texts)["embeddings"]
        arr = np.asarray(vecs, dtype=np.float32)
        return arr / np.linalg.norm(arr, axis=1, keepdims=True)   # normalizacja

_embedder = None
def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()      # model ładuje się raz
    return _embedder