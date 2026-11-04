"""Matched official/candidate/capped-Nucleus source-prefix replay; no promotion."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path("/tmp/nucleus-budget-tournament")
BASE = Path("/tmp/nucleus-eval-artifact/candidate/nucleus")
VARIANT = Path("/tmp/nucleus-source/metatron-kernel/target/release/metatron-kernel")
REFERENCE = Path("/tmp/reference/bundle/kernel")
SOURCE = ROOT / "next-frontier.ndjson"
EXPECTED = {
    str(SOURCE): "5b7a6b7ad11f5683937e8258322d47f09a9daf6d254bd921e6d23b0d1ee3b494",
    str(BASE): "23747353a359169cfc76b540260464ffa9e9e9c6035903a1e49ce3b6d2c36521",
    str(REFERENCE): "ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(label: str, cmd: list[str], use_stdin: bool, env: dict):
    start = time.monotonic()
    with (ROOT / (label + ".stdout")).open("wb") as out:
        with (ROOT / (label + ".stderr")).open("wb") as err:
            with (SOURCE.open("rb") if use_stdin else open(os.devnull, "rb")) as stream:
                result = subprocess.run(cmd, stdin=stream, stdout=out, stderr=err,
                                        env=env, timeout=240, check=False)
    return {"rc": result.returncode, "elapsed_s": round(time.monotonic()-start,3),
            "stdout": (ROOT / (label + ".stdout")).read_text(errors="replace")[:1000],
            "stderr": (ROOT / (label + ".stderr")).read_text(errors="replace")[:1000]}


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    verified_hashes = {path: digest(Path(path)) for path in EXPECTED}
    assert verified_hashes == EXPECTED, verified_hashes
    record = json.loads(Path("/tmp/nucleus-eval-artifact/qualification.json").read_text())["candidate"]
    assert record["qualified"] and record["binary_sha"] == verified_hashes[str(BASE)]
    flags = record["configuration"]
    assert len(flags) == 20 and all(k.startswith("NUCLEUS_EXPERIMENTAL_") and v == "1"
                                    for k, v in flags.items())
    env = dict(os.environ)
    env.update(flags)
    official = run("official", [str(REFERENCE), str(SOURCE)], False, env)
    original = run("original", [str(BASE)], True, env)
    budget_8192 = run("budget_8192", [str(VARIANT)], True, env)
    summary = {
        "status": "HYPOTHESIS_ONLY_UNPROTECTED",
        "change": "nested-recursion major exposure bound 512 -> 8192, same shared fuel",
        "hashes": verified_hashes, "variant_sha256": digest(VARIANT),
        "qualification_flags": flags,
        "official": official, "original": original, "budget_8192": budget_8192,
        "outcome": ("CANDIDATE_FRONTIER_ACCEPT" if budget_8192["rc"] == 0 else
                    "STILL_UNKNOWN" if budget_8192["rc"] == 2 else
                    "UNEXPECTED_NONZERO"),
    }
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("RECURSOR_BUDGET_TOURNAMENT", json.dumps({
        "official": official["rc"], "original": original["rc"],
        "budget_8192": budget_8192["rc"], "outcome": summary["outcome"]
    }), flush=True)
    assert official["rc"] == 0 and "Accepted 2453 declarations" in official["stdout"]
    assert original["rc"] == 2
    assert budget_8192["rc"] in (0, 2)


if __name__ == "__main__":
    main()
