"""Generated-wheel native lifecycle with real pytest and Metatron-like bookkeeping.

The native worker is real. MemoryMachine is the existing test double; this is
not a separate-process production Metatron/FLASH qualification.
"""
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from research.unified_consequence_runtime import generic_native_verify as verifier
from research.unified_consequence_runtime.native_frontier import NativeFrontierRuntime
from research.unified_consequence_runtime.test_native_frontier import MemoryMachine


class GeneratedWheelLifecycle(unittest.TestCase):
    def test_native_admit_revoke_restore_reload(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            repo=root/"source"
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
                            "-c","user.email=fixture@example.invalid","commit","-qm","frozen"],check=True)
            commit=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
            identity=verifier.source_identity(repo,commit)
            env=verifier.environment_identity(sys.executable)
            contract={"schema":verifier.SCHEMA,"repository":"local/generated-lifecycle",
                      "repo_path":str(repo),"commit":commit,**identity,
                      "interpreter":sys.executable,
                      "environment_sha256":verifier.fingerprint(env),
                      "protocol_binding":"a"*64,"horizon_seconds":7}
            wheel=root/"generated.whl"
            with zipfile.ZipFile(wheel,"w") as z:
                z.writestr("src/sample/__init__.py",b"VALUE = 42\n")
                z.writestr("src/sample/_version.py",b"GENERATED_VERSION = 42\n")
            evidence={"schema":"UDM_AUTHENTICATED_GENERATED_WHEEL_V1",
                      "source_commit":commit,"source_tree_sha256":identity["tracked_tree_sha256"],
                      "wheel_path":str(wheel),
                      "wheel_sha256":hashlib.sha256(wheel.read_bytes()).hexdigest(),
                      "build_recipe_sha256":"b"*64,"build_environment_sha256":"c"*64}
            machine=MemoryMachine()
            runtime=NativeFrontierRuntime(machine,contract,root/"runs",generated_wheel_evidence=evidence)
            cold=verifier.verify(contract,{"replacements":[]},root/"cold")
            self.assertNotEqual(cold["status"],"PASS_NATIVE")
            key=runtime.admit({"replacements":[]})
            first,consequence=runtime.execute(key)
            self.assertEqual(first["status"],"PASS_NATIVE")
            self.assertEqual(first["generated_module_count"],1)
            unrelated=machine.append("unrelated_evidence",{"status":"retained"})
            runtime.withdraw(key)
            with self.assertRaises(PermissionError):
                runtime.execute(key)
            self.assertIn(unrelated,machine.live_ids(machine.log))
            restored=runtime.restore(key)
            self.assertNotEqual(key,restored)
            loaded=MemoryMachine()
            loaded.log=copy.deepcopy(machine.log)
            loaded.objects=copy.deepcopy(machine.objects)
            restarted=NativeFrontierRuntime(loaded,contract,root/"restart",generated_wheel_evidence=evidence)
            after,final=restarted.execute(restored)
            self.assertEqual(after["status"],"PASS_NATIVE")
            self.assertIn(final,loaded.live_ids(loaded.log))
            self.assertFalse((repo/"src/sample/_version.py").exists())
            # A different wheel digest must not inherit the old authority.
            bad=dict(evidence,wheel_sha256="0"*64)
            rejected=NativeFrontierRuntime(loaded,contract,root/"bad",generated_wheel_evidence=bad)
            with self.assertRaises(ValueError):
                rejected.admit({"replacements":[]})


if __name__=="__main__":
    unittest.main()
