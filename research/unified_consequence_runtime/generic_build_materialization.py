"""Generic build-materialization gate for frozen native frontiers.

This module never chooses a repair or inspects a target's test outcomes.
It prepares an independently pinned source tree through the project's declared
PEP 517 wheel build, then imports from the installed wheel rather than a raw
Git-object copy (which may omit generated modules).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(argv, *, cwd=None, timeout=300):
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(json.dumps({
            "argv": argv, "returncode": result.returncode,
            "stdout_tail": result.stdout[-4000:],
            "stderr_tail": result.stderr[-4000:],
        }, sort_keys=True))
    return {"argv": argv, "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:]}


def materialize(source, destination, *, python=sys.executable, timeout=300):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not (source / "pyproject.toml").is_file():
        raise ValueError("UNKNOWN_BUILD_CONTRACT: no pyproject.toml")
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError("source/output overlap")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-build-") as td:
        wheelhouse = Path(td) / "wheels"
        wheelhouse.mkdir()
        build = command([python, "-m", "pip", "wheel", "--no-deps",
                         "--wheel-dir", str(wheelhouse), str(source)], timeout=timeout)
        wheels = sorted(wheelhouse.glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError("UNKNOWN_BUILD_OUTPUT: expected one wheel")
        wheel = wheels[0]
        environment = destination / "venv"
        venv.EnvBuilder(with_pip=True, clear=False).create(environment)
        interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        install = command([str(interpreter), "-m", "pip", "install", "--no-deps",
                           str(wheel)], timeout=timeout)
        report = {"schema": "udm.generic-build-materialization.v1",
                  "status": "BUILT_NOT_SCIENTIFICALLY_VERIFIED",
                  "source": str(source), "source_pyproject_sha256": sha256(source / "pyproject.toml"),
                  "wheel_filename": wheel.name, "wheel_sha256": sha256(wheel),
                  "interpreter": str(interpreter),
                  "build": build, "install": install,
                  "limitations": ["build backend executes source-controlled code",
                                  "wheel build does not verify protected native outcomes",
                                  "wheel dependencies are not installed by this gate",
                                  "no prospective target was evaluated"]}
        (destination / "build-receipt.json").write_text(json.dumps(report, indent=2) + "\n")
        return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--python", default=sys.executable)
    args = p.parse_args()
    print(json.dumps(materialize(args.source, args.out, python=args.python), indent=2))


if __name__ == "__main__":
    main()
