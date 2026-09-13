#!/usr/bin/env python3
"""Frozen V28 finite partition / consequence substrate."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Tuple


Partition = Tuple[Tuple[int, ...], ...]


@dataclass(frozen=True)
class MultiContextWorld:
    state_count: int
    context_names: Tuple[str, ...]
    future_signatures: Tuple[Tuple[Tuple[int, ...], ...], ...]
    record_signatures: Tuple[Tuple[Tuple[int, ...], ...], ...] | None = None
    complete: bool = True
    world_id: str = ""

    def __post_init__(self) -> None:
        if self.state_count <= 0:
            raise ValueError("positive state_count required")
        if len(self.future_signatures) != len(self.context_names):
            raise ValueError("context/future mismatch")
        for ctx in self.future_signatures:
            if len(ctx) != self.state_count:
                raise ValueError("future state count mismatch")
        if self.record_signatures is not None:
            if len(self.record_signatures) != len(self.context_names):
                raise ValueError("context/record mismatch")
            for ctx in self.record_signatures:
                if len(ctx) != self.state_count:
                    raise ValueError("record state count mismatch")

    def states(self) -> Tuple[int, ...]:
        return tuple(range(self.state_count))


def canonical_partition(blocks: Iterable[Iterable[int]]) -> Partition:
    out = [tuple(sorted(int(x) for x in block)) for block in blocks]
    out = [b for b in out if b]
    out.sort(key=lambda b: (b[0], len(b), b))
    return tuple(out)


def all_partitions(n: int) -> Iterator[Partition]:
    """Generate every set partition of {0,...,n-1} exactly once."""
    if n <= 0:
        return

    blocks: list[list[int]] = []

    def rec(i: int):
        if i == n:
            yield canonical_partition(blocks)
            return
        for j in range(len(blocks)):
            blocks[j].append(i)
            yield from rec(i + 1)
            blocks[j].pop()
        blocks.append([i])
        yield from rec(i + 1)
        blocks.pop()

    yield from rec(0)


def partition_from_signatures(
    signatures: Tuple[Tuple[int, ...], ...],
) -> Partition:
    groups: dict[Tuple[int, ...], list[int]] = {}
    for i, sig in enumerate(signatures):
        groups.setdefault(tuple(sig), []).append(i)
    return canonical_partition(groups.values())


def block_count(p: Partition) -> int:
    return len(p)


def block_size_signature(p: Partition) -> Tuple[int, ...]:
    return tuple(sorted(len(b) for b in p))


def block_of(p: Partition, x: int) -> Tuple[int, ...]:
    for b in p:
        if x in b:
            return b
    raise KeyError(x)


def refines(finer: Partition, coarser: Partition) -> bool:
    """True iff every finer block is contained in some coarser block."""
    return all(any(set(b) <= set(c) for c in coarser) for b in finer)


def incomparable(a: Partition, b: Partition) -> bool:
    return not refines(a, b) and not refines(b, a)


def sufficient(
    p: Partition,
    signatures: Tuple[Tuple[int, ...], ...],
) -> bool:
    for block in p:
        vals = {tuple(signatures[x]) for x in block}
        if len(vals) != 1:
            return False
    return True


def record_lawful(
    p: Partition,
    record_signatures: Tuple[Tuple[int, ...], ...],
) -> bool:
    """A grain may not distinguish states the record channel cannot distinguish."""
    q_record = partition_from_signatures(record_signatures)
    return refines(q_record, p)


def relabel_partition(p: Partition, permutation: Tuple[int, ...]) -> Partition:
    return canonical_partition(
        tuple(permutation[x] for x in block)
        for block in p
    )
