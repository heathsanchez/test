"""Build-generated module -> original native pytest control, no target exposure.

A fixture is deliberately absent from its Git-like source and generated only by
the declared build backend. The installed wheel must satisfy an unchanged test;
removing the generated module must restore the native failure.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from .generic_build_materialization import materialize


def run():
    with tempfile.TemporaryDirectory(prefix="udm-wheel-native-") as td:
        root = Path(td)
        source = root / "source"
        pkg = source / "src" / "fixture_generated"
        tests = source / "tests"
        pkg.mkdir(parents=True)
        tests.mkdir()
        (pkg / "__init__.py").write_text("VALUE = 42\n")
        (source / "pyproject.toml").write_text(
            '[build-system]\nrequires = ["setuptools>=68", "wheel"]\n'
            'build-backend = "setuptools.build_meta"\n'
            '[project]\nname = "udm-native-wheel-fixture"\nversion = "0.0.1"\n'
        )
        (source / "setup.py").write_text(
            "from setuptools import setup\n"
            "from setuptools.command.build_py import build_py\n"
            "from pathlib import Path\n"
            "class Generate(build_py):\n"
            "    def run(self):\n"
            "        super().run()\n"
            "        target = Path(self.build_lib) / 'fixture_generated' / '_version.py'\n"
            "        target.parent.mkdir(parents=True, exist_ok=True)\n"
            "        target.write_text('GENERATED_VERSION = 42' + chr(10))\n"
            "setup(cmdclass={'build_py': Generate})\n"
        )
        test = tests / "test_native.py"
        test.write_text(
            "from fixture_generated._version import GENERATED_VERSION\n"
            "def test_generated_module(): assert GENERATED_VERSION == 42\n"
        )
        source_hash = hashlib.sha256(test.read_bytes()).hexdigest()
        assert not (pkg / "_version.py").exists()
        build = materialize(source, root / "output")
        python = build["interpreter"]
        subprocess.run([python, "-m", "pip", "install", "pytest==8.3.5"],
                       check=True, capture_output=True, text=True, timeout=120)
        script = (
            "import json,pytest,sys;"
            "sys.path.insert(0,sys.argv[1]);"
            "raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',"
            "'--junitxml='+sys.argv[2],sys.argv[3:]]))"
        )
        def native(label):
            xml = root / (label + ".xml")
            p = subprocess.run(
                [python, "-I", "-B", "-c", script, str(tests), str(xml), str(test)],
                cwd=root, capture_output=True, text=True, timeout=60,
                env={"PATH": "/usr/bin:/bin", "HOME": str(root),
                     "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
            return {"exit": p.returncode, "stdout": p.stdout[-1500:],
                    "stderr": p.stderr[-1500:],
                    "xml": xml.read_text()[-1200:] if xml.exists() else ""}
        positive = native("positive")
        if positive["exit"] != 0 or 'tests="1"' not in positive["xml"]:
            raise AssertionError("installed wheel did not pass unchanged native test: " + json.dumps(positive))
        site = subprocess.check_output(
            [python, "-I", "-c",
             "import fixture_generated._version as v;print(v.__file__)"],
            text=True).strip()
        generated = Path(site)
        if not generated.is_file() or not generated.is_relative_to(root / "output"):
            raise AssertionError("generated import escaped built wheel")
        generated.unlink()
        negative = native("ablation")
        if negative["exit"] == 0:
            raise AssertionError("deleting generated module did not restore native failure")
        if hashlib.sha256(test.read_bytes()).hexdigest() != source_hash:
            raise AssertionError("native test changed")
        if (pkg / "_version.py").exists():
            raise AssertionError("source fixture was modified")
        return {"schema": "udm.wheel-native-control.v1",
                "status": "PASS_BOUNDED_NATIVE_BUILD_CONTROL",
                "build_status": build["status"],
                "source_test_sha256": source_hash,
                "positive": positive, "ablation": negative,
                "claim_boundary": "fixture-only; no generic_native_verify or UDM admission yet"}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
