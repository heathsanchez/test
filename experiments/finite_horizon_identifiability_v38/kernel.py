from __future__ import annotations
from itertools import product
from typing import Any

from basis import World

class Kernel:
    @staticmethod
    def sequences(alphabet_size: int, max_depth: int) -> tuple[tuple[int, ...], ...]:
        out = []
        for n in range(max_depth + 1):
            out.extend(
                tuple(int(x) for x in xs)
                for xs in product(range(alphabet_size), repeat=n)
            )
        return tuple(out)

    @classmethod
    def authority(cls, world: World) -> dict[str, Any] | None:
        if not world.complete or not world.rows:
            return {"status": "UNKNOWN_AUTHORITY"}
        if world.alphabet_size < 1 or world.max_depth < 0:
            return {"status": "INVALID_DECLARED_DOMAIN"}
        if any(r.consequence is None for r in world.rows):
            return {"status": "UNKNOWN_AUTHORITY"}

        observed = [tuple(int(x) for x in r.sequence) for r in world.rows]
        if any(
            any(x < 0 or x >= world.alphabet_size for x in seq)
            or len(seq) > world.max_depth
            for seq in observed
        ):
            return {"status": "INVALID_SEQUENCE"}

        if len(set(observed)) != len(observed):
            return {"status": "INVALID_DUPLICATE_SEQUENCE"}

        required = set(cls.sequences(world.alphabet_size, world.max_depth))
        if set(observed) != required:
            return {"status": "UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def table(world: World) -> dict[tuple[int, ...], int]:
        return {
            tuple(int(x) for x in r.sequence): int(r.consequence)
            for r in world.rows
        }

    @classmethod
    def compare(
        cls,
        left: World,
        right: World,
        *,
        verification_enabled: bool = True,
        global_completeness_certificate: bool = False,
    ) -> dict[str, Any]:
        if not verification_enabled:
            return {"status": "UNKNOWN_NO_VERIFIER"}

        la = cls.authority(left)
        ra = cls.authority(right)
        if la or ra:
            return {"status": "UNKNOWN_AUTHORITY"}

        if (
            left.alphabet_size != right.alphabet_size
            or left.max_depth != right.max_depth
        ):
            return {"status": "INCOMPARABLE_DECLARED_DOMAINS"}

        lt = cls.table(left)
        rt = cls.table(right)
        for seq in cls.sequences(left.alphabet_size, left.max_depth):
            if lt[seq] != rt[seq]:
                return {
                    "status": "VERIFIED_NOT_EQUIVALENT",
                    "witness": list(seq),
                    "left": int(lt[seq]),
                    "right": int(rt[seq]),
                    "witness_depth": len(seq),
                }

        if global_completeness_certificate:
            return {
                "status": "VERIFIED_EQUIVALENT_UNDER_EXTERNAL_COMPLETENESS_CERTIFICATE",
                "verified_depth": int(left.max_depth),
            }

        return {
            "status": "UNKNOWN_BEYOND_FINITE_HORIZON",
            "verified_bounded_equivalence_depth": int(left.max_depth),
        }

    @classmethod
    def bounded_compare(
        cls,
        left: World,
        right: World,
        bound: int,
        *,
        verification_enabled: bool = True,
    ) -> dict[str, Any]:
        if not verification_enabled:
            return {"status": "UNKNOWN_NO_VERIFIER"}

        la = cls.authority(left)
        ra = cls.authority(right)
        if la or ra:
            return {"status": "UNKNOWN_AUTHORITY"}

        if left.alphabet_size != right.alphabet_size:
            return {"status": "INCOMPARABLE_DECLARED_DOMAINS"}
        if bound < 0 or left.max_depth < bound or right.max_depth < bound:
            return {"status": "UNKNOWN_AUTHORITY"}

        lt = cls.table(left)
        rt = cls.table(right)
        for seq in cls.sequences(left.alphabet_size, bound):
            if lt[seq] != rt[seq]:
                return {
                    "status": "VERIFIED_NOT_EQUIVALENT_WITHIN_BOUND",
                    "bound": int(bound),
                    "witness": list(seq),
                    "left": int(lt[seq]),
                    "right": int(rt[seq]),
                    "witness_depth": len(seq),
                }

        return {
            "status": "VERIFIED_BOUNDED_EQUIVALENCE",
            "bound": int(bound),
        }

    @classmethod
    def observation_signature(cls, world: World) -> tuple[tuple[tuple[int, ...], int], ...] | None:
        if cls.authority(world):
            return None
        table = cls.table(world)
        return tuple(
            (seq, int(table[seq]))
            for seq in cls.sequences(world.alphabet_size, world.max_depth)
        )
