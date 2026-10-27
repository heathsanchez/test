"""Pin the actually installed Flash 1.21.0 decorator contract.

The accepted keywords are copied from runpod/flash v1.21.0
src/runpod_flash/endpoint.py::Endpoint.__init__. This static test requires
no RunPod credentials or paid GPU time.
"""

import ast
from pathlib import Path
import unittest


FLASH_1_21_ENDPOINT_KEYWORDS = {
    "name", "id", "gpu", "cpu", "workers", "idle_timeout",
    "dependencies", "system_dependencies", "accelerate_downloads",
    "volume", "datacenter", "env", "gpu_count", "execution_timeout_ms",
    "flashboot", "image", "scaler_type", "scaler_value", "template",
    "min_cuda_version", "max_concurrency",
}


class FlashDecoratorContractTests(unittest.TestCase):
    def test_no_unsupported_121_decorator_arguments(self):
        path = Path(__file__).with_name("runpod_flash_h100_bridge.py")
        module = ast.parse(path.read_text())
        decorators = [d for fn in ast.walk(module)
                      if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
                      for d in fn.decorator_list
                      if isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
                      and d.func.id == "Endpoint"]
        self.assertEqual(len(decorators), 1)
        params = {kw.arg for kw in decorators[0].keywords}
        self.assertFalse(params - FLASH_1_21_ENDPOINT_KEYWORDS,
                         f"Unsupported Flash SDK 1.21.0 kwargs: {params - FLASH_1_21_ENDPOINT_KEYWORDS}")
        # Client binding by ID is a distinct, valid SDK use; it provisions nothing.
        all_calls = [n for n in ast.walk(module)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                     and n.func.id == "Endpoint"]
        clients = [n for n in all_calls if n not in decorators]
        self.assertEqual(len(clients), 1)
        self.assertEqual({kw.arg for kw in clients[0].keywords}, {"id"})


if __name__ == "__main__":
    unittest.main()
