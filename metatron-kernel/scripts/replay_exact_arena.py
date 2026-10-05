"""Replay every case with input digests and bounded subprocess execution."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("checker", type=pathlib.Path)
parser.add_argument("corpus", type=pathlib.Path)
parser.add_argument("output", type=pathlib.Path)
parser.add_argument("--candidate", required=True)
parser.add_argument("--arena", required=True)
parser.add_argument("--timeout", type=float, default=30)
args = parser.parse_args()
rows = []
started = time.monotonic()
for bucket, expected, expected_code in (("good", "accept", 0), ("bad", "reject", 1)):
    for path in sorted((args.corpus / bucket).rglob("*.ndjson")):
        case_start = time.monotonic()
        try:
            with path.open("rb") as stream:
                run = subprocess.run([str(args.checker.resolve())], stdin=stream,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                     timeout=args.timeout, check=False)
            code = run.returncode
            stderr = run.stderr.decode(errors="replace").strip()
        except subprocess.TimeoutExpired:
            code, stderr = 124, "TIMEOUT"
        actual = {0: "accept", 1: "reject", 2: "unknown"}.get(code, "error")
        status = ("matched" if code == expected_code else "incomplete" if code == 2
                  else "error" if actual == "error" else "incorrect")
        rows.append(dict(test=str(path.relative_to(args.corpus / bucket).with_suffix("")),
                         expected=expected, actual=actual, status=status, exit_code=code,
                         stderr=stderr, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         elapsed_seconds=time.monotonic() - case_start))
counts = {key: sum(r["status"] == key for r in rows)
          for key in ("matched", "incomplete", "incorrect", "error")}
verdicts = {key: sum(r["actual"] == key for r in rows)
            for key in ("accept", "reject", "unknown", "error")}
summary = dict(schema="nucleus-arena-full-replay-v1", candidate_sha=args.candidate,
               arena_sha=args.arena, case_count=len(rows), counts=counts,
               verdict_counts=verdicts, qualified=not (counts["incorrect"] or counts["error"]),
               elapsed_seconds=time.monotonic() - started, cases=rows)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "cases"}, indent=2))
for row in rows:
    if row["status"] != "matched":
        print(json.dumps(row, sort_keys=True))
