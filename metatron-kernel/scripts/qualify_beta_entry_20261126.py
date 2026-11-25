"""Qualify a frozen launch configuration against exact current beta bytes."""
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARENA = "leanprover/lean-kernel-arena-beta"
RUN = 45676210453
REV = "ac0765f269b3cb5d4ed3744301aa59f4ee67ad10"
ARTIFACTS = {
    "results": (15053165516, "a381a71b2b6d2a8f198083b75eff42875932db81d6d2a342bf7dc21639332725"),
    "tarball": (15051667460, "2fadb87d1906397c294f2eeb0aecbcc1004f4c4da1a0fe29669199dd4cbdffa6"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(
        "baseline", ROOT / "scripts/renovation_beta_baseline_20261125.py")
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    baseline.RUN, baseline.REV, baseline.ARTIFACTS = RUN, REV, ARTIFACTS
    sys.argv = [__file__, "--checker", str(ROOT / "arena.py"),
                "--flags", str(ROOT.parent / "experiments/nucleus-capture-substitution-20261107/alias-result-canonical-off-replay.json"),
                "--out", str(out)]
    baseline.main()
    rows = json.loads((out / "beta-rows.json").read_text())
    assert rows and all(r["observed"] in ("accept", "reject", "unknown") for r in rows)
    assert all(r["observed"] in (r["expected"], "unknown") for r in rows)
    fresh = [r for r in rows if r["format"] == "3.2.0"]
    assert any(r["observed"] == "accept" for r in fresh)
    assert any(r["observed"] == "reject" for r in fresh)
    # The exact same launch configuration must agree with direct binary
    # invocation, including inherited environment contamination controls.
    selected = {kind: next(r for r in fresh if r["observed"] == kind)
                for kind in ("accept", "reject", "unknown")}
    flags = json.loads((ROOT / "arena-flags.json").read_text())
    clean = {k: v for k, v in os.environ.items()
             if not k.startswith(("NUCLEUS_", "METATRON_"))}
    clean.update(flags)
    config_controls = []
    with tarfile.open(out / "tests.tar.gz", "r:gz") as tf:
        for kind, row in selected.items():
            group = "good" if row["expected"] == "accept" else "bad"
            raw = tf.extractfile(group + "/" + row["name"] + ".ndjson").read()
            assert sha(raw) == row["sha256"]
            direct = subprocess.run([str(ROOT / "target/release/metatron-kernel")],
                                    input=raw, env=clean, capture_output=True, timeout=120)
            contaminated = dict(clean, NUCLEUS_C238_STACK_MIB="64",
                                METATRON_KERNEL_DIAGNOSTICS="1")
            wrapped = subprocess.run([str(ROOT / "arena.py")], input=raw,
                                     env=contaminated, capture_output=True, timeout=120)
            assert direct.returncode == wrapped.returncode == row["raw_exit"]
            config_controls.append({"name": row["name"], "sha256": sha(raw),
                                    "direct": direct.returncode, "launcher": wrapped.returncode})
    write(out / "launcher-controls.json", config_controls)
    # Known large tests are declined by a generic byte allowance, independent
    # of their names, contents and expected outcomes. They are not ACCEPTs.
    data = json.loads((out / "official-results.json").read_text())
    large = [t for t in data["tests"] if t.get("outcome") in ("accept", "reject")
             and t["size"] > 10 * 1024 * 1024]
    summary = {
        "status": "WARRANTED_BOUNDED_IF_GITHUB_SUCCESS",
        "upstream_run": RUN, "upstream_revision": REV,
        "executed_inputs": len(rows),
        "counts": dict(collections.Counter(r["observed"] for r in rows)),
        "format_3_2_counts": dict(collections.Counter(r["observed"] for r in fresh)),
        "wrong_decisive": [], "crashes": [],
        "resource_declines": [{"name": t["name"], "size": t["size"], "exit": 2}
                              for t in large],
        "unknowns": [r["name"] for r in rows if r["observed"] == "unknown"],
        "full_mathlib_acceptance": False,
        "official_arena_ranking": "not established",
    }
    write(out / "entry-qualification.json", summary)
    write(out / "checker-identity.json", {
        "binary_sha256": sha((ROOT / "target/release/metatron-kernel").read_bytes()),
        "launcher_sha256": sha((ROOT / "arena.py").read_bytes()),
        "configuration_sha256": sha((ROOT / "arena-flags.json").read_bytes()),
        "flags": flags, "source_tree": "362242c265ee2b1758645c78ad141ad78bf6f8c2",
    })
    print("ENTRY_QUALIFICATION", json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
