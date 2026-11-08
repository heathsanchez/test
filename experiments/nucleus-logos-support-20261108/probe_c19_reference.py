"""Advisory-only comparison with a SHA-pinned external reference kernel.

It may illuminate which normalizer structures matter; it cannot qualify
Nucleus, establish comparable work units, or substitute the trusted prelude
required by the reference kernel for its primitive semantics.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


REFERENCE_SHA = "54ce971a5ac2513a1bac0ac9bca73f672196c0f2"
GOOD = {
    "fueled-chain": "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a",
    "grind-ring-5": "e9c394e0ff311fd10f60dee2433a530f16e82354c32d6588a8775baa06fd221f",
    "magma-list-pair-n7": "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35",
    "magma-list-pair-n21": "b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84",
    "magma-list-deep-n21": "b7a211699ab32a5d2397319702e2d5552f5796a6bdac990efa69fb186039f526",
    "magma-list-deep-n36": "6669cee92ad330dada351ac9e63656f7e9e848dd70376f17030d64677f8c81ac",
}
BAD = {
    "bad/bugs/nat-rec-k-lie.ndjson": "5a49d132bb0c7dca091baa481333f5e97e390fde72c8ec18c6124a690ec47d7c",
    "bad/bugs/rec-missing-ih.ndjson": "8a240552317ba17d44d175c10531e5f988f55569db5eff734701735ce598fa73",
    "bad/other/nat-lit-add-bad.ndjson": "9fcac9c9e16cda51f60bbd91fd14c359bf8b2272aaf02fef86ef0c2aba9333f0",
    "bad/bugs/proj-of-stuck-prop.ndjson": "4bdc45de8980cf9cb6e712ab6260f42a89201876f096441fb5ec49e3a0052a22",
}


def verify_payload(name: str, payload: bytes, expected_digest: str) -> None:
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected_digest:
        raise ValueError(f"C19 refused modified input {name}: {actual}")


def classify_exit(rc: int) -> str:
    if rc == 0:
        return "REFERENCE_ACCEPT_UNQUALIFIED"
    if rc == 1:
        return "REFERENCE_REJECT_UNQUALIFIED"
    return "REFERENCE_UNKNOWN"


def run(binary: Path, path: Path, expected_digest: str, expected: str,
        steps: int, timeout: int) -> dict:
    data = path.read_bytes()
    verify_payload(str(path), data, expected_digest)
    command = [str(binary.resolve()), "--steps", str(steps), "-j", "1",
               "--quiet", str(path.resolve())]
    started = time.monotonic()
    try:
        process = subprocess.run(command, capture_output=True, timeout=timeout)
        rc = process.returncode
        out = process.stdout.decode(errors="replace")[-2400:]
        err = process.stderr.decode(errors="replace")[-2400:]
    except subprocess.TimeoutExpired as error:
        rc = 124
        out = ""
        err = f"reference timeout: {error}"
    return {
        "case": path.name,
        "expected": expected,
        "source_sha256": expected_digest,
        "reference_exit": rc,
        "reference_state": classify_exit(rc),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout_tail": out,
        "stderr_tail": err,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--valid-root", type=Path, required=True)
    parser.add_argument("--bad-root", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=262144)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if args.steps <= 0 or args.timeout <= 0:
        raise SystemExit("C19 requires finite positive work and wall budgets")
    records = [
        run(args.binary, args.valid_root / "good/perf" / (name + ".ndjson"),
            digest, "VALID", args.steps, args.timeout)
        for name, digest in GOOD.items()
    ]
    records.extend(
        run(args.binary, args.bad_root / path, digest,
            "FORGED", args.steps, args.timeout)
        for path, digest in BAD.items()
    )
    unexpected_accepts = [r["case"] for r in records
                          if r["expected"] == "FORGED" and r["reference_exit"] == 0]
    report = {
        "reference": "sdiehl/nano-lean",
        "reference_commit": REFERENCE_SHA,
        "verdict_authority": False,
        "trusted_prelude": False,
        "work_units_comparable_to_nucleus": False,
        "reference_step_limit": args.steps,
        "source_frozen": True,
        "results": records,
        "unexpected_forged_accepts": unexpected_accepts,
    }
    print(json.dumps(report, indent=2), flush=True)
    if unexpected_accepts:
        print("C19 reference accepted a forged fixture; not a trustworthy "
              "substitute for source-qualified Nucleus", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
