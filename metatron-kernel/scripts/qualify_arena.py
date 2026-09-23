from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


VERDICTS = {0: "accept", 1: "reject", 2: "unknown", 3: "error"}
COUNT_KEYS = ("matched", "incomplete", "incorrect", "error")
VERDICT_KEYS = ("accept", "reject", "unknown", "error")


@dataclass(frozen=True)
class CaseResult:
    name: str
    expected: str
    actual: str
    exit_code: int


@dataclass(frozen=True)
class SuiteCase:
    name: str
    expected: str
    path: Path


def classify_exit(exit_code: int) -> str:
    return VERDICTS.get(exit_code, "error")


def build_summary(
    *,
    candidate_sha: str,
    arena_sha: str,
    expected_cases: Mapping[str, str],
    results: Sequence[CaseResult],
) -> dict:
    by_name: dict[str, CaseResult] = {}
    for result in results:
        if result.name in by_name:
            raise ValueError(f"duplicate case: {result.name}")
        by_name[result.name] = result

    missing = sorted(set(expected_cases) - set(by_name))
    unexpected = sorted(set(by_name) - set(expected_cases))
    if missing:
        raise ValueError(f"missing case: {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"unexpected case: {', '.join(unexpected)}")

    counts = {key: 0 for key in COUNT_KEYS}
    verdict_counts = {key: 0 for key in VERDICT_KEYS}
    cases = []
    for name in sorted(expected_cases):
        result = by_name[name]
        if result.expected != expected_cases[name]:
            raise ValueError(f"case {name} carries the wrong expectation")
        status = case_status(result.expected, result.actual)
        counts[status] += 1
        verdict_counts[result.actual if result.actual in VERDICT_KEYS else "error"] += 1
        cases.append({**asdict(result), "status": status})

    qualified = counts == {
        "matched": len(expected_cases),
        "incomplete": 0,
        "incorrect": 0,
        "error": 0,
    }
    if counts["error"]:
        outcome = "error"
    elif counts["incorrect"]:
        outcome = "failed"
    elif counts["incomplete"]:
        outcome = "incomplete"
    else:
        outcome = "passed"

    return {
        "arena_sha": arena_sha,
        "candidate_sha": candidate_sha,
        "cases": cases,
        "counts": counts,
        "outcome": outcome,
        "qualified": qualified,
        "schema": "metatron-kernel-arena-qualification-v1",
        "verdict_counts": verdict_counts,
    }


def case_status(expected: str, actual: str) -> str:
    if actual == "error":
        return "error"
    if actual == expected:
        return "matched"
    if actual == "unknown":
        return "incomplete"
    return "incorrect"


def declared_suite(arena: Path, root: Path) -> list[SuiteCase]:
    return [
        SuiteCase(
            "arena/level-index-out-of-order",
            "accept",
            arena / "tests/other/level-index-out-of-order.ndjson",
        ),
        SuiteCase(
            "arena/sparse-name-index",
            "accept",
            arena / "tests/other/sparse-name-index.ndjson",
        ),
        SuiteCase(
            "local/bad-self-proof",
            "reject",
            root / "tests/fixtures/bad-self-proof.ndjson",
        ),
        SuiteCase(
            "local/bad-unbound-axiom",
            "reject",
            root / "tests/fixtures/bad-unbound-axiom.ndjson",
        ),
        SuiteCase(
            "local/good-beta-definition",
            "accept",
            root / "tests/fixtures/good-beta-definition.ndjson",
        ),
        SuiteCase(
            "local/unsupported-inductive",
            "unknown",
            root / "tests/fixtures/unsupported-inductive.ndjson",
        ),
    ]


def run_case(checker: Path, case: SuiteCase) -> CaseResult:
    with case.path.open("rb") as stream:
        completed = subprocess.run(
            [str(checker)],
            stdin=stream,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    return CaseResult(
        name=case.name,
        expected=case.expected,
        actual=classify_exit(completed.returncode),
        exit_code=completed.returncode,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checker", required=True, type=Path)
    parser.add_argument("--arena", required=True, type=Path)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--arena-sha", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    suite = declared_suite(args.arena.resolve(), root)
    expected = {case.name: case.expected for case in suite}
    results = [run_case(args.checker.resolve(), case) for case in suite]
    summary = build_summary(
        candidate_sha=args.candidate_sha,
        arena_sha=args.arena_sha,
        expected_cases=expected,
        results=results,
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 1 if summary["counts"]["incorrect"] or summary["counts"]["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
