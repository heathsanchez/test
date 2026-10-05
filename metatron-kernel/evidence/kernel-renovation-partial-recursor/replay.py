"""Replay the two compatibility requirements and their diagnostic controls."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("checker", type=pathlib.Path)
args = parser.parse_args()
root = pathlib.Path(__file__).resolve().parent
recorded = json.loads((root / "result.json").read_text())
results = []
for case in recorded["cases"]:
    path = root / (case["case"] + ".ndjson")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"]
    with path.open("rb") as stream:
        run = subprocess.run([str(args.checker.resolve())], stdin=stream,
                             capture_output=True, timeout=10, check=False)
    results.append(dict(case=case["case"], exit_code=run.returncode,
                        actual={0: "ACCEPT", 1: "REJECT", 2: "UNKNOWN"}.get(run.returncode, "ERROR"),
                        expected="ACCEPT", stderr=run.stderr.decode(errors="replace")))
controls = []
for case in ("eq", "prod"):
    for suffix in ("dependencies", "reflexivity-control"):
        with (root / f"{case}-{suffix}.ndjson").open("rb") as stream:
            run = subprocess.run([str(args.checker.resolve())], stdin=stream,
                                 capture_output=True, timeout=10, check=False)
        controls.append(dict(case=case, control=suffix, exit_code=run.returncode))
print(json.dumps(dict(cases=results, controls=controls), indent=2))
# The compatibility requirement is 2/2 ACCEPT; baseline UNKNOWN is a failed gate.
sys.exit(0 if all(r["exit_code"] == 0 for r in results + controls) else 1)
