import asyncio
import time
from collections.abc import Callable, Hashable
from dataclasses import dataclass

type Clock = Callable[[], float]


@dataclass(frozen=True, slots=True)
class Entry[V]:
    value: V
    stored_at: float


class TimedCache[K: Hashable, V]:
    def __init__(self, max_entries: int = 256, clock: Clock = time.time):
        self.max_entries = max_entries
        self.clock = clock
        self._entries: dict[K, Entry[V]] = {}

    def get(self, key: K) -> Entry[V] | None:
        return self._entries.get(key)

    def age(self, entry: Entry[V]) -> float:
        return self.clock() - entry.stored_at

    def set(self, key: K, value: V, stored_at: float | None = None) -> Entry[V]:
        if key not in self._entries and len(self._entries) >= self.max_entries:
            self._entries.pop(next(iter(self._entries)))
        entry = Entry(value, self.clock() if stored_at is None else stored_at)
        self._entries[key] = entry
        return entry

    def clear(self) -> None:
        self._entries.clear()


class KeyedLocks[K: Hashable]:
    def __init__(self) -> None:
        self._locks: dict[K, asyncio.Lock] = {}

    def __call__(self, key: K) -> asyncio.Lock:
        return self._locks.setdefault(key, asyncio.Lock())
