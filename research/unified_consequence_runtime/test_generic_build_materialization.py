"""Pure safety checks for generic native build preparation."""
import tempfile
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


if __name__ == "__main__":
    unittest.main()
