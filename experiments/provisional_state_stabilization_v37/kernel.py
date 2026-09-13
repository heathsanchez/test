from __future__ import annotations
from collections import defaultdict
from itertools import combinations, permutations
from typing import Any

from basis import (
    Bits, PartialMachine, World, binary_words, is_prefix_free,
    parse_prefix_free, token_sequences,
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
                codebook = tuple(sorted(combo, key=lambda w: (w, len(w))))
                if is_prefix_free(codebook):
                    out.append(codebook)
        return tuple(out)

    @staticmethod
    def _parse_complete(
        world: World, codebook: tuple[Bits, ...]
    ) -> dict[tuple[int, ...], int] | None:
        mapping: dict[tuple[int, ...], int] = {}
        for row in world.rows:
            seq = parse_prefix_free(tuple(int(b) for b in row.raw), codebook)
            if seq is None:
                return None
            y = int(row.consequence)
            if seq in mapping and mapping[seq] != y:
                return None
            mapping[seq] = y

        max_depth = max(len(s) for s in mapping)
        required = set(token_sequences(len(codebook), max_depth))
        if set(mapping) != required:
            return None
        return mapping

    @staticmethod
    def _residual_model(
        mapping: dict[tuple[int, ...], int],
        alphabet_size: int,
        horizon: int,
    ) -> dict[str, Any] | None:
        max_depth = max(len(s) for s in mapping)
        frontier = max_depth - horizon
        if frontier < 0:
            return None

        suffixes = token_sequences(alphabet_size, horizon)
        prefixes = token_sequences(alphabet_size, frontier)

        def signature(prefix: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(int(mapping[prefix + suffix]) for suffix in suffixes)

        sig_by_prefix = {p: signature(p) for p in prefixes}
        signatures = tuple(sorted(set(sig_by_prefix.values()), key=repr))
        sid = {sig: i for i, sig in enumerate(signatures)}

        representatives: dict[tuple[int, ...], list[tuple[int, ...]]] = defaultdict(list)
        for p, sig in sig_by_prefix.items():
            representatives[sig].append(p)

        outputs = [int(sig[0]) for sig in signatures]
        transitions: list[tuple[int | None, ...]] = []
        provisional = []

        supported_limit = max_depth - horizon - 1
        for sig in signatures:
            reps = representatives[sig]
            supported = [p for p in reps if len(p) <= supported_limit]
            if not supported:
                transitions.append(tuple(None for _ in range(alphabet_size)))
                provisional.append(sid[sig])
                continue

            dest = []
            for symbol in range(alphabet_size):
                ds = {
                    sid[sig_by_prefix[p + (symbol,)]]
                    for p in supported
                }
                if len(ds) != 1:
                    return None
                dest.append(int(next(iter(ds))))
            transitions.append(tuple(dest))

        machine = PartialMachine(
            initial=int(sid[sig_by_prefix[()]]),
            outputs=tuple(outputs),
            transitions=tuple(transitions),
            signatures=signatures,
        )

        return {
            "machine": machine,
            "state_count": len(signatures),
            "provisional_state_ids": tuple(int(q) for q in provisional),
            "provisional_state_count": len(provisional),
            "stabilized_state_count": len(signatures) - len(provisional),
            "distinguishing_horizon": int(horizon),
            "max_authority_depth": int(max_depth),
            "signature_set": signatures,
        }

    @classmethod
    def _first_warranted_model(
        cls,
        mapping: dict[tuple[int, ...], int],
        alphabet_size: int,
    ) -> dict[str, Any] | None:
        max_depth = max(len(s) for s in mapping)
        for horizon in range(max_depth + 1):
            candidate = cls._residual_model(mapping, alphabet_size, horizon)
            if candidate is not None:
                return candidate
        return None

    def synthesize(
        self, world: World, *, verification_enabled: bool = True
    ) -> dict[str, Any]:
        auth = self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "state_count": 0,
                "provisional_state_count": 0,
            }

        admissible = []
        for codebook in self._all_codebooks():
            mapping = self._parse_complete(world, codebook)
            if mapping is None:
                continue
            model = self._first_warranted_model(mapping, len(codebook))
            if model is None:
                continue
            admissible.append((codebook, mapping, model))

        if not admissible:
            return {
                "status": "CERTIFIED_CURRENT_SUBSTRATE_INADEQUATE",
                "state_count": 0,
                "provisional_state_count": 0,
                "admissible_tokenizer_count": 0,
            }

        # The staged experiment concerns state warrant, not tokenizer ambiguity.
        # If raw authority admits more than one complete tokenization, do not
        # silently choose one by task-specific taste.
        if len(admissible) != 1:
            return {
                "status": "UNKNOWN_AMBIGUOUS_TOKENIZATION",
                "state_count": 0,
                "provisional_state_count": 0,
                "admissible_tokenizer_count": len(admissible),
            }

        codebook, mapping, model = admissible[0]
        machine: PartialMachine = model["machine"]
        provisional = model["provisional_state_count"]
        status = "VERIFIED_STABLE" if provisional == 0 else "VERIFIED_PROVISIONAL"

        return {
            "status": status,
            "state_count": model["state_count"],
            "provisional_state_count": provisional,
            "stabilized_state_count": model["stabilized_state_count"],
            "provisional_state_ids": list(model["provisional_state_ids"]),
            "distinguishing_horizon": model["distinguishing_horizon"],
            "max_authority_depth": model["max_authority_depth"],
            "codebook": [
                "".join(str(int(b)) for b in word)
                for word in codebook
            ],
            "token_count": len(codebook),
            "admissible_tokenizer_count": 1,
            "signature_set": [
                [int(x) for x in sig]
                for sig in model["signature_set"]
            ],
            "machine": machine.data(),
            "stable_executable": provisional == 0,
            "_machine": machine,
            "_codebook": codebook,
            "_mapping": mapping,
        }

    @staticmethod
    def canonical_structure(machine: PartialMachine) -> tuple:
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
