#!/usr/bin/env python3
"""Discover the coarsest residual quotient induced by qualified Nucleus probes.

The script never changes checker semantics. It replays one frozen corpus through
a current checker plus a panel of exact historical/alternative qualified
checkers. Residual cases under the current checker are partitioned only by
future protected consequences: the return-code vector produced by the probe
panel.

A deterministic separator-driven refinement then reconstructs the same quotient
without enumerating set partitions. Each chosen probe is the one that separates
the largest number of still-indistinguishable residual pairs.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

DECISIVE = {0, 1}
RESIDUAL = {2, 3}


@dataclass(frozen=True)
class Case:
    name: str
    path: pathlib.Path
    expected: int


def corpus(root: pathlib.Path) -> list[Case]:
    rows: list[Case] = []
    for dirname, expected in (("good", 0), ("bad", 1)):
        base = root / dirname
        for path in sorted(base.rglob("*.ndjson")):
            rows.append(
                Case(
                    name=str(path.relative_to(base)).removesuffix(".ndjson"),
                    path=path,
                    expected=expected,
                )
            )
    return rows


def run(binary: pathlib.Path, case: Case, timeout: int) -> int:
    with case.path.open("rb") as handle:
        return subprocess.run(
            [str(binary)],
            stdin=handle,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        ).returncode


def parse_probe(spec: str) -> tuple[str, pathlib.Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("probe must be LABEL=/path/to/binary")
    label, raw_path = spec.split("=", 1)
    if not label:
        raise argparse.ArgumentTypeError("probe label must be non-empty")
    return label, pathlib.Path(raw_path)


def separated_pairs(blocks: Iterable[list[str]], outcomes: dict[str, dict[str, int]], probe: str) -> int:
    score = 0
    for block in blocks:
        counts: dict[int, int] = defaultdict(int)
        for name in block:
            counts[outcomes[name][probe]] += 1
        vals = list(counts.values())
        total = sum(vals)
        score += (total * total - sum(v * v for v in vals)) // 2
    return score


def refine(
    names: list[str],
    probe_order: list[str],
    outcomes: dict[str, dict[str, int]],
) -> tuple[list[list[str]], list[dict[str, object]]]:
    blocks = [sorted(names)]
    remaining = list(probe_order)
    sequence: list[dict[str, object]] = []

    while remaining:
        scored = [
            (separated_pairs(blocks, outcomes, probe), -probe_order.index(probe), probe)
            for probe in remaining
        ]
        score, _, chosen = max(scored)
        if score <= 0:
            break

        new_blocks: list[list[str]] = []
        for block in blocks:
            buckets: dict[int, list[str]] = defaultdict(list)
            for name in block:
                buckets[outcomes[name][chosen]].append(name)
            for status in sorted(buckets):
                new_blocks.append(sorted(buckets[status]))
        blocks = sorted(new_blocks, key=lambda b: (b[0], len(b), tuple(b)))
        remaining.remove(chosen)
        sequence.append(
            {
                "probe": chosen,
                "new_pair_separations": score,
                "class_count": len(blocks),
            }
        )
    return blocks, sequence


def signature_partition(
    names: list[str],
    probe_order: list[str],
    outcomes: dict[str, dict[str, int]],
) -> list[list[str]]:
    groups: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for name in names:
        groups[tuple(outcomes[name][probe] for probe in probe_order)].append(name)
    return sorted((sorted(v) for v in groups.values()), key=lambda b: (b[0], len(b), tuple(b)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=pathlib.Path, required=True)
    parser.add_argument("--current", type=pathlib.Path, required=True)
    parser.add_argument("--current-label", default="current")
    parser.add_argument("--probe", action="append", default=[], type=parse_probe)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--expect-count", type=int, default=193)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    cases = corpus(args.corpus)
    if len(cases) != args.expect_count:
        raise SystemExit(f"expected {args.expect_count} cases, found {len(cases)}")

    probes = [(args.current_label, args.current), *args.probe]
    labels = [label for label, _ in probes]
    if len(labels) != len(set(labels)):
        raise SystemExit("duplicate probe label")

    for label, binary in probes:
        if not binary.is_file():
            raise SystemExit(f"missing binary for {label}: {binary}")

    all_rows: list[dict[str, object]] = []
    by_name: dict[str, dict[str, int]] = {}
    wrong: list[dict[str, object]] = []

    for case in cases:
        result: dict[str, int] = {}
        for label, binary in probes:
            rc = run(binary, case, args.timeout)
            result[label] = rc
            if rc in DECISIVE and rc != case.expected:
                wrong.append(
                    {
                        "test": case.name,
                        "expected": case.expected,
                        "probe": label,
                        "status": rc,
                    }
                )
        by_name[case.name] = result
        all_rows.append(
            {
                "test": case.name,
                "expected": case.expected,
                "outcomes": result,
            }
        )

    if wrong:
        raise SystemExit("a supposedly qualified probe made a wrong protected decision: " + json.dumps(wrong[:20]))

    current_residual = sorted(
        case.name
        for case in cases
        if by_name[case.name][args.current_label] in RESIDUAL
    )

    probe_order = [label for label, _ in args.probe]
    refined, separator_sequence = refine(current_residual, probe_order, by_name)
    direct = signature_partition(current_residual, probe_order, by_name)
    if refined != direct:
        raise SystemExit(
            "separator refinement did not reconstruct full signature quotient: "
            + json.dumps({"refined": refined, "direct": direct}, sort_keys=True)
        )

    classes = []
    for index, members in enumerate(refined):
        first = members[0]
        signature = {probe: by_name[first][probe] for probe in probe_order}
        classes.append(
            {
                "class_id": f"Q{index:02d}",
                "members": members,
                "size": len(members),
                "signature": signature,
                "decisive_probes": [
                    probe for probe in probe_order if signature[probe] in DECISIVE
                ],
            }
        )

    probe_stats = []
    for probe in probe_order:
        resolved = [
            name for name in current_residual if by_name[name][probe] in DECISIVE
        ]
        probe_stats.append(
            {
                "probe": probe,
                "resolves_current_residual": len(resolved),
                "resolved_tests": resolved,
                "global_pair_separations": separated_pairs([current_residual], by_name, probe),
            }
        )
    probe_stats.sort(
        key=lambda row: (
            -int(row["resolves_current_residual"]),
            -int(row["global_pair_separations"]),
            str(row["probe"]),
        )
    )

    out = {
        "schema": "nucleus-future-quotient-arena-v1",
        "current_label": args.current_label,
        "probe_order": probe_order,
        "total_cases": len(cases),
        "current_residual_count": len(current_residual),
        "quotient_class_count": len(classes),
        "collapse_ratio": (
            len(current_residual) / len(classes) if classes else None
        ),
        "separator_sequence": separator_sequence,
        "classes": classes,
        "probe_stats": probe_stats,
        "best_next_probe": probe_stats[0]["probe"] if probe_stats else None,
        "wrong_decisions": wrong,
        "rows": all_rows,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "current_residual_count": out["current_residual_count"],
                "quotient_class_count": out["quotient_class_count"],
                "collapse_ratio": out["collapse_ratio"],
                "separator_sequence": out["separator_sequence"],
                "best_next_probe": out["best_next_probe"],
                "probe_stats": out["probe_stats"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
