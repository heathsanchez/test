"""Read-only, source-pinned diagnostic of the next Nucleus theorem frontier.

Never treats a diagnostic trace as an acceptance certificate. Official Lean and
the unmodified qualified candidate are independent verdict comparators.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path("/tmp/nucleus-app-frontier")
ARTIFACT = Path("/tmp/nucleus-eval-artifact")
SOURCE = ROOT / "next-frontier.ndjson"
BASE = ARTIFACT / "candidate/nucleus"
TRACE = Path("/tmp/nucleus-source/metatron-kernel/target/release/metatron-kernel")
REFERENCE = Path("/tmp/reference/bundle/kernel")

EXPECTED = {
    SOURCE: "5b7a6b7ad11f5683937e8258322d47f09a9daf6d254bd921e6d23b0d1ee3b494",
    BASE: "23747353a359169cfc76b540260464ffa9e9e9c6035903a1e49ce3b6d2c36521",
    REFERENCE: "ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def checked_run(name: str, cmd: list[str], use_stdin: bool = False, env: dict | None = None):
    out = ROOT / (name + ".stdout")
    err = ROOT / (name + ".stderr")
    started = time.monotonic()
    with out.open("wb") as output, err.open("wb") as error:
        with (SOURCE.open("rb") if use_stdin else open(os.devnull, "rb")) as input_stream:
            result = subprocess.run(cmd, stdin=input_stream, stdout=output, stderr=error,
                                    env=env, timeout=180, check=False)
    return {"rc": result.returncode, "elapsed_s": round(time.monotonic() - started, 3),
            "stdout_bytes": out.stat().st_size, "stderr_bytes": err.stat().st_size}


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    actual = {str(p): digest(p) for p in EXPECTED}
    assert all(actual[str(p)] == expected for p, expected in EXPECTED.items()), actual
    qualified = json.loads((ARTIFACT / "qualification.json").read_text())["candidate"]
    assert qualified["qualified"] and qualified["binary_sha"] == actual[str(BASE)]
    configuration = qualified["configuration"]
    assert configuration and all(key.startswith("NUCLEUS_EXPERIMENTAL_") and val == "1"
                                 for key, val in configuration.items())
    qualified_env = os.environ.copy()
    qualified_env.update(configuration)
    base = checked_run("qualified", [str(BASE)], use_stdin=True, env=qualified_env)
    reference = checked_run("official", [str(REFERENCE), str(SOURCE)])
    trace_env = qualified_env.copy()
    trace_env.update({"NUCLEUS_TRACE_DOWNSTREAM": "1",
                      "NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE": "1",
                      "NUCLEUS_TRACE_TARGET_APP": "1",
                      "METATRON_KERNEL_DIAGNOSTICS": "1"})
    diagnostic = checked_run("diagnostic", [str(TRACE)], use_stdin=True, env=trace_env)
    error = (ROOT / "diagnostic.stderr").read_text(errors="replace")
    lines = error.splitlines()
    application_lines = [line for line in lines if line.startswith("NUCLEUS_APPLICATION_FUNCTION_TYPE:")]
    downstream = [line for line in lines if line.startswith("NUCLEUS_DOWNSTREAM:")]
    target_neutral = [line for line in lines if line.startswith("NUCLEUS_TARGET_QUALIFIED_HEADS:")]
    applications = []
    for line in application_lines:
        fields = {}
        for key in ("application", "function", "argument", "context_len", "frame", "remaining"):
            match = re.search(r"(?:^|:)" + re.escape(key) + r"=(ExprId\(\d+\)|\d+)", line)
            fields[key] = match.group(1) if match else None
        fields["diagnostic_prefix"] = line[:1600]
        applications.append(fields)
    summary = {"status": "DIAGNOSTIC_ONLY", "configuration": configuration,
               "source_sha256": actual[str(SOURCE)],
               "candidate_sha256": actual[str(BASE)], "official_sha256": actual[str(REFERENCE)],
               "diagnostic_sha256": digest(TRACE),
               "baseline": base, "official": reference, "diagnostic": diagnostic,
               "application_failure_count": len(applications),
               "qualified_head_observation_count": len(target_neutral),
               "qualified_head_observations": target_neutral[:48],
               "applications": applications[:16], "terminal": downstream[-1] if downstream else None,
               "trace_line_count": len(lines), "trace_tail": lines[-8:]}
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("QUALIFIED_APP_FRONTIER", json.dumps({
        "source": summary["source_sha256"], "official_rc": reference["rc"],
        "baseline_rc": base["rc"], "diagnostic_rc": diagnostic["rc"],
        "failures": len(applications), "trace_bytes": diagnostic["stderr_bytes"],
        "terminal": summary["terminal"]}), flush=True)
    assert reference["rc"] == 0, "official Lean acceptance is a prerequisite"
    assert base["rc"] == diagnostic["rc"] == 2, "preserve first UNKNOWN"
    assert applications, "diagnostic instrumentation must identify an application"
    assert target_neutral, "the target's exact neutral conversion must be observed"


if __name__ == "__main__":
    main()
