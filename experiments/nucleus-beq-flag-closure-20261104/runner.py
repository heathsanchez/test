"""Source-exact closure screen for preexisting, non-default recursor demand modes.

No checker code is changed. A mode is usable only after a successful authentic
check, protected negative controls and a later full source-pinned qualification.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "let_wave", ROOT.parent / "nucleus-let-preservation-20261104/runner.py"
)
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)

SOURCE = Path("/tmp/beq-prefix.ndjson")
BINARY = Path("/tmp/beq-qualified/candidate/nucleus")
OUTPUT = Path("/tmp/nucleus-beq-flag-closure")
FLAGS = (
    "NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR",
    "NUCLEUS_EXPERIMENTAL_REPLAY_PROJECTION_MAJOR",
    "NUCLEUS_EXPERIMENTAL_REPLAY_NEUTRAL_PROJECTION",
)


def checksum(blob):
    return hashlib.sha256(blob).hexdigest()


def attempt(blob, env, label):
    begin = time.perf_counter()
    proc = subprocess.run(
        [str(BINARY)], input=blob, capture_output=True, env=env, timeout=90,
    )
    lines = proc.stderr.decode("utf-8", errors="replace").splitlines()
    last = next((line for line in reversed(lines)
                 if line.startswith("NUCLEUS_DOWNSTREAM:")), "")
    return {"label": label, "rc": proc.returncode,
            "wall_s": round(time.perf_counter() - begin, 3),
            "terminal": last[:1200], "stderr_sha256": checksum(proc.stderr)}


def main():
    OUTPUT.mkdir(exist_ok=True)
    source = SOURCE.read_bytes()
    assert checksum(source) == "d1c35f6a0de8644817b404e225a16de460e897e0b34c129fcb2a37483e630738"
    assert checksum(BINARY.read_bytes()) == "7897fdf50b447ec1bb38dd4a409d3a3bc690eeac7868d58848f6046b099684a6"
    rows = source.splitlines(keepends=True)
    terminal = json.loads(rows[-1]); assert "thm" in terminal
    forged = {}
    for field in ("type", "value"):
        edited = json.loads(rows[-1]); edited["thm"][field] = 0
        forged[field] = b"".join(rows[:-1]) + json.dumps(edited, separators=(",", ":")).encode() + b"\n"
    data = []
    for mask in range(8):
        env = L.R.N.runtime(True)
        for flag in FLAGS:
            env.pop(flag, None)
        selected = [key for bit, key in enumerate(FLAGS) if mask & (1 << bit)]
        for flag in selected:
            env[flag] = "1"
        env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
        rows = [attempt(source, env, "authentic")]
        # All configurations run both adversaries, regardless of positive
        # outcome, so the screen also detects unacceptable forged admissions.
        rows.extend(attempt(forged[field], env, "forged-" + field)
                    for field in ("type", "value"))
        result = {"mask": mask, "features": selected, "observations": rows,
                  "candidate_for_full_qualification":
                  bool(mask & 1) and rows[0]["rc"] == 0
                  and all(x["rc"] != 0 for x in rows[1:])}
        data.append(result)
        print("MODE_SCREEN", json.dumps(result, sort_keys=True), flush=True)
    # The independently qualified source baseline already uses all three
    # source replay flags. Other masks are ablations, not the baseline.
    baseline = data[7]
    assert baseline["observations"][0]["rc"] == 2
    assert "Nat.beq_refl" in baseline["observations"][0]["terminal"]
    report = {"status": "CANDIDATE_ABLATION_ONLY",
              "source_sha256": checksum(source),
              "binary_sha256": checksum(BINARY.read_bytes()),
              "n_modes": len(data), "rows": data,
              "qualified_modes": [x["mask"] for x in data
                                  if x["candidate_for_full_qualification"]]}
    (OUTPUT / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print("MODE_VERDICT", json.dumps({"qualified_modes":report["qualified_modes"],
                                    "status":report["status"]}), flush=True)


if __name__ == "__main__":
    main()
