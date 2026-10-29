"""Bounded transport tests for the pinned FLASH V16b source; no external actuation."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cold_importer import PackageError, create_package, execute, requalify, withdraw


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "learned_repair.py"


class ColdImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.package = Path(self.tmp.name) / "portable"

    def test_source_pin_and_independence_semantics(self):
        create_package(SOURCE, self.package)
        self.assertEqual(execute(self.package, 0, 0), 0)
        self.assertEqual(execute(self.package, 3, 0), 3)
        self.assertEqual(execute(self.package, 3, 7), 1)
        self.assertEqual(execute(self.package, 4, 41), 2)

    def test_every_simple_graph_up_to_six_vertices_against_independent_oracle(self):
        """Detect incorrect pruning or edge binding, not just source identity."""
        create_package(SOURCE, self.package)
        checked = 0
        for n in range(7):
            pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
            for graph in range(1 << len(pairs)):
                expected = 0
                for subset in range(1 << n):
                    if all(
                        not (graph & (1 << index) and
                             subset & (1 << a) and subset & (1 << b))
                        for index, (a, b) in enumerate(pairs)
                    ):
                        expected = max(expected, subset.bit_count())
                actual = execute(self.package, n, graph)
                self.assertEqual(actual, expected, (n, graph))
                checked += 1
        self.assertEqual(checked, 33868)

    def test_changed_source_and_manifest_are_denied(self):
        create_package(SOURCE, self.package)
        copy = self.package / "learned_repair.py"
        copy.write_bytes(copy.read_bytes() + b"\n# alteration\n")
        with self.assertRaisesRegex(PackageError, "SOURCE_HASH_MISMATCH"):
            execute(self.package, 3, 0)
        second_package = Path(self.tmp.name) / "manifest-control"
        create_package(SOURCE, second_package)
        manifest = second_package / "capability.mg"
        item = json.loads(manifest.read_text())
        item["entrypoint"] = "untrusted_method"
        manifest.write_text(json.dumps(item))
        with self.assertRaisesRegex(PackageError, "INVALID_MANIFEST"):
            execute(second_package, 3, 0)

    def test_public_reinstall_does_not_erase_revocation(self):
        create_package(SOURCE, self.package)
        withdraw(self.package)
        with self.assertRaisesRegex(PackageError, "EXISTING_PACKAGE"):
            create_package(SOURCE, self.package)

    def test_raw_local_writer_can_bypass_without_external_owner(self):
        """Known negative control: manifest authority is NOT OS-isolated."""
        create_package(SOURCE, self.package)
        withdraw(self.package)
        original = self.package / "quarantine.gen1.py"
        (self.package / "learned_repair.py").write_bytes(original.read_bytes())
        manifest = self.package / "capability.mg"
        item = json.loads(manifest.read_text())
        item["active"] = True
        manifest.write_text(json.dumps(item))
        # This successful unauthorized resurrection is a G6 obstruction, not a pass.
        self.assertEqual(execute(self.package, 4, 41), 2)

    def test_equal_information_direct_executable_ties(self):
        """A conventional caller with identical source deserves equal credit."""
        create_package(SOURCE, self.package)
        spec = importlib.util.spec_from_file_location("original_direct", SOURCE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for n, graph in [(0, 0), (3, 7), (4, 41), (5, 0), (5, 1023),
                         (6, 7), (6, 1024), (6, 16384), (6, 32767)]:
            pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
            edges = [p for k, p in enumerate(pairs) if graph & (1 << k)]
            independent = lambda m: all(not (m & (1 << i) and m & (1 << j))
                                        for i, j in edges)
            self.assertEqual(execute(self.package, n, graph),
                             mod.learned_exact_rank(n, independent), (n, graph))

    def test_undeclared_graph_domain_is_not_admitted(self):
        create_package(SOURCE, self.package)
        for n, edges in [(-1, 0), (7, 0), (3, -1), (3, 8)]:
            with self.subTest(n=n, edges=edges):
                with self.assertRaisesRegex(PackageError, "OUT_OF_SCOPE"):
                    execute(self.package, n, edges)

    def test_physical_withdrawal_and_new_generation_cold_restart(self):
        create_package(SOURCE, self.package)
        first = subprocess.run(
            [sys.executable, "-I", str(HERE / "cold_importer.py"),
             "--package", str(self.package), "--n", "4", "--edges", "41"],
            capture_output=True, text=True,
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout)["rank"], 2)
        withdraw(self.package)
        self.assertFalse((self.package / "learned_repair.py").exists())
        with self.assertRaisesRegex(PackageError, "INACTIVE_GENERATION"):
            execute(self.package, 4, 41)
        self.assertEqual(requalify(self.package), 2)
        later = subprocess.run(
            [sys.executable, "-I", str(HERE / "cold_importer.py"),
             "--package", str(self.package), "--n", "4", "--edges", "41"],
            capture_output=True, text=True,
        )
        self.assertEqual(later.returncode, 0, later.stderr)
        self.assertEqual(json.loads(later.stdout), {"generation": 2, "n": 4, "rank": 2})


if __name__ == "__main__":
    unittest.main()
