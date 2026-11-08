"""Source integrity and result-state checks for an untrusted reference kernel."""

import importlib.util
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


PATH = Path(__file__).with_name("probe_c19_reference.py")


class ReferenceProbeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("probe_c19_reference", PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        cls.probe = module

    def test_reference_exit_does_not_claim_source_warrant(self):
        self.assertTrue(hasattr(self.probe, "classify_exit"))
        self.assertEqual(self.probe.classify_exit(0), "REFERENCE_ACCEPT_UNQUALIFIED")
        self.assertEqual(self.probe.classify_exit(1), "REFERENCE_REJECT_UNQUALIFIED")
        self.assertEqual(self.probe.classify_exit(2), "REFERENCE_UNKNOWN")
        self.assertEqual(self.probe.classify_exit(124), "REFERENCE_UNKNOWN")

    def test_changed_source_is_refused_before_running_checker(self):
        self.assertTrue(hasattr(self.probe, "verify_payload"))
        valid = b"valid source fixture"
        digest = hashlib.sha256(valid).hexdigest()
        self.probe.verify_payload("fixture", valid, digest)
        with self.assertRaises(ValueError):
            self.probe.verify_payload("fixture", valid + b"!", digest)


    def test_term_core_ablation_does_not_change_default_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test.ndjson"
            source.write_bytes(b"a frozen test")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            completed = subprocess.CompletedProcess([], 0, b"ok", b"")
            with patch.object(self.probe.subprocess, "run", return_value=completed) as invoke:
                self.probe.run(Path(directory) / "nl-fast", source, digest,
                               "VALID", 262144, 60, core="term")
                self.assertIn("--term-core", invoke.call_args.args[0])
                self.probe.run(Path(directory) / "nl-fast", source, digest,
                               "VALID", 262144, 60)
                self.assertNotIn("--term-core", invoke.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
