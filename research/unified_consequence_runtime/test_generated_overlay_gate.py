import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from research.unified_consequence_runtime.generated_overlay_gate import generated_overlay, UnknownBuildOverlay


class GeneratedOverlayContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.wheel = Path(self.temp.name) / "fixture.whl"

    def make_wheel(self, files):
        with zipfile.ZipFile(self.wheel, "w") as z:
            for name, content in files:
                z.writestr(name, content)
        return hashlib.sha256(self.wheel.read_bytes()).hexdigest()

    def test_admits_only_new_module_and_preserves_source(self):
        original = {"fixture/__init__.py": b"VALUE = 42\n"}
        digest = self.make_wheel([("fixture/__init__.py", original["fixture/__init__.py"]),
                                  ("fixture/_version.py", b"VERSION = '1'\n")])
        overlay = generated_overlay(self.wheel, original, expected_wheel_sha256=digest)
        self.assertEqual(overlay, {"fixture/_version.py": b"VERSION = '1'\n"})
        self.assertEqual(original["fixture/__init__.py"], b"VALUE = 42\n")

    def test_rejects_modified_tracked_source(self):
        digest = self.make_wheel([("fixture/__init__.py", b"EVIL = True\n"),
                                  ("fixture/_version.py", b"VERSION = '1'\n")])
        with self.assertRaisesRegex(UnknownBuildOverlay, "alters Git-tracked"):
            generated_overlay(self.wheel, {"fixture/__init__.py": b"VALUE = 42\n"},
                              expected_wheel_sha256=digest)

    def test_rejects_generated_test(self):
        digest = self.make_wheel([("tests/test_override.py", b"def test_fake(): pass\n")])
        with self.assertRaisesRegex(UnknownBuildOverlay, "unapproved"):
            generated_overlay(self.wheel, {}, expected_wheel_sha256=digest)

    def test_rejects_wrong_wheel_digest(self):
        self.make_wheel([("fixture/_version.py", b"VERSION = '1'\n")])
        with self.assertRaisesRegex(UnknownBuildOverlay, "digest"):
            generated_overlay(self.wheel, {}, expected_wheel_sha256="0" * 64)

    def test_rejects_duplicate_archive_members(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            digest = self.make_wheel([("fixture/_version.py", b"a"),
                                      ("fixture/_version.py", b"b")])
        with self.assertRaisesRegex(UnknownBuildOverlay, "duplicate"):
            generated_overlay(self.wheel, {}, expected_wheel_sha256=digest)


if __name__ == "__main__":
    unittest.main()
