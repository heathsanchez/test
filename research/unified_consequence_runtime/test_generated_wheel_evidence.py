"""Generated wheel evidence and native runtime source binding contracts."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from research.unified_consequence_runtime.generated_wheel_evidence import authenticated_generated_modules


class GeneratedWheelEvidenceContracts(unittest.TestCase):
    def test_bound_generated_module(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"wheel.whl"
            original={"pkg/__init__.py":b"VALUE=1\n"}
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("pkg/__init__.py",original["pkg/__init__.py"])
                z.writestr("pkg/_version.py",b"VERSION=1\n")
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            evidence={"schema":"UDM_AUTHENTICATED_GENERATED_WHEEL_V1",
                      "source_commit":"a"*40,"source_tree_sha256":"b"*64,
                      "wheel_path":str(path),"wheel_sha256":sha,
                      "build_recipe_sha256":"c"*64,"build_environment_sha256":"d"*64}
            overlay=authenticated_generated_modules(original,evidence)
            self.assertEqual(overlay["pkg/_version.py"],b"VERSION=1\n")
            evidence["wheel_sha256"]="0"*64
            with self.assertRaises(ValueError):
                authenticated_generated_modules(original,evidence)

    def test_missing_provenance_is_unknown(self):
        with self.assertRaisesRegex(ValueError,"SCHEMA"):
            authenticated_generated_modules({},{"wheel_path":"missing"})


if __name__=="__main__":
    unittest.main()
