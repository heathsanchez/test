from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass


def v2(n: int) -> int:
    assert n > 0
    return (n & -n).bit_length() - 1


def shortcut(n: int) -> int:
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def iterate(n: int, steps: int) -> int:
    for _ in range(steps):
        n = shortcut(n)
    return n


def owner_lift(k: int, p: int) -> int:
    return 4**k * p + (4**k - 1) // 3


@dataclass(frozen=True)
class AffineMap:
    """P * target = A * source + C."""

    P: int
    A: int
    C: int

    def compose(self, after: "AffineMap") -> "AffineMap":
        return AffineMap(
            self.P * after.P,
            after.A * self.A,
            after.A * self.C + self.P * after.C,
        )

    def apply_exact(self, source: int) -> int:
        numerator = self.A * source + self.C
        assert numerator % self.P == 0
        return numerator // self.P

    def three_quarter_margin(self, source: int) -> int:
        return (3 * self.P - 4 * self.A) * source - 4 * self.C


@dataclass(frozen=True)
class Block:
    source: int
    owner: int
    source_steps: int
    owner_steps: int
    common: int
    word: tuple[int, ...]
    high_s: int
    strip_k: int
    affine: AffineMap


def renewal_block(source: int, guard: int = 100_000) -> Block:
    assert source > 0 and source % 2 == 1
    cur = source
    low_depth = 0
    intercept = 0
    word: list[int] = []

    for _ in range(guard):
        s = v2(3 * cur + 1)
        successor = (3 * cur + 1) >> s
        if s >= 3:
            k = (s - 1) // 2
            strip_intercept = (4**k - 1) // 3
            assert cur >= strip_intercept
            assert (cur - strip_intercept) % 4**k == 0
            owner = (cur - strip_intercept) // 4**k
            owner_steps = s - 2 * k
            assert owner > 0 and owner % 2 == 1
            assert owner_steps in (1, 2)
            assert owner_lift(k, owner) == cur
            assert v2(3 * owner + 1) == owner_steps

            affine = AffineMap(
                2 ** (low_depth + 2 * k),
                3 ** len(word),
                intercept - 2**low_depth * strip_intercept,
            )
            assert affine.apply_exact(source) == owner
            assert (affine.three_quarter_margin(source) >= 0) == (4 * owner <= 3 * source)
            assert iterate(source, low_depth + s) == successor
            assert iterate(owner, owner_steps) == successor
            return Block(
                source, owner, low_depth + s, owner_steps, successor,
                tuple(word), s, k, affine,
            )

        assert s in (1, 2)
        intercept = 3 * intercept + 2**low_depth
        low_depth += s
        word.append(s)
        cur = successor

    raise RuntimeError("low-valuation guard exhausted")


@dataclass(frozen=True)
class Closure:
    closed: bool
    owner: int
    source_steps: int
    owner_steps: int
    blocks: int
    peak: int
    total_affine: AffineMap
    path: tuple[Block, ...]


def close_three_quarter(source: int, cap: int) -> Closure:
    cur = source
    left_steps = right_steps = 0
    peak = source
    path: list[Block] = []
    total = AffineMap(1, 1, 0)

    for block_count in range(1, cap + 1):
        block = renewal_block(cur)
        path.append(block)
        peak = max(peak, block.owner, block.common)

        if block.source_steps >= right_steps:
            left_steps += block.source_steps - right_steps
            right_steps = block.owner_steps
        else:
            right_steps = block.owner_steps + right_steps - block.source_steps
        cur = block.owner
        assert iterate(source, left_steps) == iterate(cur, right_steps)

        total = total.compose(block.affine)
        assert total.apply_exact(source) == cur
        margin = total.three_quarter_margin(source)
        assert (margin >= 0) == (4 * cur <= 3 * source)
        if margin >= 0:
            return Closure(True, cur, left_steps, right_steps, block_count, peak, total, tuple(path))

    return Closure(False, cur, left_steps, right_steps, cap, peak, total, tuple(path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1 << 22)
    parser.add_argument("--cap", type=int, default=256)
    args = parser.parse_args()

    tested = unresolved = 0
    max_blocks = 0
    record: dict[str, int] | None = None
    exact_replay_failures = 0
    affine_margin_mismatches = 0
    extended_word_signatures: dict[tuple[tuple[int, ...], int], tuple[int, int, int]] = {}
    first_low_word_outcome: dict[tuple[int, ...], tuple[bool, Block]] = {}
    first_extended_outcome: dict[tuple[tuple[int, ...], int], tuple[bool, Block]] = {}
    low_word_collision: dict[str, object] | None = None
    extended_word_collision: dict[str, object] | None = None
    distinct_words: set[tuple[int, ...]] = set()
    distinct_affine_signatures: set[tuple[int, int, int]] = set()
    certificate = hashlib.sha256()

    for source in range(7, args.limit, 12):
        tested += 1
        closure = close_three_quarter(source, args.cap)
        unresolved += not closure.closed
        if closure.blocks > max_blocks:
            max_blocks = closure.blocks
            record = {
                "source": source,
                "owner": closure.owner,
                "source_steps": closure.source_steps,
                "owner_steps": closure.owner_steps,
                "peak": closure.peak,
            }

        for index, block in enumerate(closure.path):
            key = (block.word, block.high_s)
            signature = (block.affine.P, block.affine.A, block.affine.C)
            distinct_words.add(block.word)
            distinct_affine_signatures.add(signature)
            if key in extended_word_signatures:
                assert extended_word_signatures[key] == signature
            else:
                extended_word_signatures[key] = signature

            local_outcome = 4 * block.owner <= 3 * block.source
            margin = block.affine.three_quarter_margin(block.source)
            if (margin >= 0) != local_outcome:
                affine_margin_mismatches += 1
            if block.affine.apply_exact(block.source) != block.owner:
                exact_replay_failures += 1

            previous = first_low_word_outcome.get(block.word)
            if previous is None:
                first_low_word_outcome[block.word] = (local_outcome, block)
            elif previous[0] != local_outcome and low_word_collision is None:
                prior = previous[1]
                low_word_collision = {
                    "word": list(block.word),
                    "first": {
                        "source": prior.source, "owner": prior.owner, "high_s": prior.high_s,
                        "affine": {"P": prior.affine.P, "A": prior.affine.A, "C": prior.affine.C},
                        "margin": prior.affine.three_quarter_margin(prior.source),
                        "local_three_quarter": previous[0],
                    },
                    "second": {
                        "source": block.source, "owner": block.owner, "high_s": block.high_s,
                        "affine": {"P": block.affine.P, "A": block.affine.A, "C": block.affine.C},
                        "margin": margin, "local_three_quarter": local_outcome,
                    },
                }

            extended_previous = first_extended_outcome.get(key)
            if extended_previous is None:
                first_extended_outcome[key] = (local_outcome, block)
            elif extended_previous[0] != local_outcome and extended_word_collision is None:
                prior = extended_previous[1]
                extended_word_collision = {
                    "word": list(block.word), "high_s": block.high_s,
                    "affine": {"P": block.affine.P, "A": block.affine.A, "C": block.affine.C},
                    "first_source": prior.source, "second_source": block.source,
                }

            certificate.update(
                (
                    f"{source},{index},{block.source},{block.owner},{block.source_steps},"
                    f"{block.owner_steps},{block.common},{block.word},{block.high_s},"
                    f"{block.affine.P},{block.affine.A},{block.affine.C},"
                    f"{closure.total_affine.P},{closure.total_affine.A},{closure.total_affine.C}\n"
                ).encode()
            )

    result = {
        "schema": "COLLATZ_OWNER_RENEWAL_AFFINE_V0",
        "limit_exclusive": args.limit,
        "cap": args.cap,
        "tested": tested,
        "unresolved": unresolved,
        "max_blocks": max_blocks,
        "record": record,
        "distinct_words": len(distinct_words),
        "distinct_affine_signatures": len(distinct_affine_signatures),
        "exact_replay_failures": exact_replay_failures,
        "affine_margin_mismatches": affine_margin_mismatches,
        "low_word_collision": low_word_collision,
        "low_word_quotient_status": "REJECTED_BOUNDED" if low_word_collision else "NOT_REJECTED_BOUNDED",
        "extended_word_collision": extended_word_collision,
        "extended_word_quotient_status": "REJECTED_BOUNDED"
        if extended_word_collision else "NOT_REJECTED_BOUNDED",
        "affine_source_margin_status": "EXACT_ACCOUNTING_BOUNDED"
        if exact_replay_failures == 0 and affine_margin_mismatches == 0 else "FAILED",
        "certificate_sha256": certificate.hexdigest(),
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
