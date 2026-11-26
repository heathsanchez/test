"""Bounded C234 A/B experiment against unchanged, SHA-pinned Arena exports.

The experimental flag modifies only speculative capture-trial fuel scheduling.
No diagnostic conversion result is substituted for a checker judgment.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile


SOURCE_ARCHIVE_SHA256 = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED_CHAIN_SHA256 = "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
CAPTURE_FLAG = "NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"
PROBE_ONLY_FLAG = "NUCLEUS_C234_CAPTURE_PROBE_ONLY"
EXTRA_FEATURES = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)
CONTROLS = (
    "bad/bugs/eta-ctor-alias.ndjson",
    "bad/bugs/rec-rule-proof-irrel.ndjson",
    "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
    "bad/bugs/rec-type-proof-irrel.ndjson",
    "bad/bugs/rec-rule-wrong-arg.ndjson",
    "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
    "good/tutorial/126_quotMkType.ndjson",
)


def replay(checker: Path, source: bytes, environment: dict[str, str],
           output: Path, name: str, timeout: int = 180) -> dict:
    started = time.monotonic()
    run = subprocess.run((str(checker),), input=source, env=environment,
                         capture_output=True, timeout=timeout, check=False)
    log = run.stderr.decode(errors="replace")
    (output / f"{name}.stderr").write_text(log)
    ladder = [line for line in log.splitlines() if line.startswith("NUCLEUS_C230_LADDER:")]
    capture = [line for line in log.splitlines() if line.startswith("NUCLEUS_C234_RESERVE:")]
    owners = [line for line in log.splitlines() if line.startswith("NUCLEUS_C223_ARG_CONVERSION_UNKNOWN:")]
    return {
        "case": name, "verdict": run.returncode,
        "ladder": ladder[0] if ladder else None,
        "capture_reserve_events": len(capture),
        "source_owner_unknown_events": len(owners),
        "last_source_owner_unknown": owners[-1] if owners else None,
        "truncated": "NUCLEUS_C233_TRUNCATED" in log,
        "elapsed_s": round(time.monotonic() - started, 3),
    }


def main() -> None:
    arg = argparse.ArgumentParser()
    arg.add_argument("--archive", type=Path, required=True)
    arg.add_argument("--checker", type=Path, required=True)
    arg.add_argument("--out", type=Path, required=True)
    arg.add_argument("--flags", type=Path, required=True)
    args = arg.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == SOURCE_ARCHIVE_SHA256
    flags = json.loads(args.flags.read_text())["flags"]
    assert len(flags) == 24 and set(flags.values()) == {"1"}
    base_env = {key: value for key, value in os.environ.items() if not key.startswith("NUCLEUS_")}
    base_env.update(flags)
    base_env.update({f"NUCLEUS_EXPERIMENTAL_{feature}": "1" for feature in EXTRA_FEATURES})

    with zipfile.ZipFile(args.archive) as bundle:
        baseline = {row["case"]: row for row in json.loads(bundle.read("current212.json"))}
        assert len(baseline) == 212

        def pinned(case: str) -> bytes:
            source = bundle.read("inputs/" + case)
            assert hashlib.sha256(source).hexdigest() == baseline[case]["sha256"]
            return source

        case = "good/perf/fueled-chain.ndjson"
        assert baseline[case]["sha256"] == FUELED_CHAIN_SHA256
        source = pinned(case)
        probes = []
        for outer, expr, low, high in ((65536, 4771, 28, 35), (65600, 4777, 26, 33)):
            for allowance in (low, high):
                for experimental in (False, True):
                    env = base_env.copy()
                    env["NUCLEUS_C230_SINGLE_BUDGET"] = str(allowance)
                    env["NUCLEUS_C233_BRANCH_PATH"] = "1"
                    if experimental:
                        # Retain the exact original checking path; intervene
                        # only in its separate C230 diagnostic replay.
                        env[PROBE_ONLY_FLAG] = "1"
                    if outer > 65536:
                        env["NUCLEUS_C225_JUDGMENT_STEPS"] = str(outer)
                    row = replay(args.checker, source, env, args.out,
                                 f"fueled_outer{outer}_expr{expr}_allow{allowance}_reserve{int(experimental)}")
                    assert row["verdict"] in (0, 2), row
                    assert row["verdict"] == baseline[case]["actual"] == 2, row
                    assert row["ladder"] is not None, row
                    if not experimental:
                        assert row["capture_reserve_events"] == 0, row
                    elif allowance == high:
                        assert row["capture_reserve_events"] > 0, row
                    row.update(outer=outer, expr=expr, allowance=allowance,
                               experimental=experimental, source_sha256=FUELED_CHAIN_SHA256)
                    if row["ladder"] is not None:
                        assert f"expr=ExprId({expr})" in row["ladder"]
                        assert f"fresh_budget={allowance}" in row["ladder"]
                    print("C234_PROBE", json.dumps(row), flush=True)
                    probes.append(row)

        global_cases = []
        for outer in (65536, 65600):
            env = base_env.copy()
            env[CAPTURE_FLAG] = "1"
            env["NUCLEUS_C223_FIRST_OWNER"] = "1"
            env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
            if outer > 65536:
                env["NUCLEUS_C225_JUDGMENT_STEPS"] = str(outer)
            row = replay(args.checker, source, env, args.out,
                         f"fueled_global_reserve_outer{outer}")
            assert row["verdict"] in (0, 2), row
            row.update(outer=outer, experimental=True,
                       source_sha256=FUELED_CHAIN_SHA256)
            print("C234_GLOBAL", json.dumps(row), flush=True)
            global_cases.append(row)

        other_valid = []
        for case in ("good/perf/grind-ring-5.ndjson",
                     "good/perf/magma-list-deep-n36.ndjson",
                     "good/perf/magma-list-pair-n7.ndjson"):
            env = base_env.copy()
            env[CAPTURE_FLAG] = "1"
            row = replay(args.checker, pinned(case), env, args.out,
                         "other_" + case.replace("/", "_").removesuffix(".ndjson"))
            assert row["verdict"] in (0, 2), row
            row.update(source_case=case, expected=baseline[case]["expected"])
            print("C234_OTHER_VALID", json.dumps(row), flush=True)
            other_valid.append(row)

        protected = []
        for case in CONTROLS:
            for outer in (65536, 65600):
                for experimental in (False, True):
                    env = base_env.copy()
                    if experimental:
                        env[CAPTURE_FLAG] = "1"
                    if outer > 65536:
                        env["NUCLEUS_C225_JUDGMENT_STEPS"] = str(outer)
                    row = replay(args.checker, pinned(case), env, args.out,
                                 "control_" + case.replace("/", "_").removesuffix(".ndjson")
                                 + f"_outer{outer}_reserve{int(experimental)}", timeout=60)
                    assert row["verdict"] == baseline[case]["actual"] == baseline[case]["expected"], row
                    assert row["ladder"] is None and row["capture_reserve_events"] == 0, row
                    row.update(source_case=case, outer=outer, experimental=experimental)
                    protected.append(row)
        assert len(probes) == 8 and len(global_cases) == 2 and len(other_valid) == 3 and len(protected) == 28
        report = {"probes": probes, "global_cases": global_cases,
                  "other_valid": other_valid, "protected": protected,
                  "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
                  "original_source_unchanged": True,
                  "experimental_only": True}
        (args.out / "conclusion.json").write_text(json.dumps(report, indent=2))
        print("C234_SUMMARY", json.dumps({
            "probes": probes, "global_cases": global_cases, "other_valid": other_valid,
            "protected_counts": {"reject": sum(x["verdict"] == 1 for x in protected),
                                 "accept": sum(x["verdict"] == 0 for x in protected)},
        }), flush=True)


if __name__ == "__main__":
    main()
