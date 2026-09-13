from __future__ import annotations
from collections import defaultdict
from itertools import permutations
from typing import Any

from basis import Machine, World, binary_strings_upto, run_machine


class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str, Any] | None:
        if not world.complete or not world.rows:
            return {"status": "UNKNOWN_AUTHORITY"}
        if any(r.consequence is None for r in world.rows):
            return {"status": "UNKNOWN_AUTHORITY"}
        if any(any(int(b) not in (0, 1) for b in r.stream) for r in world.rows):
            return {"status": "INVALID_SYMBOL_ALPHABET"}
        max_len = max(len(r.stream) for r in world.rows)
        observed = {tuple(int(b) for b in r.stream) for r in world.rows}
        required = set(binary_strings_upto(max_len))
        if observed != required:
            return {"status": "UNKNOWN_AUTHORITY"}
        if len(observed) != len(world.rows):
            return {"status": "INVALID_DUPLICATE_ENCOUNTER"}
        return None

    @staticmethod
    def _mapping(world: World) -> dict[tuple[int, ...], int]:
        return {tuple(int(b) for b in r.stream): int(r.consequence) for r in world.rows}

    @staticmethod
    def _candidate(mapping: dict[tuple[int, ...], int], max_len: int, horizon: int) -> dict[str, Any] | None:
        depth = max_len - horizon
        if depth < 1:
            return None
        suffixes = binary_strings_upto(horizon)
        prefixes = binary_strings_upto(depth)

        def signature(prefix: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(mapping[prefix + suffix] for suffix in suffixes)

        sig_by_prefix = {p: signature(p) for p in prefixes}
        signatures = sorted(set(sig_by_prefix.values()), key=repr)
        sid = {sig: i for i, sig in enumerate(signatures)}
        by_sig: dict[tuple[int, ...], list[tuple[int, ...]]] = defaultdict(list)
        for p, sig in sig_by_prefix.items():
            by_sig[sig].append(p)

        outputs = [0] * len(signatures)
        transitions: list[tuple[int, int] | None] = [None] * len(signatures)
        for sig, ps in by_sig.items():
            q = sid[sig]
            outputs[q] = int(mapping[ps[0]])
            source_prefixes = [p for p in ps if len(p) < depth]
            if not source_prefixes:
                return None
            dest = []
            for b in (0, 1):
                ds = {sid[sig_by_prefix[p + (b,)]] for p in source_prefixes}
                if len(ds) != 1:
                    return None
                dest.append(next(iter(ds)))
            transitions[q] = (int(dest[0]), int(dest[1]))

        if any(t is None for t in transitions):
            return None
        machine = Machine(
            initial=int(sid[sig_by_prefix[()]]),
            outputs=tuple(int(x) for x in outputs),
            transitions=tuple(t for t in transitions if t is not None),
        )
        if any(run_machine(machine, s) != y for s, y in mapping.items()):
            return None

        self_loops = sum(1 for q, t in enumerate(machine.transitions) for z in t if int(z) == q)
        changing_edges = 2 * len(machine.transitions) - self_loops
        return {
            "machine": machine,
            "state_count": len(machine.outputs),
            "distinguishing_horizon": int(horizon),
            "construction_depth": int(depth),
            "self_loop_count": int(self_loops),
            "state_changing_edge_count": int(changing_edges),
        }

    def synthesize(self, world: World, *, verification_enabled: bool = True) -> dict[str, Any]:
        auth = self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status": "UNKNOWN_NO_VERIFIER", "state_count": 0}

        mapping = self._mapping(world)
        max_len = max(len(s) for s in mapping)
        candidates = []
        for horizon in range(max_len + 1):
            c = self._candidate(mapping, max_len, horizon)
            if c is not None:
                candidates.append(c)
        if not candidates:
            return {"status": "CERTIFIED_CURRENT_RESIDUAL_CLASS_INADEQUATE", "state_count": 0}

        candidates.sort(key=lambda c: (c["state_count"], c["distinguishing_horizon"], c["construction_depth"]))
        best = candidates[0]
        machine: Machine = best["machine"]
        replay = [run_machine(machine, r.stream) for r in world.rows]
        exact = all(v == int(r.consequence) for v, r in zip(replay, world.rows))
        return {
            "status": "VERIFIED" if exact else "REPLAY_FAILED",
            "max_training_length": max_len,
            "state_count": best["state_count"],
            "distinguishing_horizon": best["distinguishing_horizon"],
            "construction_depth": best["construction_depth"],
            "self_loop_count": best["self_loop_count"],
            "state_changing_edge_count": best["state_changing_edge_count"],
            "candidate_count": len(candidates),
            "machine": machine.data(),
            "exact_training_replay": exact,
            "_machine": machine,
        }

    @staticmethod
    def canonical_structure(machine: Machine) -> tuple:
        n = len(machine.outputs)
        best = None
        for perm in permutations(range(n)):
            inv = {old: new for new, old in enumerate(perm)}
            for symbol_order in ((0, 1), (1, 0)):
                raw_outputs = [int(machine.outputs[old]) for old in perm]
                label_map = {}
                canon_outputs = []
                for y in raw_outputs:
                    if y not in label_map:
                        label_map[y] = len(label_map)
                    canon_outputs.append(label_map[y])
                trans = []
                for old in perm:
                    t = machine.transitions[old]
                    trans.append(tuple(inv[int(t[b])] for b in symbol_order))
                enc = (inv[int(machine.initial)], tuple(canon_outputs), tuple(trans))
                if best is None or enc < best:
                    best = enc
        assert best is not None
        return best
