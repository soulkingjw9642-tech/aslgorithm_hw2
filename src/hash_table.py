"""A string-to-string hash table using separate chaining."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _Node:
    key: str
    value: str
    next: _Node | None = None


class HashTable:
    """A hash table with a deterministic polynomial string hash."""

    _MAX_LOAD_FACTOR = 0.75

    def __init__(
        self, capacity: int = 8, max_load_factor: float | None = _MAX_LOAD_FACTOR
    ) -> None:
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an integer")
        if capacity < 1:
            raise ValueError("capacity must be positive")
        if max_load_factor is not None and max_load_factor <= 0:
            raise ValueError("max_load_factor must be positive or None")
        self._buckets: list[_Node | None] = [None] * capacity
        self._size = 0
        self._max_load_factor = max_load_factor
        self.last_lookup_probes = 0
        self.last_lookup_trace: list[str] = []

    def __len__(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    @property
    def buckets(self) -> tuple[_Node | None, ...]:
        return tuple(self._buckets)

    def hash_details(self, key: str) -> tuple[int, tuple[int, ...]]:
        """Return the bucket index and each intermediate polynomial hash."""
        self._validate_key(key)
        value = 0
        steps = []
        for character in key:
            value = (31 * value + ord(character)) % self.capacity
            steps.append(value)
        return value, tuple(steps)

    def put(self, key: str, value: str) -> None:
        self._validate_key(key)
        self._validate_value(value)
        index, _ = self.hash_details(key)
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self._size += 1
        if (
            self._max_load_factor is not None
            and self._size / self.capacity > self._max_load_factor
        ):
            self._resize(self.capacity * 2)

    def get(self, key: str) -> str:
        self._validate_key(key)
        index, _ = self.hash_details(key)
        node = self._buckets[index]
        self.last_lookup_probes = 0
        self.last_lookup_trace = []
        while node is not None:
            self.last_lookup_probes += 1
            self.last_lookup_trace.append(node.key)
            if node.key == key:
                return node.value
            node = node.next
        raise KeyError(key)

    def contains(self, key: str) -> bool:
        self._validate_key(key)
        index, _ = self.hash_details(key)
        node = self._buckets[index]
        self.last_lookup_probes = 0
        self.last_lookup_trace = []
        while node is not None:
            self.last_lookup_probes += 1
            self.last_lookup_trace.append(node.key)
            if node.key == key:
                return True
            node = node.next
        return False

    def _resize(self, capacity: int) -> None:
        old_buckets = self._buckets
        self._buckets = [None] * capacity
        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next
                index, _ = self.hash_details(node.key)
                node.next = self._buckets[index]
                self._buckets[index] = node
                node = next_node

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    @staticmethod
    def _validate_value(value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("value must be a string")
