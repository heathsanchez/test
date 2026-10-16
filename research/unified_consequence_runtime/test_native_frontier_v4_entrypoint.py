"""Source-free regression for the real -m canonical checker entrypoint.

Separate from the eight previously frozen qualifier acceptance tests. Added
before fixing the __main__ checker identity found by source review.
"""
import importlib
import runpy
import sys
import unittest
import warnings
from unittest.mock import patch

MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v4'


class NativeFrontierV4Entrypoint(unittest.TestCase):
    def test_module_execution_dispatches_through_importable_checker_module(self):
        q = importlib.import_module(MODULE)
        called = []
        def source_free_main():
            from .native_meta_decision import _checker_source
            called.append(_checker_source(q.reconstruct_profiles)['module'])
        refusal = None
        with patch.object(q, 'main', source_free_main), \
                patch.object(sys, 'argv', [MODULE, '--out', '/unused']), \
                warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            try:
                runpy.run_module(MODULE, run_name='__main__')
            except (ValueError, SystemExit) as error:
                refusal = str(error)
        self.assertEqual(called, [MODULE],
            'real -m execution did not use the canonical checker module: '+str(refusal))


if __name__ == '__main__':
    unittest.main()
