import re
from collections.abc import Iterator, MutableSequence, Sequence
from typing import Any, Self, TypeVar


SLUGIFY_RE = re.compile(r"[^a-zA-Z0-9]+")


def get_first(d: dict, *keys: Any) -> Any | None:
    ks = list(keys)
    while ks:
        if (k := ks.pop(0)) in d:
            return d[k]


def slugify(s: str) -> str:
    return SLUGIFY_RE.sub("-", s).lower()


class Node:
    def __post_init__(self) -> None:
        self.prev: Self | None = None
        self.next: Self | None = None


N = TypeVar("N", bound=Node)


class DLList(MutableSequence[N]):
    def __init__(self, values: Sequence[N] = ()) -> None:
        self.head: N | None = None
        self.tail: N | None = None

        it = iter(values)
        first = next(it, None)
        if first is not None:
            cur = first
            self.head = cur
            self.tail = cur

            for v in it:
                cur = v
                cur.prev = self.tail
                self.tail.next = cur
                self.tail = cur

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __iter__(self) -> Iterator[N]:
        cur = self.head
        while cur:
            yield cur
            cur = cur.next

    def __reversed__(self) -> Iterator[N]:
        cur = self.tail
        while cur:
            yield cur
            cur = cur.prev

    def __getitem__(self, key: int | slice) -> N:  # type: ignore
        if isinstance(key, slice):
            raise NotImplementedError

        if key >= 0:
            for v in self:
                if key == 0:
                    return v
                key -= 1

        else:
            for v in reversed(self):
                if key == 0:
                    return v
                key += 1

        raise IndexError

    def __setitem__(self, key: int | slice, value: N):  # type: ignore
        if isinstance(key, slice):
            raise NotImplementedError

        value.prev = self[key].prev
        value.next = self[key].next
        self[key] = value

    def __delitem__(self, key: int | slice):
        if isinstance(key, slice):
            raise NotImplementedError

        node = self[key]
        if node.prev is not None:
            node.prev.next = node.next
        if node.next is not None:
            node.next.prev = node.prev

    def insert(self, index: int, value: N):  # type: ignore
        if index > len(self):
            value.prev = self.tail
            self.tail = value
        else:
            cur = self[index]
            prev = cur.prev
            value.prev = prev
            value.next = cur
            if prev is not None:
                prev.next = value
            else:
                self.head = value
            cur.prev = value

    def append(self, value: N):  # type: ignore
        value.prev = self.tail
        if self.tail is not None:
            self.tail.next = value
        self.tail = value
