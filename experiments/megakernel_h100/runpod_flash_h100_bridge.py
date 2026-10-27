"""GitHub Actions -> RunPod Flash -> pinned public Megakernels H100 test.

Secrets stay only in GitHub Actions. The remote worker receives test code, not
the RunPod API key. This script is intended for a single bounded experiment.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys

from runpod_flash import Endpoint, GpuType


SOURCE_PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"
ENDPOINT_NAME = "mathgraph-megakernel-h100-20261027"
ASYNC_WAIT_SECONDS = 1140


def prepare_python_build_env(root: Path, env: dict) -> dict:
    """Ensure upstream Make uses the Python with installed pybind11 headers."""
    shims = root / "python-build-tools"
    shims.mkdir()
    (shims / "python3").symlink_to(sys.executable)
    config = shims / "python3-config"
    config.write_text(
        f"#!{sys.executable}\n"
        "import shlex, sys, sysconfig\n"
        "if sys.argv[1:] == ['--extension-suffix']:\n"
        "    print(sysconfig.get_config_var('EXT_SUFFIX') or '.so')\n"
        "elif sys.argv[1:] == ['--ldflags']:\n"
        "    c = sysconfig.get_config_var\n"
        "    fields = ([f\"-L{c('LIBDIR')}\"] if c('LIBDIR') else [])\n"
        "    for k in ('LDFLAGS', 'LIBS', 'SYSLIBS'):\n"
        "        fields.extend(shlex.split(c(k) or ''))\n"
        "    print(' '.join(fields))\n"
        "else:\n"
        "    raise SystemExit('unsupported python3-config argument')\n"
    )
    config.chmod(0o755)
    build_env = env.copy()
    build_env["PATH"] = str(shims) + os.pathsep + env.get("PATH", "")
    return build_env


@Endpoint(
    name="mathgraph-megakernel-h100-20261027",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    workers=(0, 1),
    idle_timeout=10,
    execution_timeout_ms=1500000,
    dependencies=[
        "torch", "transformers==4.48.3", "accelerate",
        "safetensors", "einops", "pydra-config", "pybind11",
    ],
)
async def run_h100_differential(gate_source: str, probe_kind: str = "baseline"):
    """GPU worker executes a finite, fail-closed source-native differential test."""
    import shutil
    import subprocess
    import sys
    import tempfile
    import time
    import torch

    report = {
        "schema": "mathgraph-h100-differential-v1",
        "status": "UNKNOWN",
        "source_pin": SOURCE_PIN,
        "gpu_name": None,
        "checks": {},
        "stages": [],
    }
    started = time.monotonic()

    def stage(name, argv, timeout, cwd=None, env=None):
        begin = time.monotonic()
        try:
            p = subprocess.run(
                argv, cwd=cwd, env=env, timeout=timeout,
                capture_output=True, text=True, errors="replace", check=False,
            )
        except subprocess.TimeoutExpired as exc:
            # TimeoutExpired may retain stdout/stderr as bytes even with text=True.
            def decoded(stream):
                return (stream or b"").decode("utf-8", "replace") if isinstance(stream, bytes) else (stream or "")
            combined = decoded(exc.stdout) + "\n" + decoded(exc.stderr)
            report["stages"].append({
                "name": name, "returncode": None, "timed_out": True,
                "timeout_seconds": timeout,
                "wall_seconds": round(time.monotonic() - begin, 3),
                "output_sha256": hashlib.sha256(combined.encode()).hexdigest(),
                "output_size": len(combined), "output_tail": combined[-6500:],
            })
            raise
        combined = p.stdout + "\n" + p.stderr
        row = {
            "name": name, "returncode": p.returncode, "timed_out": False,
            "wall_seconds": round(time.monotonic() - begin, 3),
            "output_sha256": hashlib.sha256(combined.encode()).hexdigest(),
            "output_size": len(combined),
            "output_tail": combined[-6500:],
        }
        report["stages"].append(row)
        if p.returncode:
            raise RuntimeError(f"{name} failed: rc={p.returncode}")

    try:
        if not torch.cuda.is_available():
            report["status"] = "UNKNOWN_NO_CUDA"
            return report
        p = torch.cuda.get_device_properties(0)
        report["gpu_name"] = p.name
        report["sm_count"] = p.multi_processor_count
        report["torch_version"] = torch.__version__
        if "H100" not in p.name or p.multi_processor_count != 132:
            report["status"] = "UNKNOWN_NOT_132_SM_H100_SXM"
            return report
        required = ("git", "make", "nvcc", "python3")
        missing = [s for s in required if not shutil.which(s)]
        report["missing_tools"] = missing
        if missing:
            report["status"] = "UNKNOWN_REMOTE_IMAGE_MISSING_TOOLCHAIN"
            return report

        with tempfile.TemporaryDirectory(prefix="mathgraph-h100-") as root:
            root = Path(root)
            repo = root / "upstream"
            stage("clone", ["git", "clone", "--no-checkout", "--depth", "1",
                            "https://github.com/HazyResearch/Megakernels.git", str(repo)], 180)
            # Shallow checkout of a historical pin is not always available.
            # Fetch the exact commit if the initial shallow checkout omitted it.
            stage("fetch_pin", ["git", "-C", str(repo), "fetch", "--depth", "1",
                                "origin", report["source_pin"]], 120)
            stage("checkout_pin", ["git", "-C", str(repo), "checkout", "--detach",
                                   report["source_pin"]], 45)
            stage("submodules", ["git", "-C", str(repo), "submodule", "update",
                                 "--init", "--recursive"], 240)
            stage("install", [sys.executable, "-m", "pip", "install", "--no-input",
                              "-e", str(repo)], 240)

            gate = root / "gpu_megakernel_gate.py"
            gate.write_text(gate_source)
            stage("source_check", [sys.executable, str(gate), "--verify-checkout",
                                   "--repo", str(repo)], 40)
            stage("gate_self_test", [sys.executable, str(gate), "--self-test"], 40)

            env = os.environ.copy()
            env.update({
                "THUNDERKITTENS_ROOT": str(repo / "ThunderKittens"),
                "MEGAKERNELS_ROOT": str(repo),
                "PYTHON_VERSION": f"{sys.version_info.major}.{sys.version_info.minor}",
                "GPU": "H100",
            })
            env = prepare_python_build_env(root, env)
            stage("build", ["make", "-C", str(repo / "demos" / "low-latency-llama")],
                  420, env=env)
            if probe_kind == "baseline":
                fixture = root / "fixture"
                stage("fixture", [sys.executable, str(gate), "--make-fixture",
                                  "--fixture", str(fixture)], 180, env=env)
                for sched in ("rr", "dag"):
                    dest = root / f"{sched}.json"
                    try:
                        stage(f"diff_{sched}", [sys.executable, "-u", str(gate),
                             "--diff", sched, "--repo", str(repo),
                             "--fixture", str(fixture), "--out", str(dest)],
                             180, env=env)
                    finally:
                        if dest.exists():
                            report["checks"][sched] = json.loads(dest.read_text())
                report["status"] = "PASS" if all(
                    report["checks"][s]["passed"] for s in ("rr", "dag")
                ) else "REJECTED_DIFFERENTIAL"
            elif probe_kind == "lmhead":
                # Control: 2 of 3 layers. Treatment: 2 of 2 layers (LM head).
                # Both fixtures are deterministically seeded; common weights
                # have identical values and upstream code remains pinned.
                report["probe_kind"] = "lmhead"
                for case, fixture_layers in (("partial_2of3", 3), ("full_2of2", 2)):
                    stage(f"fixture_{case}",
                          [sys.executable, str(gate), "--make-fixture",
                           "--fixture", str(root / case), "--fixture-layers",
                           str(fixture_layers)], 180, env=env)
                stage("shared_weight_equivalence",
                      [sys.executable, str(gate), "--compare-fixtures",
                       "--fixture", str(root / "partial_2of3"),
                       "--other-fixture", str(root / "full_2of2")], 120, env=env)
                report["shared_fixture_weights_checked"] = True
                for case, fixture_layers, run_layers in (
                    ("partial_2of3", 3, 2), ("full_2of2", 2, 2)
                ):
                    fixture = root / case
                    dest = root / f"{case}.json"
                    try:
                        stage(f"diff_{case}",
                              [sys.executable, "-u", str(gate),
                               "--diff", "rr", "--repo", str(repo),
                               "--fixture", str(fixture), "--layer-limit",
                               str(run_layers), "--out", str(dest)],
                              120, env=env)
                    except subprocess.TimeoutExpired:
                        report["checks"][case] = {
                            "status": "UNKNOWN_NATIVE_TIMEOUT", "passed": False,
                            "lm_head_exercised": fixture_layers == run_layers,
                        }
                    finally:
                        if dest.exists():
                            report["checks"][case] = json.loads(dest.read_text())
                    # If the control itself cannot complete, do not pay for
                    # the full-model treatment; its result is uninformative.
                    if case == "partial_2of3" and not report["checks"].get(case, {}).get("passed"):
                        report["status"] = "UNKNOWN_PARTIAL_CONTROL_FAILED"
                        break
                else:
                    full = report["checks"]["full_2of2"]
                    if full.get("passed") is True:
                        report["status"] = "LMHEAD_FULL_PASS"
                    elif full.get("status") == "UNKNOWN_NATIVE_TIMEOUT":
                        report["status"] = "LMHEAD_NATIVE_TIMEOUT"
                    else:
                        report["status"] = "LMHEAD_REJECTED_DIFFERENTIAL" if full.get("passed") is False else "UNKNOWN_LMHEAD_RESULT"
            else:
                report["status"] = "UNKNOWN_UNREGISTERED_PROBE"
    except Exception as exc:
        if any(c.get("passed") is False for c in report["checks"].values()):
            report["status"] = "REJECTED_DIFFERENTIAL"
        else:
            report["status"] = "UNKNOWN_EXPERIMENT_INTERRUPTED"
        report["exception_type"] = type(exc).__name__
        report["exception_summary"] = str(exc)[:800]
    report["total_seconds"] = round(time.monotonic() - started, 3)
    return report


def select_endpoint_id(endpoints, name: str) -> str:
    """Fail closed unless exactly one deployed endpoint matches the pinned name."""
    matches = [e.get("id") for e in endpoints if e.get("name") == name]
    if len(matches) != 1 or not matches[0]:
        raise ValueError(f"expected one deployed endpoint named {name}, found {len(matches)}")
    return matches[0]


async def resolve_deployed_endpoint_id() -> str:
    """Resolve the endpoint from the Flash app's server-side environment record."""
    from runpod_flash.core.api.runpod import RunpodGraphQLClient
    from runpod_flash.core.resources.app import FlashApp

    app_name = os.environ.get("FLASH_APP", "").strip()
    if not app_name:
        raise RuntimeError("FLASH_APP is required for isolated experiment resolution")
    app = await FlashApp.from_name(app_name)
    environment = await app.get_environment_by_name(os.environ.get("FLASH_ENV", "production"))
    async with RunpodGraphQLClient() as client:
        hydrated = await client.get_flash_environment(
            {"flashEnvironmentId": environment["id"]}
        )
    if not isinstance(hydrated, dict):
        raise RuntimeError("Flash environment not available after deployment")
    return select_endpoint_id(hydrated.get("endpoints") or [], ENDPOINT_NAME)


def persist_evidence(out: Path, data: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def redact_error(exc: object) -> str:
    result = str(exc)
    secret = os.environ.get("RUNPOD_API_KEY", "")
    if secret:
        result = result.replace(secret, "[REDACTED]")
    return result[:800]


async def run_async_differential(gate_source: str, out: Path, probe_kind: str = "baseline") -> dict:
    """Submit a bounded /run job, retain its ID and poll for the actual result."""
    report = {
        "schema": "mathgraph-h100-differential-v1",
        "status": "UNKNOWN_CLIENT_STARTUP",
        "source_pin": SOURCE_PIN,
        "checks": {},
    }
    job = None
    try:
        endpoint_id = await resolve_deployed_endpoint_id()
        report["runpod_endpoint_id"] = endpoint_id
        payload = {"gate_source": gate_source}
        if probe_kind == "lmhead":
            payload["probe_kind"] = "lmhead"
        elif probe_kind != "baseline":
            raise ValueError("Unregistered RunPod probe kind")
        job = await Endpoint(id=endpoint_id).run(payload)
        if not job.id:
            raise RuntimeError("asynchronous job response has no job ID")
        report["runpod_job_id"] = job.id
        persist_evidence(out, report)  # retain ID before the long GPU wait
        print(f"MATHGRAPH_H100_ASYNC_JOB={job.id}", flush=True)

        await job.wait(timeout=ASYNC_WAIT_SECONDS)
        runpod_status = getattr(job, "_data", {}).get("status")
        report["runpod_status"] = runpod_status
        if runpod_status != "COMPLETED":
            report["status"] = ("UNKNOWN_REMOTE_JOB_FAILED" if runpod_status == "FAILED"
                                else "UNKNOWN_REMOTE_JOB_NOT_COMPLETED")
            report["remote_error_present"] = bool(job.error)
        elif job.error:
            report["status"] = "UNKNOWN_REMOTE_JOB_FAILED"
            report["exception_summary"] = redact_error(job.error)
        elif isinstance(job.output, dict):
            # A GPU-produced FAIL/REJECTED report must never be promoted to PASS.
            report = dict(job.output)
            report["runpod_status"] = runpod_status
            report["runpod_job_id"] = job.id
            report["runpod_endpoint_id"] = endpoint_id
        else:
            report["status"] = "UNKNOWN_REMOTE_MISSING_OUTPUT"
    except TimeoutError as exc:
        report["status"] = "UNKNOWN_CLIENT_TIMEOUT"
        report["exception_type"] = type(exc).__name__
        report["exception_summary"] = redact_error(exc)
        if job is not None:
            try:
                await asyncio.wait_for(job.cancel(), timeout=10)
                report["cancel_requested"] = True
            except Exception as cancel_exc:
                report["cancel_error"] = redact_error(cancel_exc)
    except Exception as exc:
        report["status"] = "UNKNOWN_CLIENT_FAILURE"
        report["exception_type"] = type(exc).__name__
        report["exception_summary"] = redact_error(exc)
        if job is not None and job.id:
            try:
                await asyncio.wait_for(job.cancel(), timeout=10)
                report["cancel_requested"] = True
            except Exception as cancel_exc:
                report["cancel_error"] = redact_error(cancel_exc)
    persist_evidence(out, report)
    return report


async def _main(out: Path, gate: Path, probe_kind: str = "baseline"):
    if not os.getenv("RUNPOD_API_KEY", "").strip():
        persist_evidence(out, {"schema": "mathgraph-h100-differential-v1",
                               "status": "UNKNOWN_NO_RUNPOD_CREDENTIAL",
                               "source_pin": SOURCE_PIN, "checks": {}})
        return 1
    data = await run_async_differential(gate.read_text(), out, probe_kind=probe_kind)
    print(json.dumps({"status": data.get("status"), "gpu_name": data.get("gpu_name"),
                      "stages": len(data.get("stages", []))}, sort_keys=True))
    allowed = ("PASS",) if probe_kind == "baseline" else (
        "LMHEAD_FULL_PASS", "LMHEAD_NATIVE_TIMEOUT", "LMHEAD_REJECTED_DIFFERENTIAL"
    )
    return 0 if data.get("status") in allowed else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gate", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--probe-kind", choices=("baseline", "lmhead"), default="baseline")
    a = p.parse_args()
    raise SystemExit(asyncio.run(_main(a.out, a.gate, a.probe_kind)))


if __name__ == "__main__":
    main()
