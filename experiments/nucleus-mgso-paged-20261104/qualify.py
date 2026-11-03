#!/usr/bin/env python3
"""Fresh 208-case protected replay of v1/v2-capable MGSO shadow Nucleus.

Every ordinary, first-shadow, and restarted-shadow verdict must exactly match
the previously source-pinned independent Nucleus baseline. A stored receipt
never changes the running kernel's return value or proves its own validity.
"""

import collections
import hashlib
import json
import os
import pathlib
import subprocess
import time


OUT = pathlib.Path("/tmp/mgso-pages/evidence")
INPUT = pathlib.Path("/tmp/mgso-pages/inputs")
CACHE = pathlib.Path("/tmp/mgso-pages/cache")
BINARY = pathlib.Path("metatron-kernel/target/release/metatron-kernel")
FLAGS = (
    "RELEVANCE", "CONTEXT_BINDER", "TYPED_LINEAGE", "SUBSTITUTION_RECLOSURE",
    "TYPED_VALUE_NORMALIZATION", "PROJECTION_CONTEXT", "PROJECTION_CROSSFRAME_512",
    "TYPED_RECEIVER", "SOURCE_PAIR_DEPTH8", "POLYMORPHIC_PROP_IRREL",
    "PROP_SINGLETON_2P1F", "EXPECTED_LAMBDA", "FORMED_PROP_DOMAIN_RETRY",
    "TYPED_DATA_CONGRUENCE", "TYPED_PROJECTION_SPINE", "REPLAY_PROJECTION_MAJOR",
    "REPLAY_NEUTRAL_PROJECTION",
)


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def invoke(source, args, env):
    start = time.perf_counter()
    with source.open("rb") as stream:
        try:
            result = subprocess.run([str(BINARY), *args], stdin=stream,
                                    capture_output=True, timeout=240, env=env, check=False)
            rc, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            rc, stdout, stderr = 124, exc.stdout or b"", exc.stderr or b""
    return dict(rc=rc, wall_seconds=round(time.perf_counter() - start, 5),
                stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                stderr_sha256=hashlib.sha256(stderr).hexdigest(),
                candidate_match=b"status=candidate-match" in stderr,
                report_tail=stderr.decode(errors="replace")[-300:])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest_path = INPUT / "inputs-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    baseline_path = OUT / "baseline-verdicts.json"
    prior = json.loads(baseline_path.read_text())
    if len(manifest) != 208 or len(prior) != 208:
        raise ValueError("missing complete source-pinned protected corpus")
    baseline = {row["case"]: row for row in prior}
    if len(baseline) != 208:
        raise ValueError("baseline duplicate names")
    env = {key: val for key, val in os.environ.items() if not key.startswith("NUCLEUS_")}
    env.update({"NUCLEUS_EXPERIMENTAL_" + flag: "1" for flag in FLAGS})
    rows = []
    for index, case in enumerate(manifest):
        source = INPUT / "inputs" / case["relative_path"]
        if digest(source) != case["sha256"]:
            raise ValueError("source bytes changed for " + case["case"])
        old = baseline[case["case"]]
        if old["sha256"] != case["sha256"] or old["expected"] != case["expected"]:
            raise ValueError("historical corpus identity mismatch")
        path = CACHE / f"{index:03d}"
        arms = {
            "ordinary": invoke(source, [], env),
            "shadow_first": invoke(source, ["--mgso-shadow-dir", str(path)], env),
            "shadow_restart": invoke(source, ["--mgso-shadow-dir", str(path)], env),
        }
        expected_rc = old["rc"]
        if any(arm["rc"] != expected_rc for arm in arms.values()):
            raise AssertionError((case["case"], expected_rc, arms))
        if any(arm["stdout_sha256"] != arms["ordinary"]["stdout_sha256"]
               for arm in arms.values()):
            raise AssertionError((case["case"], "stdout changed"))
        root_exists = (path / "root.json").is_file()
        if root_exists != (expected_rc == 0):
            raise AssertionError((case["case"], expected_rc, "root persistence mismatch"))
        if expected_rc == 0 and not arms["shadow_restart"]["candidate_match"]:
            raise AssertionError((case["case"], "no cross-process matched receipt"))
        rows.append(dict(case=case["case"], sha256=case["sha256"],
                         expected=case["expected"], original_rc=expected_rc,
                         root_exists=root_exists, arms=arms))
        if index % 20 == 19:
            print("source-pinned 208 replay", index + 1, "/ 208", flush=True)
        (OUT / "verdicts.json").write_text(json.dumps(rows, indent=2, sort_keys=True))
    counts = dict(collections.Counter(row["original_rc"] for row in rows))
    roots = sum(row["root_exists"] for row in rows)
    matches = sum(row["arms"]["shadow_restart"]["candidate_match"] for row in rows)
    result = dict(count=len(rows), counts=counts, roots=roots,
                  shadow_restart_matches=matches, no_cached_verdict_authority=True,
                  configuration={key: val for key, val in env.items() if key.startswith("NUCLEUS_")},
                  manifest_sha256=digest(manifest_path),
                  baseline_sha256=digest(baseline_path),
                  binary_sha256=digest(BINARY),
                  workflow_commit=os.environ.get("GITHUB_SHA"),
                  wall_seconds={label: round(sum(r["arms"][label]["wall_seconds"]
                                            for r in rows), 4)
                                for label in ("ordinary", "shadow_first", "shadow_restart")})
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, sort_keys=True), flush=True)
    if counts != {0: 121, 1: 79, 2: 8} or roots != 121 or matches != 121:
        raise AssertionError("original Nucleus verdict or shadow parity changed")


if __name__ == "__main__":
    main()
