import tempfile
from pathlib import Path
import unittest

from experiments.gpu_developmental_optimization_v1.run import (
    acquire_capabilities,
    generate_targets,
    run_arm,
    serialize_caps,
    sham_caps,
    source_kernels,
)


class GPUDevelopmentalOptimizationV1Tests(unittest.TestCase):
    def test_source_acquisition_and_restart(self):
        caps = acquire_capabilities(source_kernels())
        self.assertEqual(
            {c.transformation for c in caps},
            {"remove_identity", "fuse_adjacent_affine"},
        )
        with tempfile.TemporaryDirectory() as td:
            restarted = serialize_caps(caps, Path(td) / "caps.json")
            self.assertEqual(caps, restarted)

    def test_warm_reduces_search_and_ablation_restores(self):
        caps = acquire_capabilities(source_kernels())
        targets = generate_targets("frozen-test-seed", count=24)
        cold = run_arm("cold", (), targets)
        warm = run_arm("warm", caps, targets)
        sham = run_arm("sham", sham_caps(caps), targets)
        ablation = run_arm("ablation", (), targets)
        self.assertLess(warm["total_developmental_search_cost"], cold["total_developmental_search_cost"])
        self.assertLess(warm["total_developmental_search_cost"], sham["total_developmental_search_cost"])
        self.assertEqual(ablation["total_developmental_search_cost"], cold["total_developmental_search_cost"])
        self.assertGreater(warm["reuse_hits"], 0)


if __name__ == "__main__":
    unittest.main()
