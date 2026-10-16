"""Real Metatron/FLASH lifecycle control for source-pinned generated modules.

This is a local fixture qualification, not O1/O2/O3. The wheel is supplied
rather than produced by an independently authenticated build recipe.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from .developmental_machine import Machine
from .generic_native_verify import source_identity, environment_identity, fingerprint, verify
from .native_frontier import NativeFrontierRuntime
from .qualify_recursive_frontier import _copy_qualified_state


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def machine(components, state):
    return Machine(components, state, components / "evaluator", state / "unused-native-config.json")


def fixture(root):
    repo = root / "fixture-source"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "src/sample").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "src/sample/__init__.py").write_text("VALUE = 42\n")
    (repo / "tests/test_native.py").write_text(
        "from sample._version import GENERATED_VERSION\n"
        "def test_native(): assert GENERATED_VERSION == 42\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid",
                    "commit", "-qm", "frozen"], check=True)
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    identity = source_identity(repo, commit)
    env = environment_identity(sys.executable)
    contract = {"schema": "UDM_GENERIC_NATIVE_PYTEST_V1",
                "repository": "local/real-machine-fixture",
                "repo_path": str(repo), "commit": commit, **identity,
                "interpreter": sys.executable,
                "environment_sha256": fingerprint(env),
                "protocol_binding": "a" * 64, "horizon_seconds": 7}
    wheel = root / "generated.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("src/sample/__init__.py", b"VALUE = 42\n")
        archive.writestr("src/sample/_version.py", b"GENERATED_VERSION = 42\n")
    evidence = {"schema": "UDM_AUTHENTICATED_GENERATED_WHEEL_V1",
                "source_commit": commit,
                "source_tree_sha256": identity["tracked_tree_sha256"],
                "wheel_path": str(wheel),
                "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                "build_recipe_sha256": "b" * 64,
                "build_environment_sha256": "c" * 64}
    return contract, evidence


def restart(spec_path, output):
    spec = json.loads(Path(spec_path).read_text())
    output = Path(output)
    m = machine(Path(spec["components"]), Path(spec["state"]))
    runtime = NativeFrontierRuntime(m, spec["contract"], output / "native",
                                    generated_wheel_evidence=spec["evidence"])
    try:
        runtime.execute(spec["withdrawn"])
    except PermissionError:
        pass
    else:
        raise AssertionError("withdrawn capability executed after restart")
    receipt, consequence = runtime.execute(spec["restored"])
    assert receipt["status"] == "PASS_NATIVE"
    output.mkdir(parents=True, exist_ok=True)
    (output / "restart.json").write_text(canonical({
        "status": "PASS", "process_id": os.getpid(),
        "consequence": consequence, "native": receipt["status"]}) + "\n")


def qualify(components, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    _copy_qualified_state(output)
    state = output / "state"
    m = machine(Path(components).resolve(), state)
    original = tuple(node.id for node in m.log)
    contract, evidence = fixture(output)
    cold = verify(contract, {"replacements": []}, output / "cold")
    assert cold["status"] != "PASS_NATIVE"
    runtime = NativeFrontierRuntime(m, contract, output / "native",
                                    generated_wheel_evidence=evidence)
    cap = runtime.admit({"replacements": []})
    receipt, consequence = runtime.execute(cap)
    assert receipt["status"] == "PASS_NATIVE"
    assert receipt["generated_module_count"] == 1
    unrelated = m.append("unrelated_evidence", {"fixture": "independent"})
    m.flush()
    runtime.withdraw(cap)
    try:
        runtime.execute(cap)
    except PermissionError:
        pass
    else:
        raise AssertionError("withdrawn capability still executable")
    assert unrelated in m.mt.live_ids(m.log)
    assert unrelated in m.flash_live_ids()
    restored = runtime.restore(cap)
    assert restored != cap
    m.flush()
    spec = {"components": str(Path(components).resolve()), "state": str(state),
            "contract": contract, "evidence": evidence,
            "withdrawn": cap, "restored": restored}
    spec_path = output / "restart-spec.json"
    spec_path.write_text(canonical(spec) + "\n")
    child = subprocess.run(
        [sys.executable, "-m",
         "research.unified_consequence_runtime.qualify_real_generated_lifecycle",
         "--restart", str(spec_path), "--out", str(output / "child")],
        capture_output=True, text=True, timeout=120)
    assert child.returncode == 0, (child.stdout, child.stderr)
    reloaded = machine(Path(components).resolve(), state)
    assert tuple(node.id for node in reloaded.log[:len(original)]) == original
    assert consequence in {node.id for node in reloaded.log}
    restart_result = json.loads((output / "child/restart.json").read_text())
    assert restart_result["process_id"] != os.getpid()
    result = {"status": "PASS_REAL_METATRON_FLASH_FIXTURE_LIFECYCLE",
              "original_records_retained": len(original),
              "final_records": len(reloaded.log),
              "cold_status": cold["status"],
              "native_status": receipt["status"],
              "restart": restart_result,
              "claim_boundary": "fixture wheel; build recipe and environment hashes supplied; O1/O2/O3 UNKNOWN"}
    (output / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--components")
    p.add_argument("--out", required=True)
    p.add_argument("--restart")
    args = p.parse_args()
    if args.restart:
        restart(args.restart, args.out)
    else:
        qualify(args.components, args.out)
