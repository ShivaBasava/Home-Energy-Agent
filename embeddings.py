"""Embedding backends for Chroma. EMBED_BACKEND=ollama (default) or hash (offline smoke test)."""
import hashlib, math, os, re

def _hash_embed(text: str, dim: int = 256) -> list[float]:
    vec = [0.0] * dim
    for tok in re.findall(r"[a-z0-9]+", text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

class Embedder:
    def __init__(self):
        self.backend = os.getenv("EMBED_BACKEND", "ollama")
        self.model = os.getenv("EMBED_MODEL", "nomic-embed-text")

    def __call__(self, input):
        if self.backend == "hash":
            return [_hash_embed(t) for t in input]
        import ollama
        return ollama.embed(model=self.model, input=list(input))["embeddings"]

    def embed_query(self, input):
        return self(input)

    @staticmethod
    def name() -> str:
        return "energy-embedder"
