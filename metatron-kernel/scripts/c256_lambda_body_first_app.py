"""C256: source-pinned, read-only first lambda-body application failure observer.

The checker semantics are identical to C255. This script does not promote
a diagnostic result into a typing/reduction warrant.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import time
import zipfile

import c255_lambda_premise_replay as c255

def main():
    parser = argparse.ArgumentParser()
    for field in ("archive", "checker", "flags", "out"):
        parser.add_argument("--" + field, required=True, type=pathlib.Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if c255.sha(args.archive.read_bytes()) != c255.ARCHIVE:
        raise ValueError("Original current212 archive changed")
    historical = json.loads(args.flags.read_text())["flags"]
    if len(historical) != 24 or set(historical.values()) != {"1"}:
        raise ValueError("Historical baseline flags changed")
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(historical)
    env.update({f"NUCLEUS_EXPERIMENTAL_{key}": "1" for key in c255.EXTRAS})
    env.update({
        "NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE": "1",
        "NUCLEUS_C247_TYPED_PI_LOCAL_RETRY": "1",
        "NUCLEUS_C250_ZERO_DOMAIN_RETRY": "1",
        "NUCLEUS_C251_LITERAL_PI_VIEW": "1",
        "NUCLEUS_C252_ARGUMENT_PROOF_RETRY": "1",
        "NUCLEUS_C253_WIDEN_SCOPE": "1",
        "NUCLEUS_C254_ARG_ALLOWANCE_512": "1",
        "NUCLEUS_C255_LAMBDA_PREMISES": "1",
        "NUCLEUS_C256_BODY_FIRST_APP": "1",
        "NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE": "1",
        "NUCLEUS_TRACE_DOWNSTREAM": "1",
        "NUCLEUS_C225_JUDGMENT_STEPS": "69632",
    })
    with zipfile.ZipFile(args.archive) as z:
        roster = {r["case"]: r for r in json.loads(z.read("current212.json"))}
        if len(roster) != 212:
            raise ValueError("Source roster changed")
        source = z.read("inputs/good/perf/fueled-chain.ndjson")
        if c255.sha(source) != c255.FUELED:
            raise ValueError("Fueled source changed")
        if c255.sha(source) != roster["good/perf/fueled-chain.ndjson"]["sha256"]:
            raise ValueError("Fueled manifest mismatch")
    start = time.monotonic()
    completed = subprocess.run([str(args.checker)], input=source, env=env,
                               capture_output=True, timeout=180, check=False)
    stderr = completed.stderr.decode(errors="replace")
    (args.out / "c256-fueled.stderr").write_text(stderr)
    body = [line for line in stderr.splitlines() if line.startswith("NUCLEUS_C256_BODY:")]
    apps = [line for line in stderr.splitlines() if line.startswith("NUCLEUS_C256_BODY_APP:")]
    terminal = [line for line in stderr.splitlines() if line.startswith("NUCLEUS_DOWNSTREAM:")]
    if completed.returncode != 2 or terminal[-1:] != [c255.TERM]:
        raise ValueError("Original whole verdict/terminal changed")
    if not body:
        raise ValueError("C256 exact body never observed")
    report = {
        "state": "WARRANTED_BOUNDED_READ_ONLY_IF_GITHUB_SUCCESS",
        "source_sha256": c255.FUELED,
        "archive_sha256": c255.ARCHIVE,
        "elapsed_s": round(time.monotonic() - start, 3),
        "whole_exit": completed.returncode,
        "whole_terminal": terminal[-1],
        "body_count": len(body),
        "body_trace_first": body[:40],
        "application_failure_count": len(apps),
        "application_trace_first": apps[:48],
        "claim_boundary": "No new ACCEPT; instrumented C255 body application only",
    }
    (args.out / "c256-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("C256_SUMMARY " + json.dumps(report, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
