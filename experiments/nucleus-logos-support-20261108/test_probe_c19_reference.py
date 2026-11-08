"""Source integrity and result-state checks for an untrusted reference kernel."""

import importlib.util
from pathlib import Path
import unittest


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
        import hashlib
        valid = b"valid source fixture"
        digest = hashlib.sha256(valid).hexdigest()
        self.probe.verify_payload("fixture", valid, digest)
        with self.assertRaises(ValueError):
            self.probe.verify_payload("fixture", valid + b"!", digest)


if __name__ == "__main__":
    unittest.main()
