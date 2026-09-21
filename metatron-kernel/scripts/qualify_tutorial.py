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
    TutorialCase("012", Path("bad/012_nonPropThm.ndjson"), 1, "07c030b1e9ee321bb537f4f82f5238087cbed199f5e4f8673650c3190e54a33a"),
    TutorialCase("013", Path("good/013_thmProof.ndjson"), 0, "5e4664a6d4f05afbeff4e0af19681e88b2817c48787a9a281c4ba95d80483333"),
    TutorialCase("014", Path("bad/014_selfProof.ndjson"), 1, "f39b1bba5099649997a6c7cd49c870f91dfc86432979eafae58692d236142499"),
    TutorialCase("015", Path("good/015_levelComp1.ndjson"), 0, "2e6b6016ac241c9e1dd01ee86782f21adabd928bca24880b60619de453bec0c3"),
    TutorialCase("016", Path("good/016_levelComp2.ndjson"), 0, "aa971f4ba7603e183ebcf90a8ac92241f5fa2a96fbc6659e45380f52de3ffd6e"),
    TutorialCase("017", Path("good/017_levelComp3.ndjson"), 0, "e11ecbb09540778e2d2d0084d7759ce1c1483ca7f02168b87e1ec8bd1bf2c5cd"),
    TutorialCase("018", Path("good/018_levelParams.ndjson"), 0, "d78d458ea81bb210c80d3915976a03536f1b267879207f3604745b777014a167"),
    TutorialCase("019", Path("bad/019_tut06_bad01.ndjson"), 1, "9c5c0329065ef0b470c7b43a365c30a0098697dbeb8d69f2c2bea2e345ab9533"),
    TutorialCase("020", Path("good/020_levelComp4.ndjson"), 0, "39dced2925dcce7f66539f47f408d276b48d57638b4bfefc47860eed2f710a58"),
    TutorialCase("021", Path("good/021_levelComp5.ndjson"), 0, "31910166228cf46f68dbaa876d1c155734475b0f3f7a15c2a82f5535e8c150f8"),
    TutorialCase("022", Path("good/022_imax1.ndjson"), 0, "8fe3d41b913c8717847bc4a544e6b947bb5a1b616d80dbe19859d465ff225d57"),
    TutorialCase("023", Path("good/023_imax2.ndjson"), 0, "9d7fdab95e9ac1f87e19055e3133b98173f90d94c641870dc49cff6db2d1061f"),
    TutorialCase("024", Path("good/024_levelMaxComm.ndjson"), 0, "8a2ed8095cf9f69fcebb1e8b695944599cd524b42334cd6ff3051a5deebe7134"),
    TutorialCase("025", Path("good/025_levelMaxAssoc.ndjson"), 0, "2e97e820cfffa0f890ea70f7c3ea7f7e1636568196f3fc738868249644f9f229"),
    TutorialCase("026", Path("good/026_levelMaxIdem.ndjson"), 0, "1ee0d884c19ef76feb4ba77f5448507da2f8d983a688f4e8711d61784f50e571"),
    TutorialCase("027", Path("good/027_levelMaxAbsorb.ndjson"), 0, "87fab97e0b524a64e21ebe2adbadb407b381d1bee45cd2060e4a24055d554b11"),
    TutorialCase("028", Path("good/028_inferVar.ndjson"), 0, "2ed39c087f88481185d28085d7d2ba2f2985426da70062bfe4e6dd987af46110"),
    TutorialCase("029", Path("good/029_defEqLambda.ndjson"), 0, "7a28d11e2a035c2d0d97c75d5cb0bb12e16be1c5502b9975aa08775e1928ba92"),
    TutorialCase("030", Path("good/030_peano1.ndjson"), 0, "fe92f67341850f0c222c43cd99e9f17904cdb003654f394890f49df431ceaf7d"),
    TutorialCase("031", Path("good/031_peano2.ndjson"), 0, "63c8aec3c8457d2f4e76476b1d503647fb58d998b0dc2176cacc5efd814586e0"),
    TutorialCase("032", Path("good/032_peano3.ndjson"), 0, "e731f91828d3bb6186205233ba8ba94dd54bdf21e7b9a06e020f789be70ad55d"),
    TutorialCase("033", Path("good/033_letType.ndjson"), 0, "1222e60968ee37505bbb4952811a9645af2307f2a85e7f3d2d6fa2a7f1d5e667"),
    TutorialCase("034", Path("good/034_letTypeDep.ndjson"), 0, "eca16eea9573a481f232edfd0ff84a02ae208c1f379d967a56aec75f86fc7ca1"),
    TutorialCase("035", Path("good/035_letRed.ndjson"), 0, "b3d5e6f1f6e45721973e4e7167fbe0a92abbdcd69f039112eac70ab25c028acc"),
    TutorialCase("036", Path("good/036_empty.ndjson"), 0, "030852937308e66cb90de3b8de7cd336f3d825e81c87c5be5cc1fe33c6d54356"),
    TutorialCase("037", Path("good/037_boolType.ndjson"), 0, "02053d077abf5a63594d1025f9ef2f90dfff65f331503aa3b7486bbbb997b3e8"),
    TutorialCase("038", Path("good/038_twoBool.ndjson"), 0, "91a1f7379e22ebbec710ce6b43b7e0750be258ace8fc22d0b889fb76b57010de"),
    TutorialCase("039", Path("good/039_andType.ndjson"), 0, "d81009480e131d451da9e625fe9a90fff92fbee08d324aefd6fde3c3b89979e1"),
    TutorialCase("040", Path("good/040_prodType.ndjson"), 0, "a74e83890dce34014ef7dc8f1f6e7baf56d481df2a776d886462c789c529741d"),
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


def build_differential_summary(
    *,
    oracle_sha: str,
    candidate_sha: str,
    manifest: Sequence[TutorialCase],
    oracle_results: Sequence[CaseResult],
    candidate_results: Sequence[CaseResult],
    earned_case: str,
    earned_oracle_exit: int,
    earned_candidate_exit: int,
) -> dict:
    oracle = {result.number: result.actual_exit_code for result in oracle_results}
    candidate = {result.number: result.actual_exit_code for result in candidate_results}
    expected_numbers = {case.number for case in manifest}
    if set(oracle) != expected_numbers or set(candidate) != expected_numbers:
        raise ValueError("differential results must cover the declared manifest exactly")
    if earned_case not in expected_numbers:
        raise ValueError(f"earned case {earned_case} is not in the declared manifest")

    counts = {"equal": 0, "earned_delta": 0, "mismatch": 0}
    cases = []
    for case in manifest:
        oracle_exit = oracle[case.number]
        candidate_exit = candidate[case.number]
        if case.number == earned_case:
            status = (
                "earned_delta"
                if oracle_exit == earned_oracle_exit
                and candidate_exit == earned_candidate_exit
                else "mismatch"
            )
        else:
            status = "equal" if oracle_exit == candidate_exit else "mismatch"
        counts[status] += 1
        cases.append(
            {
                "candidate_exit_code": candidate_exit,
                "input": case.relative_path.as_posix(),
                "input_sha256": case.sha256,
                "number": case.number,
                "oracle_exit_code": oracle_exit,
                "status": status,
            }
        )

    qualified = counts["mismatch"] == 0 and counts["earned_delta"] == 1
    return {
        "candidate_sha": candidate_sha,
        "cases": cases,
        "counts": counts,
        "earned_case": earned_case,
        "oracle_sha": oracle_sha,
        "outcome": "passed" if qualified else "failed",
        "qualified": qualified,
        "schema": "metatron-kernel-tutorial-differential-v1",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checker", required=True, type=Path)
    parser.add_argument("--tutorial-output", required=True, type=Path)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--arena-sha", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--oracle-sha")
    parser.add_argument("--differential-output", type=Path)
    parser.add_argument("--earned-case")
    parser.add_argument("--earned-oracle-exit", type=int, default=2)
    parser.add_argument("--earned-candidate-exit", type=int, default=0)
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

    differential_qualified = True
    if args.oracle:
        if not args.oracle_sha or not args.earned_case or not args.differential_output:
            raise ValueError(
                "--oracle requires --oracle-sha, --earned-case, and --differential-output"
            )
        oracle = args.oracle.resolve()
        oracle_results = tuple(run_case(oracle, tutorial_output, case) for case in suite)
        differential = build_differential_summary(
            oracle_sha=args.oracle_sha,
            candidate_sha=args.candidate_sha,
            manifest=suite,
            oracle_results=oracle_results,
            candidate_results=results,
            earned_case=args.earned_case,
            earned_oracle_exit=args.earned_oracle_exit,
            earned_candidate_exit=args.earned_candidate_exit,
        )
        args.differential_output.write_text(
            json.dumps(differential, indent=2, sort_keys=True) + "\n"
        )
        differential_qualified = differential["qualified"]
    return 0 if summary["qualified"] and differential_qualified else 1


if __name__ == "__main__":
    raise SystemExit(main())
