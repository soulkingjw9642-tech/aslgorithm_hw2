"""A string-to-string hash table using linear probing."""

from __future__ import annotations

from dataclasses import dataclass

from src.hash_table import polynomial_hash_details


class _Tombstone:
    pass


_TOMBSTONE = _Tombstone()


@dataclass
class _Entry:
    key: str
    value: str


class LinearProbingHashTable:
    """Open-addressed hash table with wraparound probing and tombstones."""

    slot_label = "Slot"
    strategy = "linear probing"
    _MAX_LOAD_FACTOR = 0.75

    def __init__(
        self, capacity: int = 8, max_load_factor: float | None = _MAX_LOAD_FACTOR
    ) -> None:
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an integer")
        if capacity < 1:
            raise ValueError("capacity must be positive")
        if max_load_factor is not None:
            if not isinstance(max_load_factor, (int, float)) or isinstance(
                max_load_factor, bool
            ):
                raise TypeError("max_load_factor must be a number or None")
            if max_load_factor <= 0 or max_load_factor > 1:
                raise ValueError("max_load_factor must be in (0, 1] or None")
        self._slots: list[_Entry | _Tombstone | None] = [None] * capacity
        self._max_load_factor = max_load_factor
        self._size = 0
        self.last_lookup_probes = 0
        self.last_lookup_trace: list[str] = []
        self.last_lookup_slots: list[int] = []

    def __len__(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return len(self._slots)

    def hash_details(self, key: str) -> tuple[int, tuple[int, ...]]:
        self._validate_key(key)
        return polynomial_hash_details(key, self.capacity)

    def slot_entries(self, index: int) -> tuple[tuple[str, str], ...]:
        entry = self._slots[index]
        if isinstance(entry, _Entry):
            return ((entry.key, entry.value),)
        return ()

    def put(self, key: str, value: str) -> None:
        self._validate_key(key)
        self._validate_value(value)
        found, insertion = self._find_slot(key)
        if found is not None:
            entry = self._slots[found]
            assert isinstance(entry, _Entry)
            entry.value = value
            return

        if (
            self._max_load_factor is not None
            and (self._size + 1) / self.capacity > self._max_load_factor
        ):
            self._resize(self.capacity * 2)
            _, insertion = self._find_slot(key)
        if insertion is None:
            raise OverflowError("hash table is full")

        self._slots[insertion] = _Entry(key, value)
        self._size += 1

    def get(self, key: str) -> str:
        self._validate_key(key)
        found, _ = self._find_slot(key)
        if found is None:
            raise KeyError(key)
        entry = self._slots[found]
        assert isinstance(entry, _Entry)
        return entry.value

    def contains(self, key: str) -> bool:
        self._validate_key(key)
        found, _ = self._find_slot(key)
        return found is not None

    def delete(self, key: str) -> None:
        self._validate_key(key)
        found, _ = self._find_slot(key)
        if found is None:
            raise KeyError(key)
        self._slots[found] = _TOMBSTONE
        self._size -= 1

    def _find_slot(self, key: str) -> tuple[int | None, int | None]:
        start, _ = self.hash_details(key)
        first_tombstone = None
        self.last_lookup_probes = 0
        self.last_lookup_trace = []
        self.last_lookup_slots = []

        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            entry = self._slots[index]
            self.last_lookup_probes += 1
            self.last_lookup_slots.append(index)
            if entry is None:
                self.last_lookup_trace.append("<empty>")
                insertion = first_tombstone if first_tombstone is not None else index
                return None, insertion
            if isinstance(entry, _Tombstone):
                self.last_lookup_trace.append("<tombstone>")
                if first_tombstone is None:
                    first_tombstone = index
            else:
                self.last_lookup_trace.append(entry.key)
                if entry.key == key:
                    return index, index

        return None, first_tombstone

    def _resize(self, capacity: int) -> None:
        old_slots = self._slots
        self._slots = [None] * capacity
        self._size = 0
        for entry in old_slots:
            if isinstance(entry, _Entry):
                start, _ = self.hash_details(entry.key)
                for offset in range(self.capacity):
                    index = (start + offset) % self.capacity
                    if self._slots[index] is None:
                        self._slots[index] = entry
                        self._size += 1
                        break

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    @staticmethod
    def _validate_value(value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("value must be a string")
