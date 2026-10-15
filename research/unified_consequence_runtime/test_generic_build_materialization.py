"""Pure safety checks for generic native build preparation."""
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

from research.unified_consequence_runtime.generic_build_materialization import materialize


class BuildMaterializationContracts(unittest.TestCase):
    def test_requires_declared_build_contract(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "UNKNOWN_BUILD_CONTRACT"):
                materialize(source, Path(td) / "out")

    def test_refuses_output_inside_source(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            source.mkdir()
            (source / "pyproject.toml").write_text("[build-system]\nrequires=[]\n")
            with self.assertRaisesRegex(ValueError, "overlap"):
                materialize(source, source / "out")

    def test_refuses_nonempty_destination(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            source.mkdir()
            (source / "pyproject.toml").write_text("[build-system]\nrequires=[]\n")
            out = Path(td) / "out"
            out.mkdir()
            (out / "existing").write_text("preserve")
            with self.assertRaisesRegex(ValueError, "empty"):
                materialize(source, out)
            self.assertEqual((out / "existing").read_text(), "preserve")



    def test_real_build_generated_module_control(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            pkg = source / "src" / "fixture_generated"
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("VALUE = 42\n")
            (source / "pyproject.toml").write_text(
                '[build-system]\nrequires = ["setuptools>=68", "wheel"]\n'
                'build-backend = "setuptools.build_meta"\n'
                '[project]\nname = "udm-generic-build-fixture"\nversion = "0.0.1"\n'
            )
            (source / "setup.py").write_text(
                "from setuptools import setup\n"
                "from setuptools.command.build_py import build_py\n"
                "from pathlib import Path\n"
                "class BuildGenerated(build_py):\n"
                "    def run(self):\n"
                "        super().run()\n"
                "        target = Path(self.build_lib) / 'fixture_generated' / '_version.py'\n"
                "        target.parent.mkdir(parents=True, exist_ok=True)\n"
                "        target.write_text('GENERATED_VERSION = 42' + chr(10))\n"
                "setup(cmdclass={'build_py': BuildGenerated})\n"
            )
            self.assertFalse((pkg / "_version.py").exists())
            out = root / "built"
            result = materialize(source, out)
            self.assertEqual(result["status"], "BUILT_NOT_SCIENTIFICALLY_VERIFIED")
            interpreter = Path(result["interpreter"])
            check = subprocess.run(
                [str(interpreter), "-I", "-c",
                 "from fixture_generated._version import GENERATED_VERSION; assert GENERATED_VERSION == 42"],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertFalse((pkg / "_version.py").exists())

if __name__ == "__main__":
    unittest.main()
