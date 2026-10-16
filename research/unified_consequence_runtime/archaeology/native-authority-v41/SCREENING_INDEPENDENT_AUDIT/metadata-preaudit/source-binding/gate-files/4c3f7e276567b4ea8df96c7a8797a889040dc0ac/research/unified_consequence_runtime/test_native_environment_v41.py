"""Frozen public provisioning bindings; formatting is not package authority."""
from pathlib import Path
import unittest
from . import native_environment_selection_v4 as old_selection
from . import native_environment_selection_v41 as selection
from . import native_environment_v3 as original
from . import native_environment_v4 as old_environment
from . import native_environment_v41 as environment


class NativeEnvironmentBindingsV41(unittest.TestCase):
    def test_public_requirement_types_used_by_original_provisioner_remain_exported(self):
        for name in ('canonicalize_name', 'Requirement'):
            self.assertTrue(hasattr(selection, name), name)
            self.assertIs(getattr(selection, name), getattr(old_selection, name))

    def test_original_hashlock_renderer_executes_through_versioned_binding(self):
        self.assertTrue(hasattr(selection, 'canonicalize_name'))
        self.assertTrue(hasattr(selection, 'Requirement'))
        profile = {'packages': ['pytest==8.4.1'],
                   'package_artifacts': {'pytest': {'sha256': '0' * 64}}}
        expected = 'pytest==8.4.1 --hash=sha256:' + '0' * 64 + '\n'
        self.assertEqual(environment.package_requirements(profile), expected)
        self.assertEqual(environment.package_requirements(profile),
                         old_environment.package_requirements(profile))

    def test_private_bindings_preserve_original_source_and_native_code(self):
        self.assertIs(environment.provision.__code__, original.provision.__code__)
        self.assertIs(environment.provision.__globals__['selection'], selection)
        self.assertIsNot(original.provision.__globals__['selection'], selection)
        self.assertIs(old_environment.provision.__globals__['selection'], old_selection)
        self.assertIs(environment.execution, original.execution)
        self.assertEqual(original.sha256(Path(original.__file__).read_bytes()),
                         environment.PREVIOUS_SHA256)


if __name__ == '__main__':
    unittest.main()
