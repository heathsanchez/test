import json
from pathlib import Path
import tempfile
import unittest

from open_development import prospective_oracle as oracle
from open_development.prospective_genesis import (
    FORM_OPS, SUBSTRATE, ProspectiveARCAdapter, develop_stream, evaluate_chain,
    form, freeze_state, generated_asts, grid, d4)
from open_development.runtime import EvidenceStore, digest


def full_task(value, function):
    output = [list(row) for row in function(grid(value))]
    return {"train": [{"input": value, "output": output}],
            "test": [{"input": value, "output": output}]}


def public(task):
    return {"train": task["train"], "test": [{"input": x["input"]} for x in task["test"]]}


class ProspectiveGenesisTests(unittest.TestCase):
    @staticmethod
    def object_input(offset=0):
        value = [[0] * 9 for _ in range(9)]
        cells = [(2 + offset, 2, 1), (2 + offset, 3, 1),
                 (3 + offset, 2, 1),
                 (4 + offset, 2, 1), (4 + offset, 3, 1),
                 (4 + offset, 4, 1),
                 # These distinguish mono4 from mono8, mixed-color and
                 # color-class object semantics without changing its maximum.
                 (1 + offset, 1, 1), (2 + offset, 1, 2), (8, 8, 1),
                 (0, 7, 3), (7, 0, 4)]
        for row, column, color in cells:
            value[row][column] = color
        return value

    def fixture(self):
        first = lambda g: form(g, d4(g, "flip-h"), "concat-h")
        second = lambda g: form(first(g), g, "concat-h")
        tasks = [full_task([[1, 2, 3], [4, 5, 6]], first),
                 full_task([[7, 1, 3], [2, 8, 4]], second),
                 full_task([[9, 2, 5], [6, 3, 7]], second)]
        rows = [{"task_id": name, "task_sha256": digest(task), "task": public(task)}
                for name, task in zip(("a", "b", "c"), tasks)]
        body = {"schema": "prospective-route-neutral-stream/v2", "selection_nonce": "fixture",
                "tasks": rows, "route_labels_present": False}
        return {**body, "stream_digest": digest(body)}, tasks

    def test_generated_multigeneration_continuation_and_controls(self):
        stream, tasks = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.sqlite"
            freeze_state(state)
            decisions = develop_stream(stream, state)
            self.assertEqual([x["predicted_route"] for x in decisions["results"]],
                             ["EXPANSION", "EXPANSION", "REUSE"])
            g1 = decisions["results"][0]["generated_admissions"][0]
            g2 = decisions["results"][1]["generated_admissions"][0]
            self.assertEqual(decisions["results"][1]["admitted_records"][g2]
                             ["repair"]["dependencies"], [g1])
            self.assertEqual(decisions["results"][2]["restart_execution"]["execution_traces"][0][:2],
                             [g2, g1])
            external = {name: (digest(task), task)
                        for name, task in zip(("a", "b", "c"), tasks)}
            chain = evaluate_chain(stream, decisions, external, 0, g1, 1, g2, 2, root, oracle)
            self.assertTrue(chain["passes"])
            self.assertTrue(all(chain["controls"].values()))
            self.assertEqual(chain["cold_counterfactual"]["rows"][-1]["verdict"], "unknown")

    def test_generation_is_algorithmic_and_minimal(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.sqlite"
            freeze_state(state_path)
            store = EvidenceStore(state_path)
            state = store.state()
            store.close()
            candidates = generated_asts(state)
            self.assertEqual(SUBSTRATE["schema"], "object-spatial-substrate/v2")
            self.assertTrue({"objects", "select", "transform-object", "recolor-object",
                             "render-object"} <= set(SUBSTRATE["nodes"]))
            self.assertGreater(len(candidates), 24)
            self.assertFalse(any("spec" in json.dumps(ast) for ast in candidates))
            first = lambda g: form(g, d4(g, "flip-h"), "concat-h")
            task = full_task([[1, 2, 3], [4, 5, 6]], first)
            analysis = ProspectiveARCAdapter().generation_analysis(state, task)
            self.assertEqual(analysis["minimum_size"], 4)
            self.assertEqual(analysis["smaller_survivor_count"], 0)
            self.assertEqual(analysis["minimum_survivor_count"], 1)

    def test_object_substrate_is_typed_finite_and_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.sqlite"
            freeze_state(state_path)
            store = EvidenceStore(state_path)
            state = store.state()
            store.close()
            task = full_task([[1, 0, 0], [1, 1, 0], [0, 0, 2]],
                             lambda g: ((1, 0), (1, 1)))
            analysis = ProspectiveARCAdapter().generation_analysis(state, task)
            independent = oracle.analyze(state, task)
            old = oracle.old_language_analysis(state, task)
            self.assertTrue(old["complete"])
            self.assertEqual(old["closure_cardinality"], 16)
            self.assertGreater(analysis["raw_candidate_count"], analysis["normalized_candidate_count"])
            self.assertGreater(analysis["normalized_candidate_count"], 207)
            self.assertEqual(analysis["raw_candidate_count"], independent["raw_candidate_count"])
            self.assertEqual(analysis["normalized_candidate_count"], independent["normalized_candidate_count"])
            self.assertEqual(analysis["minimum_survivors"], independent["minimum_survivors"])
            self.assertLessEqual(max(analysis["candidate_count_by_size"]), str(SUBSTRATE["maximum_ast_size"]))
            self.assertIsNotNone(analysis["minimum_size"])
            self.assertTrue(all(ast["op"] in {*FORM_OPS, "render-object"}
                                for ast in analysis["minimum_survivors"]))

    def test_object_generated_means_supports_dependent_future_fixture(self):
        a_input, c_input = self.object_input(0), self.object_input(1)
        extracted = ((1, 1, 0), (1, 0, 0), (1, 1, 1))
        rotated = [list(row) for row in d4(extracted, "r90")]
        doubled = [row + row for row in rotated]
        tasks = [
            {"train": [{"input": a_input, "output": rotated}],
             "test": [{"input": a_input, "output": rotated}]},
            {"train": [{"input": a_input, "output": doubled}],
             "test": [{"input": a_input, "output": doubled}]},
            {"train": [{"input": c_input, "output": doubled}],
             "test": [{"input": c_input, "output": doubled}]},
        ]
        rows = [{"task_id": name, "task_sha256": digest(task), "task": public(task)}
                for name, task in zip(("object-a", "object-b", "object-c"), tasks)]
        body = {"schema": "prospective-route-neutral-stream/v2", "selection_nonce": "object-fixture",
                "tasks": rows, "route_labels_present": False}
        stream = {**body, "stream_digest": digest(body)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.sqlite"
            freeze_state(state)
            decisions = develop_stream(stream, state)
            self.assertEqual([row["predicted_route"] for row in decisions["results"]],
                             ["EXPANSION", "EXPANSION", "REUSE"])
            g1 = decisions["results"][0]["generated_admissions"][0]
            g2 = decisions["results"][1]["generated_admissions"][0]
            g1_ast = decisions["results"][0]["admitted_records"][g1]["repair"]["payload"]["body"]["ast"]
            self.assertEqual(g1_ast["op"], "call")
            self.assertEqual(g1_ast["arg"]["op"], "render-object")
            self.assertIn(g1, decisions["results"][1]["admitted_records"][g2]["repair"]["dependencies"])
            external = {name: (digest(task), task)
                        for name, task in zip(("object-a", "object-b", "object-c"), tasks)}
            chain = evaluate_chain(stream, decisions, external, 0, g1, 1, g2, 2, root, oracle)
            self.assertTrue(chain["passes"])
            self.assertTrue(all(chain["controls"].values()))

    def test_unresolved_minimum_version_space_stays_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.sqlite"
            freeze_state(state_path)
            store = EvidenceStore(state_path)
            state = store.state()
            store.close()
            # On this observation r90 and flip-h coincide but neither is identity,
            # leaving two inequivalent minimum normalized ASTs.
            task = full_task([[0, 0], [0, 1]],
                             lambda g: form(g, d4(g, "r90"), "concat-h"))
            analysis = ProspectiveARCAdapter().generation_analysis(state, task)
            self.assertGreater(analysis["minimum_survivor_count"], 1)

    def test_route_and_chain_leakage_are_rejected(self):
        stream, _ = self.fixture()
        stream["ground_truth_route"] = "EXPANSION"
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            freeze_state(state)
            with self.assertRaisesRegex(ValueError, "leakage"):
                develop_stream(stream, state)


if __name__ == "__main__":
    unittest.main()
