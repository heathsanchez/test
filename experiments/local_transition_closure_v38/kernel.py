from __future__ import annotations
from collections import defaultdict
from itertools import permutations
from typing import Any

from basis import PartialMachine, World, suffixes_upto


class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str, Any] | None:
        if not world.complete_authority or not world.rows:
            return {"status": "UNKNOWN_AUTHORITY"}
        if any(r.consequence is None for r in world.rows):
            return {"status": "UNKNOWN_AUTHORITY"}

        histories = [tuple(int(b) for b in r.history) for r in world.rows]
        if any(any(b not in (0,1) for b in h) for h in histories):
            return {"status": "INVALID_SYMBOL_ALPHABET"}
        if len(set(histories)) != len(histories):
            return {"status": "INVALID_DUPLICATE_HISTORY"}
        observed = set(histories)
        if () not in observed:
            return {"status": "UNKNOWN_AUTHORITY"}

        for h in observed:
            for k in range(len(h) + 1):
                if h[:k] not in observed:
                    return {"status": "UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def _mapping(world: World) -> dict[tuple[int,...], int]:
        return {
            tuple(int(b) for b in r.history): int(r.consequence)
            for r in world.rows
        }

    @staticmethod
    def _supported_prefixes(
        mapping: dict[tuple[int,...], int],
        horizon: int,
    ) -> tuple[tuple[int,...], ...]:
        suffixes = suffixes_upto(horizon)
        out = []
        for p in mapping:
            if all(p + s in mapping for s in suffixes):
                out.append(p)
        return tuple(sorted(out, key=lambda x: (len(x), x)))

    @staticmethod
    def _candidate(
        mapping: dict[tuple[int,...], int],
        horizon: int,
    ) -> dict[str, Any] | None:
        suffixes = suffixes_upto(horizon)
        supported = Kernel._supported_prefixes(mapping, horizon)
        if not supported:
            return None

        def signature(p: tuple[int,...]) -> tuple[int,...]:
            return tuple(int(mapping[p+s]) for s in suffixes)

        sig_by_prefix = {p: signature(p) for p in supported}
        signatures = tuple(sorted(set(sig_by_prefix.values()), key=repr))
        sid = {sig:i for i,sig in enumerate(signatures)}

        reps: dict[tuple[int,...], list[tuple[int,...]]] = defaultdict(list)
        for p,sig in sig_by_prefix.items():
            reps[sig].append(p)

        transitions: list[tuple[int|None,int|None]] = []
        warranted_edges = []
        stable_states = []

        for sig in signatures:
            row = []
            for symbol in (0,1):
                targets = {
                    sig_by_prefix[p+(symbol,)]
                    for p in reps[sig]
                    if p+(symbol,) in sig_by_prefix
                }
                if len(targets) > 1:
                    return None
                if not targets:
                    row.append(None)
                    continue

                target_sig = next(iter(targets))
                row.append(int(sid[target_sig]))
                warranted_edges.append({
                    "source_signature": tuple(int(x) for x in sig),
                    "symbol": int(symbol),
                    "target_signature": tuple(int(x) for x in target_sig),
                })

            transitions.append(tuple(row))
            if all(z is not None for z in row):
                stable_states.append(int(sid[sig]))

        machine = PartialMachine(
            initial=int(sid[sig_by_prefix[()]]),
            outputs=tuple(int(sig[0]) for sig in signatures),
            transitions=tuple(transitions),
            signatures=signatures,
        )

        cycle = Kernel._spanning_cycle(machine)
        warranted_count = sum(
            1 for row in machine.transitions for z in row if z is not None
        )
        unresolved_count = 2*len(machine.transitions) - warranted_count

        return {
            "machine": machine,
            "state_count": len(signatures),
            "supported_prefix_count": len(supported),
            "warranted_transition_count": int(warranted_count),
            "unresolved_transition_count": int(unresolved_count),
            "locally_stable_state_ids": tuple(stable_states),
            "locally_stable_state_count": len(stable_states),
            "whole_machine_stable": unresolved_count == 0,
            "spanning_warranted_cycle": cycle is not None,
            "spanning_cycle_state_ids": None if cycle is None else tuple(int(q) for q in cycle),
            "warranted_edges": tuple(warranted_edges),
            "signature_set": signatures,
            "distinguishing_horizon": int(horizon),
        }

    @staticmethod
    def _spanning_cycle(machine: PartialMachine) -> tuple[int,...] | None:
        n = len(machine.outputs)
        if n == 0:
            return None
        if n == 1:
            q = 0
            if any(z == q for z in machine.transitions[q] if z is not None):
                return (q,)
            return None

        adjacency = {
            q: {int(z) for z in machine.transitions[q] if z is not None}
            for q in range(n)
        }
        anchor = 0
        others = [q for q in range(1,n)]
        for perm in permutations(others):
            cyc = (anchor,) + tuple(perm)
            ok = True
            for i,q in enumerate(cyc):
                nxt = cyc[(i+1) % len(cyc)]
                if nxt not in adjacency[q]:
                    ok = False
                    break
            if ok:
                return cyc
        return None

    def synthesize(
        self,
        world: World,
        *,
        verification_enabled: bool = True,
    ) -> dict[str, Any]:
        auth = self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "state_count": 0,
                "warranted_transition_count": 0,
            }

        mapping = self._mapping(world)
        max_depth = max(len(p) for p in mapping)

        candidate = None
        for horizon in range(max_depth + 1):
            c = self._candidate(mapping, horizon)
            if c is not None:
                candidate = c
                break

        if candidate is None:
            return {
                "status": "CERTIFIED_CURRENT_RESIDUAL_CLASS_INADEQUATE",
                "state_count": 0,
                "warranted_transition_count": 0,
            }

        machine: PartialMachine = candidate["machine"]
        if candidate["whole_machine_stable"]:
            status = "VERIFIED_STABLE"
        elif candidate["spanning_warranted_cycle"]:
            status = "VERIFIED_CYCLE_CLOSED"
        else:
            status = "VERIFIED_LOCAL"

        return {
            "status": status,
            "state_count": candidate["state_count"],
            "supported_prefix_count": candidate["supported_prefix_count"],
            "warranted_transition_count": candidate["warranted_transition_count"],
            "unresolved_transition_count": candidate["unresolved_transition_count"],
            "locally_stable_state_count": candidate["locally_stable_state_count"],
            "locally_stable_state_ids": list(candidate["locally_stable_state_ids"]),
            "whole_machine_stable": candidate["whole_machine_stable"],
            "spanning_warranted_cycle": candidate["spanning_warranted_cycle"],
            "spanning_cycle_state_ids": (
                None if candidate["spanning_cycle_state_ids"] is None
                else list(candidate["spanning_cycle_state_ids"])
            ),
            "distinguishing_horizon": candidate["distinguishing_horizon"],
            "signature_set": [
                [int(x) for x in sig]
                for sig in candidate["signature_set"]
            ],
            "warranted_edges": [
                {
                    "source_signature": list(edge["source_signature"]),
                    "symbol": int(edge["symbol"]),
                    "target_signature": list(edge["target_signature"]),
                }
                for edge in candidate["warranted_edges"]
            ],
            "machine": machine.data(),
            "stable_executable": candidate["whole_machine_stable"],
            "_machine": machine,
        }

    @staticmethod
    def canonical_structure(machine: PartialMachine) -> tuple:
        n = len(machine.outputs)
        best = None
        for state_perm in permutations(range(n)):
            inv = {old:new for new,old in enumerate(state_perm)}
            for symbol_perm in ((0,1),(1,0)):
                raw_outputs = [int(machine.outputs[old]) for old in state_perm]
                label_map = {}
                canon_outputs = []
                for y in raw_outputs:
                    if y not in label_map:
                        label_map[y] = len(label_map)
                    canon_outputs.append(label_map[y])

                trans = []
                for old in state_perm:
                    row = []
                    for s in symbol_perm:
                        z = machine.transitions[old][s]
                        row.append(-1 if z is None else inv[int(z)])
                    trans.append(tuple(row))

                enc = (
                    inv[int(machine.initial)],
                    tuple(canon_outputs),
                    tuple(trans),
                )
                if best is None or enc < best:
                    best = enc
        assert best is not None
        return best
