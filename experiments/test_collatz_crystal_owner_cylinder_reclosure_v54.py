import importlib.util
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location(
    "v54", HERE / "collatz_crystal_owner_cylinder_reclosure_v54.py")
v54 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = v54
SPEC.loader.exec_module(v54)


class OwnerCylinderReclosureTests(unittest.TestCase):
    def test_uniform_v2_boundary(self):
        self.assertEqual(v54.uniform_v2(12, 16), 2)
        self.assertIsNone(v54.uniform_v2(12, 4))

    def test_uniform_lower_source_is_exact_on_nonnegative_ray(self):
        closed = v54.Family(0, 0, 11, 8, 7, 8, 1)
        crossing = v54.Family(0, 0, 11, 8, 7, 16, 1)
        self.assertTrue(v54.uniform_lower_source(closed))
        self.assertFalse(v54.uniform_lower_source(crossing))

    def test_root_symbolic_blocks_replay_v53(self):
        root = v54.Family(
            0, 0, v54.v25.N0, v54.v25.NC,
            v54.v25.N0, v54.v25.NC, 0)
        status, end, path = v54.advance_until_seam(root, 32)
        self.assertEqual(status, "SPLIT")
        self.assertEqual(end.blocks, 4)
        self.assertEqual(len(path), 4)
        self.assertFalse(v54.uniform_lower_source(end))

    def test_depth_cap_survivor_is_not_reported_empty(self):
        root = v54.Family(
            0, 0, v54.v25.N0, v54.v25.NC,
            v54.v25.N0, v54.v25.NC, 0)
        status, end, _ = v54.advance_until_seam(root, 32)
        self.assertEqual(status, "SPLIT")
        self.assertEqual(len((v54.split(end, 0), v54.split(end, 1))), 2)


if __name__ == "__main__":
    unittest.main()
