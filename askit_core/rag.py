"""Reference RAG building blocks (used by Lab 2C and later labs).
Labs 2A/2B ask you to write your own versions first - try before you peek!
"""
import json

import numpy as np

EMBED_MODEL = "amazon.titan-embed-text-v2:0"


def embed_text(client, text, dimensions=512):
    """Titan Text Embeddings v2 -> list[float] (normalised)."""
    body = json.dumps({"inputText": text, "dimensions": dimensions, "normalize": True})
    resp = client.invoke_model(modelId=EMBED_MODEL, body=body)
    return json.loads(resp["body"].read())["embedding"]


def cosine(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def chunk_words(text, size=80, overlap=20):
    words = text.split()
    step = max(1, size - overlap)
    return [" ".join(words[i:i + size]) for i in range(0, max(len(words) - overlap, 1), step)]


class SimpleIndex:
    """A tiny in-memory vector store: a list of chunks + a numpy matrix of vectors."""

    def __init__(self, chunks=None):
        self.chunks = chunks or []  # each: {"id", "doc_id", "text", "vector"}

    @classmethod
    def build(cls, client, docs, size=80, overlap=20):
        chunks = []
        for doc_id, text in docs.items():
            for i, piece in enumerate(chunk_words(text, size, overlap)):
                chunks.append({"id": f"{doc_id}#{i}", "doc_id": doc_id, "text": piece,
                               "vector": embed_text(client, piece)})
        return cls(chunks)

    def search(self, client, query, k=3):
        q = np.asarray(embed_text(client, query))
        m = np.asarray([c["vector"] for c in self.chunks])
        scores = m @ q / (np.linalg.norm(m, axis=1) * np.linalg.norm(q))
        top = np.argsort(-scores)[:k]
        return [{**{k2: v for k2, v in self.chunks[i].items() if k2 != "vector"}, "score": float(scores[i])} for i in top]

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.chunks), encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls(json.loads(path.read_text(encoding="utf-8")))
