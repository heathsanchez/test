"""Small bounded interaction tests over the C38 binary and immutable originals.

Each arm uses the same 262144-step limit and selected 24 flags. These are
diagnostic combinations, not source qualification or a promoted kernel.
"""

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from probe_c35_metered_recursor import ORIGINAL_INPUTS


CASES = ("fueled-chain", "magma-list-pair-n7", "magma-list-deep-n36")
ARMS = {
    "c38-only": {},
    "c38-metered-iota": {"NUCLEUS_DIAGNOSTIC_C35_ACTUAL_RECURSOR_CHARGE": "1"},
    "c38-source-probe": {
        "NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE": "1",
        "NUCLEUS_DIAGNOSTIC_C33_SOURCE_CONGRUENCE_GRANT": "512",
        "NUCLEUS_DIAGNOSTIC_C34_FALLBACK_RESERVE_DIVISOR": "2",
    },
    "c38-full-crosshead": {
        "NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_REPLAY": "1",
        "NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_GRANT": "262144",
        "NUCLEUS_DIAGNOSTIC_C37_FULL_OWNER": "1",
    },
}


def replay(job: tuple[str, str]) -> dict:
    case, arm = job
    path = Path("arena207/good/perf") / f"{case}.ndjson"
    source = path.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if ORIGINAL_INPUTS.get(case) != digest:
        raise ValueError(f"not original: {case}")
    flags = json.loads(Path("base/flags.json").read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("selected flag mismatch")
    env = {key: value for key, value in os.environ.items() if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE"] = "1"
    env.update(ARMS[arm])
    start = time.monotonic()
    result = subprocess.run([str(Path("candidate/metatron-kernel").resolve())],
                            input=source, capture_output=True, env=env, timeout=180)
    if result.returncode not in (0, 2) or result.stdout:
        raise ValueError(f"outside verifier boundary: {case}:{arm}:{result.returncode}")
    stderr = result.stderr.decode(errors="replace")
    return {"case": case, "arm": arm, "source_sha256": digest,
            "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if result.returncode == 0 else "UNKNOWN",
            "elapsed_seconds": round(time.monotonic() - start, 2),
            "c38_early_proven": sum("proved=true" in line for line in stderr.splitlines()
                                     if line.startswith("NUCLEUS_C38_EARLY_ATTEMPT:"))}


if __name__ == "__main__":
    jobs = [(case, arm) for case in CASES for arm in ARMS]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        rows = list(executor.map(replay, jobs))
    Path("reports/c38-interaction-cycles.json").write_text(json.dumps(rows, indent=2))
    for row in rows:
        print(json.dumps(row), flush=True)
