"""Native, fail-closed observer qualification against the selected Nucleus artifact.

The candidate is diagnostic-only: any changed standard verdict is a failure.
The protected 403-case receipt belongs to selected source SHA 0181352 and is
replayed on the *same* 24 captured flags. No source name or metadata grants
typing authority here.
"""

import collections
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
BASELINE = Path("base/candidate/metatron-kernel").resolve()
CANDIDATE = Path("candidate/metatron-kernel").resolve()
FLAGS = json.loads(Path("base/flags.json").read_text())
ENV = {key: value for key, value in os.environ.items() if not key.startswith("NUCLEUS_")}
ENV.update(FLAGS)
SIX = {
    "fueled-chain": "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a",
    "grind-ring-5": "e9c394e0ff311fd10f60dee2433a530f16e82354c32d6588a8775baa06fd221f",
    "magma-list-pair-n7": "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35",
    "magma-list-pair-n21": "b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84",
    "magma-list-deep-n21": "b7a211699ab32a5d2397319702e2d5552f5796a6bdac990efa69fb186039f526",
    "magma-list-deep-n36": "6669cee92ad330dada351ac9e63656f7e9e848dd70376f17030d64677f8c81ac",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run_case(label, binary, source, *, probe=False, expected=None):
    data = source.read_bytes()
    start = time.monotonic()
    env = ENV.copy()
    if probe:
        env["NUCLEUS_LOGOS_SCOPE_PROBE"] = "1"
    try:
        result = subprocess.run([str(binary)], input=data, capture_output=True, env=env, timeout=240)
        rc = result.returncode
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stderr = exc.stderr or b""
    (REPORTS / (label + ".stderr")).write_bytes(stderr)
    observation = [json.loads(line.partition(":")[2]) for line in stderr.decode(errors="replace").splitlines()
                   if line.startswith("NUCLEUS_LOGOS_PROJECTION_SHADOW:")]
    row = {"case": label, "rc": rc, "sha256": digest(data), "seconds": round(time.monotonic() - start, 3),
           "binary_sha256": digest(binary.read_bytes()), "observer": observation}
    if expected is not None:
        assert rc == expected, (label, rc, expected, row)
    return row


def main():
    original = sorted(Path("original196").rglob("*.ndjson"))
    arena = sorted(Path("arena207").rglob("*.ndjson"))
    assert len(original) == 196 and len(arena) == 207, (len(original), len(arena))

    # Source-native, unchanged prefix; byte hash guards against choosing a
    # different theorem or silently modifying the input.
    raw = Path("original196/good/perf/fueled-chain.ndjson").read_bytes().splitlines(keepends=True)
    chain9 = Path("reports/chain9-original.ndjson")
    chain9.write_bytes(b"".join(raw[:11792]))
    assert digest(chain9.read_bytes()) == "78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3"

    comparisons = []
    for label, binary, probe in [("chain9-pristine", BASELINE, False),
                                 ("chain9-observer-off", CANDIDATE, False),
                                 ("chain9-observer-on", CANDIDATE, True)]:
        row = run_case(label, binary, chain9, probe=probe, expected=2)
        comparisons.append(row)
        print(json.dumps(row), flush=True)
    assert comparisons[0]["sha256"] == comparisons[1]["sha256"] == comparisons[2]["sha256"]

    # A former observer build increased infer_in's recursive stack frame and
    # aborted on this exact original despite the observer being disabled.
    # Guard this independently of broad concurrency and inspect its stderr.
    app_lam = Path("original196/good/perf/app-lam.ndjson")
    assert digest(app_lam.read_bytes()) == "552d6e8398f579fcf59ab9abd8187fc7a8a037697da66c129aacb4cc1b9dd414"
    stack_controls = [run_case(label, binary, app_lam, probe=probe, expected=0)
                      for label, binary, probe in [("app-lam-pristine", BASELINE, False),
                                                    ("app-lam-observer-off", CANDIDATE, False),
                                                    ("app-lam-observer-on", CANDIDATE, True)]]

    # An independent protected receipt from the exact selected-source
    # artifact supplies the expected outcome for each unchanged original.
    baseline = json.loads(Path("base/reports/ordinary-403.json").read_text())
    assert len(baseline) == 403
    assert collections.Counter(row["new"] for row in baseline) == {0: 240, 1: 150, 2: 13}
    protected = []

    def replay(row):
        name = row["case"]
        assert name.startswith(("original196/", "arena207/"))
        case = Path(name)
        assert case.suffix == ".ndjson" and case.is_file()
        assert digest(case.read_bytes()) == row["input_sha256"]
        start = time.monotonic()
        try:
            result = subprocess.run([str(CANDIDATE)], input=case.read_bytes(), env=ENV,
                                    capture_output=True, timeout=240)
            rc = result.returncode
        except subprocess.TimeoutExpired:
            rc = 124
        return {"case": name, "rc": rc, "baseline": row["new"],
                "sha256": row["input_sha256"], "seconds": round(time.monotonic() - start, 3)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(replay, baseline):
            protected.append(row)
            if row["rc"] != row["baseline"]:
                print("REGRESSION", json.dumps(row), flush=True)
    (REPORTS / "protected-403.json").write_text(json.dumps(protected, indent=2))
    assert all(row["rc"] == row["baseline"] for row in protected), "Selected 403 outcomes changed"

    six = {}
    for name, expected_hash in SIX.items():
        path = Path("arena207/good/perf") / (name + ".ndjson")
        assert digest(path.read_bytes()) == expected_hash, name
        row = next(row for row in protected if row["case"] == str(path))
        assert row["rc"] == 2, (name, row)
        six[name] = row

    # The observer is a diagnostic, not a truth source; no speculative
    # cache entries are installed. Its result may be a useful negative.
    observations = comparisons[-1]["observer"]
    summary = {
        "status": "OBSERVATION_ONLY", "acceptance_authority": False,
        "selected_artifact": 13520537513, "selected_commit": "018135224632f72ba06a2818132c3e857d67eaad",
        "flags": FLAGS, "standard_budget": 262144,
        "baseline_binary_sha256": digest(BASELINE.read_bytes()),
        "candidate_binary_sha256": digest(CANDIDATE.read_bytes()),
        "chain9": comparisons, "app_lam_stack_controls": stack_controls,
        "observations": observations,
        "protected_count": len(protected),
        "protected_verdict_counts": dict(collections.Counter(row["rc"] for row in protected)),
        "six_original_unchanged": six,
    }
    (REPORTS / "logos-projection-summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"protected": len(protected), "six_unknown": len(six), "observations": observations}), flush=True)


if __name__ == "__main__":
    main()
