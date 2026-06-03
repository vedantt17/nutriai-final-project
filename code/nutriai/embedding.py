from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

import numpy as np


TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    """Dependency-light dense text embeddings for offline grading.

    The vectorizer uses signed feature hashing over unigrams and adjacent
    bigrams. It is deterministic, fast on 5k+ records, and keeps the app
    runnable without downloading model weights during a live demo.
    """

    def __init__(self, dimensions: int = 160):
        self.dimensions = dimensions

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return TOKEN_RE.findall((text or "").lower())

    def _features(self, text: str) -> Iterable[str]:
        tokens = self._tokens(text)
        for token in tokens:
            yield token
        for left, right in zip(tokens, tokens[1:]):
            yield f"{left}_{right}"

    def encode(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        for feature in self._features(text):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            raw = int.from_bytes(digest, "big")
            index = raw % self.dimensions
            sign = 1.0 if (raw >> 9) & 1 else -1.0
            vector[index] += sign
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
        return vector

    def encode_many(self, texts: Iterable[str]) -> np.ndarray:
        vectors = [self.encode(text) for text in texts]
        if not vectors:
            return np.zeros((0, self.dimensions), dtype=np.float32)
        return np.vstack(vectors)

    def similarity(self, query: str, matrix: np.ndarray) -> np.ndarray:
        if matrix.size == 0:
            return np.zeros(0, dtype=np.float32)
        query_vector = self.encode(query)
        return matrix @ query_vector
