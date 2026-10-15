"""Native verifier + authenticated generated wheel control, local Git fixture only."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from research.unified_consequence_runtime import generic_native_verify as v
from research.unified_consequence_runtime.generated_overlay_gate import generated_overlay, UnknownBuildOverlay


class NativeGeneratedOverlayIntegration(unittest.TestCase):
    def test_original_native_verifier_generated_module_and_ablation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            repo=root/"repo"
            repo.mkdir()
            subprocess.run(["git","init","-q",str(repo)],check=True)
            (repo/"src/sample").mkdir(parents=True)
            (repo/"tests").mkdir()
            (repo/"src/sample/__init__.py").write_text("VALUE = 42\n")
            (repo/"tests/test_native.py").write_text(
                "from sample._version import GENERATED_VERSION\n"
                "def test_native(): assert GENERATED_VERSION == 42\n")
            subprocess.run(["git","-C",str(repo),"add","."],check=True)
            subprocess.run(["git","-C",str(repo),"-c","user.name=Fixture",
                            "-c","user.email=fixture@example.invalid","commit","-qm","freeze"],check=True)
            commit=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
            identity,files,_=v._snapshot(repo,commit)
            environment=v.environment_identity(sys.executable)
            contract={"schema":v.SCHEMA,"repository":"local/generated-control",
                      "repo_path":str(repo),"commit":commit,**identity,
                      "interpreter":sys.executable,"environment_sha256":v.fingerprint(environment),
                      "protocol_binding":"a"*64,"horizon_seconds":7}
            wheel=root/"generated.whl"
            with zipfile.ZipFile(wheel,"w") as archive:
                archive.writestr("src/sample/__init__.py",files["src/sample/__init__.py"])
                archive.writestr("src/sample/_version.py",b"GENERATED_VERSION = 42\n")
            digest=hashlib.sha256(wheel.read_bytes()).hexdigest()
            overlay=generated_overlay(wheel,files,expected_wheel_sha256=digest)
            self.assertEqual(set(overlay),{"src/sample/_version.py"})
            cold=v.verify(contract,{"replacements":[]},root/"cold")
            self.assertNotEqual(cold["status"],"PASS_NATIVE")
            warm=v.verify(contract,{"replacements":[]},root/"warm",generated_modules=overlay)
            self.assertEqual(warm["status"],"PASS_NATIVE",warm)
            self.assertEqual(warm["junit"]["passed"],1)
            self.assertEqual(warm["generated_module_count"],1)
            self.assertIn("src/sample/_version.py",[x["path"] for x in warm["import_manifest"]])
            self.assertFalse((repo/"src/sample/_version.py").exists())
            with self.assertRaisesRegex(UnknownBuildOverlay,"unapproved"):
                v.verify(contract,{"replacements":[]},root/"wrong",
                         generated_modules={"tests/test_native.py":b"pass\n"})
            with self.assertRaisesRegex(UnknownBuildOverlay,"digest"):
                generated_overlay(wheel,files,expected_wheel_sha256="0"*64)


if __name__=="__main__":
    unittest.main()
