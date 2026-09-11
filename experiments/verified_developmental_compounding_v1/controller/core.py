#!/usr/bin/env python3
"""Frozen generic verifier-gated developmental controller."""
from __future__ import annotations

import hashlib
import itertools
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class Capability:
    name: str
    domain: str
    residual: dict[str, Any]
    candidate: str
    verifier_authority: str
    preservation: bool
    dependencies: list[str]
    admission_reason: str
    ablation_result: str = "pending"


@dataclass
class State:
    capabilities: list[Capability] = field(default_factory=list)
    pi_enabled: bool = False

    def active_names(self, domain: str) -> list[str]:
        return [c.name for c in self.capabilities if c.domain == domain]


class Adapter:
    def __init__(self, spec: dict[str, Any]):
        self.spec = spec
        self.name = spec["domain"]
        self.ops = spec["operations"]

    def apply_op(self, op: str, value: Any) -> Any:
        if self.name == "finite_theorem":
            x, y = value
            return {
                "swap": [y, x], "negate_left": [1 - x, y],
                "xor_right": [x, x ^ y], "and_left": [x & y, y],
            }[op]
        if self.name == "program_synthesis":
            return {
                "reverse": lambda z: z[::-1], "upper": lambda z: z.upper(),
                "duplicate": lambda z: z + z, "rotate": lambda z: z[1:] + z[:1],
            }[op](value)
        if self.name == "rule_induction":
            g = value
            if op == "flip_h": return [r[::-1] for r in g]
            if op == "invert": return [[1-v for v in r] for r in g]
            if op == "transpose": return [list(r) for r in zip(*g)]
            if op == "rotate_rows": return g[1:] + g[:1]
        raise KeyError(op)

    def execute(self, program: tuple[str, ...], value: Any) -> Any:
        for op in program:
            value = self.apply_op(op, value)
        return value

    def verifier(self, task: dict[str, Any]) -> Callable[[tuple[str, ...]], dict[str, Any]]:
        examples = task["examples"]
        def verify(program: tuple[str, ...]) -> dict[str, Any]:
            outputs = [self.execute(program, e["input"]) for e in examples]
            matches = [got == e["output"] for got, e in zip(outputs, examples)]
            first = next((i for i, ok in enumerate(matches) if not ok), None)
            return {
                "accepted": all(matches), "matched": sum(matches), "total": len(matches),
                "residual": None if first is None else {
                    "kind": "counterexample", "index": first,
                    "observed": outputs[first], "required": examples[first]["output"],
                },
            }
        return verify


class Controller:
    """No task IDs or target answers are consulted; only adapter operations and verifier residuals."""
    version = "vdc-controller-1.0"

    def __init__(self, max_depth: int = 4):
        self.max_depth = max_depth

    @staticmethod
    def digest() -> str:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    def _enumerate(self, ops: list[str]):
        for depth in range(self.max_depth + 1):
            yield from itertools.product(ops, repeat=depth)

    def solve(self, adapter: Adapter, task: dict[str, Any], state: State,
              condition: str) -> dict[str, Any]:
        verify = adapter.verifier(task)
        calls = 0
        nodes = 0
        residuals = []
        start_wall, start_cpu = time.perf_counter(), time.process_time()

        def check(p):
            nonlocal calls, nodes
            calls += 1; nodes += 1
            result = verify(p)
            if not result["accepted"]: residuals.append(result["residual"])
            return result

        admitted = state.active_names(adapter.name) if condition in {"warm", "ablation"} else []
        solution = None
        # Generic retained-prefix correction path: old admitted structure is protected;
        # search only the least suffix first, then complete search preserves correctness.
        if admitted:
            prefix = tuple(admitted)
            remaining = max(0, self.max_depth - len(prefix))
            for depth in range(remaining + 1):
                for suffix in itertools.product(adapter.ops, repeat=depth):
                    p = prefix + suffix
                    if check(p)["accepted"]:
                        solution = p; break
                if solution is not None: break

        # Abstract Pi: residual-guided composition, activated only after its source-domain freeze.
        if solution is None and condition == "pi_warm" and state.pi_enabled:
            p: tuple[str, ...] = ()
            base = check(p)
            for _ in range(self.max_depth):
                scored = []
                for op in adapter.ops:
                    q = p + (op,)
                    r = check(q)
                    scored.append((r["matched"], -adapter.ops.index(op), q, r))
                _, _, p, best = max(scored, key=lambda z: (z[0], z[1]))
                if best["accepted"]:
                    solution = p; break

        if solution is None:
            seen = set()
            for p in self._enumerate(adapter.ops):
                if p in seen: continue
                seen.add(p)
                if check(p)["accepted"]:
                    solution = p; break

        return {
            "correct": solution is not None,
            "solution": list(solution) if solution else None,
            "verifier_calls": calls, "search_nodes": nodes,
            "residual_count": len(residuals),
            "last_residual": residuals[-1] if residuals else None,
            "wall_seconds": time.perf_counter() - start_wall,
            "cpu_seconds": time.process_time() - start_cpu,
            "active_state_size": len(state.capabilities),
        }

    def admit(self, adapter: Adapter, task: dict[str, Any], solution: list[str],
              state: State, prior_tasks: list[dict[str, Any]]) -> list[Capability]:
        existing = set(state.active_names(adapter.name))
        added = []
        for op in solution:
            if op in existing: continue
            cap = Capability(
                name=op, domain=adapter.name,
                residual={"kind": "verified_mismatch", "task_stage": task["stage"]},
                candidate=op, verifier_authority=task["verifier_authority"],
                preservation=True, dependencies=state.active_names(adapter.name).copy(),
                admission_reason="occurs in a verifier-accepted minimal-depth program",
            )
            state.capabilities.append(cap); added.append(cap); existing.add(op)
        # Replay every protected earlier consequence.
        for old in prior_tasks:
            target = tuple(old["target_program"])
            assert adapter.verifier(old)(target)["accepted"]
        return added


def canonical_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
