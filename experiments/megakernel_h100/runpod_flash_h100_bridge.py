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


def prepare_python_build_env(root: Path, env: dict) -> dict:
    """Make upstream's `python3`/`python3-config` use the pip worker Python.

    The pinned Makefile invokes those executable names without customization.
    RunPod's image can resolve them to `/usr/bin/python3` while installing
    packages into `sys.executable`, which breaks pybind11 header discovery.
    The local tool shims preserve the upstream source tree byte for byte.
    """
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
async def run_h100_differential(gate_source: str):
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
        "source_pin": "7309cec801537b61fea3b50d7dfe454a6cde578e",
        "gpu_name": None,
        "checks": {},
        "stages": [],
    }
    started = time.monotonic()

    def stage(name, argv, timeout, cwd=None, env=None):
        begin = time.monotonic()
        p = subprocess.run(
            argv, cwd=cwd, env=env, timeout=timeout,
            capture_output=True, text=True, errors="replace", check=False,
        )
        combined = p.stdout + "\n" + p.stderr
        row = {
            "name": name, "returncode": p.returncode,
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
            fixture = root / "fixture"
            stage("fixture", [sys.executable, str(gate), "--make-fixture",
                              "--fixture", str(fixture)], 180, env=env)
            for sched in ("rr", "dag"):
                dest = root / f"{sched}.json"
                try:
                    stage(f"diff_{sched}", [sys.executable, str(gate),
                         "--diff", sched, "--repo", str(repo),
                         "--fixture", str(fixture), "--out", str(dest)],
                         180, env=env)
                finally:
                    if dest.exists():
                        report["checks"][sched] = json.loads(dest.read_text())
            report["status"] = "PASS" if all(
                report["checks"][s]["passed"] for s in ("rr", "dag")
            ) else "REJECTED_DIFFERENTIAL"
    except Exception as exc:
        if any(c.get("passed") is False for c in report["checks"].values()):
            report["status"] = "REJECTED_DIFFERENTIAL"
        else:
            report["status"] = "UNKNOWN_EXPERIMENT_INTERRUPTED"
        report["exception_type"] = type(exc).__name__
        report["exception_summary"] = str(exc)[:800]
    report["total_seconds"] = round(time.monotonic() - started, 3)
    return report


async def _main(out: Path, gate: Path):
    if not os.getenv("RUNPOD_API_KEY", "").strip():
        raise RuntimeError("Missing GitHub repository secret RUNPOD_API_KEY")
    data = await run_h100_differential(gate.read_text())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": data.get("status"), "gpu_name": data.get("gpu_name"),
                      "stages": len(data.get("stages", []))}, sort_keys=True))
    return 0 if data.get("status") == "PASS" else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gate", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(asyncio.run(_main(a.out, a.gate)))


if __name__ == "__main__":
    main()
