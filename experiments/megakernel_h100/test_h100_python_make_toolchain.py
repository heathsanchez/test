"""Regression: upstream Make must use the same Python as the Flash worker."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile
import types
import unittest
from unittest.mock import patch


BRIDGE = Path(__file__).with_name("runpod_flash_h100_bridge.py")


def load_bridge_without_live_runpod():
    """Only replace the external decorator; execute our toolchain code unchanged."""
    runpod_stub = types.ModuleType("runpod_flash")
    runpod_stub.Endpoint = lambda **kwargs: lambda func: func
    runpod_stub.GpuType = types.SimpleNamespace(NVIDIA_H100_80GB_HBM3="h100")
    spec = importlib.util.spec_from_file_location("mg_h100_bridge_test", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"runpod_flash": runpod_stub}):
        spec.loader.exec_module(module)
    return module


class H100MakeToolchainTests(unittest.TestCase):
    def test_upstream_make_resolves_worker_python_and_config(self):
        bridge = load_bridge_without_live_runpod()
        self.assertTrue(hasattr(bridge, "prepare_python_build_env"),
                        "H100 bridge has no worker-Python Make toolchain setup")
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            fallback = root / "fallback"
            fallback.mkdir()
            # Reproduce the H100 environment: the first `python3` in PATH is
            # incompatible with the interpreter that installed pybind11.
            alien = fallback / "python3"
            alien.write_text("#!/bin/sh\necho wrong-interpreter\n")
            alien.chmod(0o755)
            makefile = root / "Makefile"
            makefile.write_text(
                "PYTHON := $(shell python3 -c 'import sys,os;print(os.path.realpath(sys.executable))')\n"
                "SUFFIX := $(shell python3-config --extension-suffix)\n"
                "LDFLAGS := $(shell python3-config --ldflags)\n"
                "all:\n"
                "\t@printf 'INTERPRETER=%s\\nSUFFIX=%s\\nLDFLAGS=%s\\n' "
                "'$(PYTHON)' '$(SUFFIX)' '$(LDFLAGS)'\n"
            )
            env = os.environ.copy()
            env["PATH"] = str(fallback) + os.pathsep + env["PATH"]
            configured = bridge.prepare_python_build_env(root, env)
            completed = subprocess.run(
                ["make", "--no-print-directory", "-C", str(root)],
                text=True, capture_output=True, env=configured,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(f"INTERPRETER={os.path.realpath(sys.executable)}", completed.stdout)
            self.assertIn(f"SUFFIX={sysconfig.get_config_var('EXT_SUFFIX')}", completed.stdout)
            self.assertNotIn("wrong-interpreter", completed.stdout)
            self.assertIn("-L", completed.stdout)


if __name__ == "__main__":
    unittest.main()
