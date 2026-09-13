#!/usr/bin/env python3
"""Frozen V12 ontology-free finite predictive substrate.

The kernel sees only anonymous actions, anonymous observations, ordered
interaction histories, future action strings, and externally supplied future
observation consequences. Hidden world state is not representable here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


Action = int
Observation = int
History = Tuple[Tuple[Action, Observation], ...]
Test = Tuple[Action, ...]
Outcome = Tuple[Observation, ...]


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class ConsequenceTable:
    action_count: int
    observation_count: int
    histories: Tuple[History, ...]
    tests: Tuple[Test, ...]
    outcomes: Tuple[Tuple[Outcome, ...], ...]
    complete: bool
    table_id: str = ""

    def __post_init__(self) -> None:
        if self.action_count <= 0 or self.observation_count <= 0:
            raise ValueError("alphabets must be nonempty")
        if len(self.outcomes) != len(self.histories):
            raise ValueError("history/outcome row mismatch")
        for row in self.outcomes:
            if len(row) != len(self.tests):
                raise ValueError("test/outcome column mismatch")
        for h in self.histories:
            for a, o in h:
                if not (0 <= int(a) < self.action_count):
                    raise ValueError("history action outside alphabet")
                if not (0 <= int(o) < self.observation_count):
                    raise ValueError("history observation outside alphabet")
        for t in self.tests:
            for a in t:
                if not (0 <= int(a) < self.action_count):
                    raise ValueError("test action outside alphabet")
        for row in self.outcomes:
            for out in row:
                for o in out:
                    if not (0 <= int(o) < self.observation_count):
                        raise ValueError("outcome outside alphabet")

    def data(self) -> Any:
        return {
            "table_id": self.table_id,
            "action_count": self.action_count,
            "observation_count": self.observation_count,
            "history_count": len(self.histories),
            "tests": [list(t) for t in self.tests],
            "complete": self.complete,
        }

    def outcome(self, history_index: int, test_index: int) -> Outcome:
        return self.outcomes[int(history_index)][int(test_index)]

    def test_cost(self, test_index: int) -> int:
        return len(self.tests[int(test_index)])

    def interface_key(self) -> Tuple[int, int, Tuple[Test, ...]]:
        return (self.action_count, self.observation_count, self.tests)


def signature(
    table: ConsequenceTable,
    history_index: int,
    active_test_indices: Iterable[int],
) -> Tuple[Outcome, ...]:
    ids = tuple(sorted(int(i) for i in active_test_indices))
    return tuple(table.outcome(history_index, j) for j in ids)


def partition(
    table: ConsequenceTable,
    active_test_indices: Iterable[int],
) -> Tuple[Tuple[int, ...], ...]:
    groups: Dict[Tuple[Outcome, ...], list[int]] = {}
    for i in range(len(table.histories)):
        key = signature(table, i, active_test_indices)
        groups.setdefault(key, []).append(i)
    classes = [tuple(v) for v in groups.values()]
    classes.sort(key=lambda c: (len(c), c))
    return tuple(classes)


def full_partition(table: ConsequenceTable) -> Tuple[Tuple[int, ...], ...]:
    return partition(table, range(len(table.tests)))


def same_partition(
    left: Sequence[Sequence[int]],
    right: Sequence[Sequence[int]],
) -> bool:
    norm = lambda xs: sorted(tuple(sorted(int(x) for x in c)) for c in xs)
    return norm(left) == norm(right)


def code_cost(
    table: ConsequenceTable,
    active_test_indices: Iterable[int],
) -> Tuple[int, int]:
    ids = tuple(sorted(set(int(i) for i in active_test_indices)))
    return (
        len(ids),
        sum(table.test_cost(i) for i in ids),
    )


def code_digest(
    table: ConsequenceTable,
    active_test_indices: Iterable[int],
) -> str:
    ids = tuple(sorted(set(int(i) for i in active_test_indices)))
    return digest_json({
        "interface": [
            table.action_count,
            table.observation_count,
            [list(t) for t in table.tests],
        ],
        "active_tests": list(ids),
    })
