from __future__ import annotations

import hashlib
import math


class BloomFilter:
    """Small deterministic Bloom filter used for fast allergen pre-screening."""

    def __init__(self, expected_items: int = 64, false_positive_rate: float = 0.01):
        expected_items = max(1, expected_items)
        false_positive_rate = min(max(false_positive_rate, 0.001), 0.25)
        size = -expected_items * math.log(false_positive_rate) / (math.log(2) ** 2)
        self.size = max(64, int(size))
        self.hash_count = max(3, int((self.size / expected_items) * math.log(2)))
        self.bits = bytearray(self.size)

    @staticmethod
    def _normalize(item: str) -> str:
        return item.strip().lower().replace("_", " ").replace("-", " ")

    def _hashes(self, item: str):
        normalized = self._normalize(item).encode("utf-8")
        for salt in range(self.hash_count):
            digest = hashlib.blake2b(normalized, digest_size=8, person=f"nutri{salt}".encode("utf-8")[:16])
            yield int.from_bytes(digest.digest(), "big") % self.size

    def add(self, item: str) -> None:
        if not item:
            return
        for index in self._hashes(item):
            self.bits[index] = 1

    def __contains__(self, item: str) -> bool:
        if not item:
            return False
        return all(self.bits[index] for index in self._hashes(item))
