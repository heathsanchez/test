from __future__ import annotations
from collections import defaultdict
from itertools import combinations, permutations
from typing import Any

from basis import (
    Bits, Machine, World, binary_words, is_prefix_free,
    parse_prefix_free, run_machine, token_sequences,
)

MAX_TOKEN_TYPES = 3
MAX_CODEWORD_LEN = 3

class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str, Any] | None:
        if not world.complete or not world.rows:
            return {"status": "UNKNOWN_AUTHORITY"}
        if any(r.consequence is None for r in world.rows):
            return {"status": "UNKNOWN_AUTHORITY"}
        raws = [tuple(int(b) for b in r.raw) for r in world.rows]
        if any(any(b not in (0, 1) for b in raw) for raw in raws):
            return {"status": "INVALID_RAW_ALPHABET"}
        if len(set(raws)) != len(raws):
            return {"status": "INVALID_DUPLICATE_RAW_ENCOUNTER"}
        if () not in set(raws):
            return {"status": "UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def _all_codebooks() -> tuple[tuple[Bits, ...], ...]:
        words = binary_words(1, MAX_CODEWORD_LEN)
        out = []
        for k in range(1, MAX_TOKEN_TYPES + 1):
            for combo in combinations(words, k):
                cb = tuple(sorted(combo, key=lambda w: (w, len(w))))
                if is_prefix_free(cb):
                    out.append(cb)
        return tuple(out)

    @staticmethod
    def _parse_world(world: World, codebook: tuple[Bits, ...]) -> dict[tuple[int, ...], int] | None:
        mapping: dict[tuple[int, ...], int] = {}
        for row in world.rows:
            parsed = parse_prefix_free(tuple(int(b) for b in row.raw), codebook)
            if parsed is None:
                return None
            y = int(row.consequence)
            if parsed in mapping and mapping[parsed] != y:
                return None
            mapping[parsed] = y
        max_tokens = max(len(s) for s in mapping)
        required = set(token_sequences(len(codebook), max_tokens))
        if set(mapping) != required:
            return None
        return mapping

    @staticmethod
    def _machine_candidate(
        mapping: dict[tuple[int, ...], int],
        alphabet_size: int,
        max_tokens: int,
        horizon: int,
    ) -> dict[str, Any] | None:
        depth = max_tokens - horizon
        if depth < 1:
            return None
        suffixes = token_sequences(alphabet_size, horizon)
        prefixes = token_sequences(alphabet_size, depth)

        def signature(prefix: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(int(mapping[prefix + suffix]) for suffix in suffixes)

        sig_by_prefix = {p: signature(p) for p in prefixes}
        signatures = sorted(set(sig_by_prefix.values()), key=repr)
        sid = {sig: i for i, sig in enumerate(signatures)}
        by_sig: dict[tuple[int, ...], list[tuple[int, ...]]] = defaultdict(list)
        for p, sig in sig_by_prefix.items():
            by_sig[sig].append(p)

        outputs = [0] * len(signatures)
        transitions: list[tuple[int, ...] | None] = [None] * len(signatures)
        for sig, ps in by_sig.items():
            q = sid[sig]
            outputs[q] = int(mapping[ps[0]])
            source = [p for p in ps if len(p) < depth]
            if not source:
                return None
            dest = []
            for symbol in range(alphabet_size):
                ds = {sid[sig_by_prefix[p + (symbol,)]] for p in source}
                if len(ds) != 1:
                    return None
                dest.append(int(next(iter(ds))))
            transitions[q] = tuple(dest)

        if any(t is None for t in transitions):
            return None

        machine = Machine(
            initial=int(sid[sig_by_prefix[()]]),
            outputs=tuple(int(x) for x in outputs),
            transitions=tuple(t for t in transitions if t is not None),
        )
        if any(run_machine(machine, seq) != int(y) for seq, y in mapping.items()):
            return None

        return {
            "machine": machine,
            "state_count": len(machine.outputs),
            "distinguishing_horizon": int(horizon),
            "construction_depth": int(depth),
        }

    @classmethod
    def _best_machine(
        cls,
        mapping: dict[tuple[int, ...], int],
        alphabet_size: int,
    ) -> dict[str, Any] | None:
        max_tokens = max(len(s) for s in mapping)
        candidates = []
        for horizon in range(max_tokens + 1):
            c = cls._machine_candidate(mapping, alphabet_size, max_tokens, horizon)
            if c is not None:
                candidates.append(c)
        if not candidates:
            return None
        candidates.sort(key=lambda c: (
            c["state_count"],
            c["distinguishing_horizon"],
            c["construction_depth"],
        ))
        return candidates[0]

    def synthesize(self, world: World, *, verification_enabled: bool = True) -> dict[str, Any]:
        auth = self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status": "UNKNOWN_NO_VERIFIER", "state_count": 0}

        verified = []
        fixed_width_verified = 0
        for codebook in self._all_codebooks():
            mapping = self._parse_world(world, codebook)
            if mapping is None:
                continue
            best = self._best_machine(mapping, len(codebook))
            if best is None:
                continue
            if len({len(w) for w in codebook}) == 1:
                fixed_width_verified += 1
            total_codeword_length = sum(len(w) for w in codebook)
            verified.append({
                **best,
                "codebook": codebook,
                "token_count": len(codebook),
                "total_codeword_length": total_codeword_length,
                "max_codeword_length": max(len(w) for w in codebook),
                "mapping": mapping,
            })

        if not verified:
            return {
                "status": "CERTIFIED_CURRENT_TOKENIZER_CLASS_INADEQUATE",
                "state_count": 0,
                "verified_tokenizer_count": 0,
                "fixed_width_verified_count": 0,
            }

        verified.sort(key=lambda c: (
            c["state_count"],
            c["total_codeword_length"],
            c["max_codeword_length"],
            c["token_count"],
            tuple(c["codebook"]),
        ))
        best = verified[0]
        machine: Machine = best["machine"]
        mapping = best["mapping"]

        return {
            "status": "VERIFIED",
            "state_count": best["state_count"],
            "distinguishing_horizon": best["distinguishing_horizon"],
            "construction_depth": best["construction_depth"],
            "codebook": ["".join(str(int(b)) for b in w) for w in best["codebook"]],
            "token_count": best["token_count"],
            "total_codeword_length": best["total_codeword_length"],
            "max_codeword_length": best["max_codeword_length"],
            "verified_tokenizer_count": len(verified),
            "fixed_width_verified_count": fixed_width_verified,
            "machine": machine.data(),
            "exact_training_replay": all(
                run_machine(machine, seq) == int(y) for seq, y in mapping.items()
            ),
            "_machine": machine,
            "_codebook": best["codebook"],
        }

    @staticmethod
    def canonical_structure(machine: Machine) -> tuple:
        n = len(machine.outputs)
        k = len(machine.transitions[0]) if machine.transitions else 0
        best = None
        for state_perm in permutations(range(n)):
            inv = {old: new for new, old in enumerate(state_perm)}
            for symbol_perm in permutations(range(k)):
                raw_outputs = [int(machine.outputs[old]) for old in state_perm]
                label_map = {}
                canon_outputs = []
                for y in raw_outputs:
                    if y not in label_map:
                        label_map[y] = len(label_map)
                    canon_outputs.append(label_map[y])
                trans = []
                for old in state_perm:
                    t = machine.transitions[old]
                    trans.append(tuple(inv[int(t[s])] for s in symbol_perm))
                enc = (inv[int(machine.initial)], tuple(canon_outputs), tuple(trans))
                if best is None or enc < best:
                    best = enc
        assert best is not None
        return best
