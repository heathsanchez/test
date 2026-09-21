from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class TutorialCase:
    number: str
    relative_path: Path
    expected_exit_code: int
    sha256: str


@dataclass(frozen=True)
class CaseResult:
    number: str
    actual_exit_code: int


TUTORIAL_MANIFEST = (
    TutorialCase("001", Path("good/001_basicDef.ndjson"), 0, "82023f63efe0d75e9966621bfc69033ccd1333e8d0d989b3d54a79859e9da0ce"),
    TutorialCase("002", Path("bad/002_badDef.ndjson"), 1, "d1342aceb5741fc040523d3b4bd5e1ae3160dc17213d1dc0f6d766559a93a227"),
    TutorialCase("003", Path("good/003_arrowType.ndjson"), 0, "5c89ad23548a25281adaaaa705193f3d3846902f93e0a6740e3b95566706ae52"),
    TutorialCase("004", Path("good/004_dependentType.ndjson"), 0, "9c1601d4a39c4393a31cb6372c6d78dc245db79e385e359a80573b5bbfb09f83"),
    TutorialCase("005", Path("good/005_constType.ndjson"), 0, "b193eee0eb8419ffdf4287c220b346d6f7f90460d8e32bef631309551626d042"),
    TutorialCase("006", Path("good/006_betaReduction.ndjson"), 0, "3320f6f67cd55b2bae9112ea9b0d002f231e88ec4fb3c3f3c8fd4e750b13ce78"),
    TutorialCase("007", Path("good/007_betaReduction2.ndjson"), 0, "fb85e6eb84319dce9fed8acacb08cab2c5a54b67960112bc9de3eac22fc5a909"),
    TutorialCase("008", Path("good/008_forallSortWhnf.ndjson"), 0, "b4af42800421f4ac5ec7e699a706bdd82f9f1324a5d2d49769fb340bf36e6a48"),
    TutorialCase("009", Path("bad/009_forallSortBad.ndjson"), 1, "36eef2fa43e86af2d031a9cb9ec8fbd452dd7e50d3444997fe71003cc7295051"),
    TutorialCase("010", Path("bad/010_nonTypeType.ndjson"), 1, "18cba14f24723f0325721cdd1a5699e45b61bcce7ed94f2bded0f42c848ba4c4"),
    TutorialCase("011", Path("bad/011_nonTypeAxiom.ndjson"), 1, "687a8966b2727b26143b3340e8bead862b9057e5b4ec1ee7fc51a2a6e7211dc6"),
)


def load_declared_suite(
    tutorial_output: Path,
    *,
    manifest: Sequence[TutorialCase] = TUTORIAL_MANIFEST,
) -> tuple[TutorialCase, ...]:
    root = tutorial_output.resolve()
    for case in manifest:
        matches = sorted(root.glob(f"*/{case.number}_*.ndjson"))
        if len(matches) != 1:
            raise ValueError(
                f"tutorial case {case.number}: expected exactly one numbered input, "
                f"found {len(matches)}"
            )
        actual_relative = matches[0].relative_to(root)
        if actual_relative != case.relative_path:
            raise ValueError(
                f"tutorial case {case.number}: expected {case.relative_path.as_posix()}, "
                f"found {actual_relative.as_posix()}"
            )
        actual_sha256 = hashlib.sha256(matches[0].read_bytes()).hexdigest()
        if actual_sha256 != case.sha256:
            raise ValueError(
                f"tutorial case {case.number}: SHA-256 mismatch; "
                f"expected {case.sha256}, found {actual_sha256}"
            )
    return tuple(manifest)


def run_case(checker: Path, tutorial_output: Path, case: TutorialCase) -> CaseResult:
    with (tutorial_output / case.relative_path).open("rb") as stream:
        completed = subprocess.run(
            [str(checker)],
            stdin=stream,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    return CaseResult(case.number, completed.returncode)


def build_summary(
    *,
    candidate_sha: str,
    arena_sha: str,
    manifest: Sequence[TutorialCase],
    results: Sequence[CaseResult],
) -> dict:
    by_number: dict[str, CaseResult] = {}
    for result in results:
        if result.number in by_number:
            raise ValueError(f"duplicate result for tutorial case {result.number}")
        by_number[result.number] = result

    expected_numbers = {case.number for case in manifest}
    missing = sorted(expected_numbers - set(by_number))
    unexpected = sorted(set(by_number) - expected_numbers)
    if missing:
        raise ValueError(f"missing tutorial result: {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"unexpected tutorial result: {', '.join(unexpected)}")

    counts = {"incorrect": 0, "matched": 0}
    cases = []
    for case in manifest:
        actual_exit_code = by_number[case.number].actual_exit_code
        status = "matched" if actual_exit_code == case.expected_exit_code else "incorrect"
        counts[status] += 1
        cases.append(
            {
                "actual_exit_code": actual_exit_code,
                "expected_exit_code": case.expected_exit_code,
                "input": case.relative_path.as_posix(),
                "input_sha256": case.sha256,
                "number": case.number,
                "status": status,
            }
        )

    qualified = counts == {"incorrect": 0, "matched": len(manifest)}
    return {
        "arena_sha": arena_sha,
        "candidate_sha": candidate_sha,
        "cases": cases,
        "counts": counts,
        "expected_exit_codes": [case.expected_exit_code for case in manifest],
        "outcome": "passed" if qualified else "failed",
        "qualified": qualified,
        "schema": "metatron-kernel-arena-tutorial-qualification-v1",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checker", required=True, type=Path)
    parser.add_argument("--tutorial-output", required=True, type=Path)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--arena-sha", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checker = args.checker.resolve()
    tutorial_output = args.tutorial_output.resolve()
    suite = load_declared_suite(tutorial_output)
    results = tuple(run_case(checker, tutorial_output, case) for case in suite)
    summary = build_summary(
        candidate_sha=args.candidate_sha,
        arena_sha=args.arena_sha,
        manifest=suite,
        results=results,
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if summary["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
