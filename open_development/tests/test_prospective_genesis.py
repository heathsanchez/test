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
    def fixture(self):
        first = lambda g: form(g, d4(g, "flip-h"), "concat-h")
        second = lambda g: form(first(g), g, "concat-h")
        tasks = [full_task([[1, 2, 3], [4, 5, 6]], first),
                 full_task([[7, 1, 3], [2, 8, 4]], second),
                 full_task([[9, 2, 5], [6, 3, 7]], second)]
        rows = [{"task_id": name, "task_sha256": digest(task), "task": public(task)}
                for name, task in zip(("a", "b", "c"), tasks)]
        body = {"schema": "prospective-route-neutral-stream/v1", "selection_nonce": "fixture",
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
            self.assertEqual(SUBSTRATE["nodes"], ["input", "call-retained", "crop", *FORM_OPS])
            self.assertGreater(len(candidates), 24)
            self.assertFalse(any("spec" in json.dumps(ast) for ast in candidates))
            first = lambda g: form(g, d4(g, "flip-h"), "concat-h")
            task = full_task([[1, 2, 3], [4, 5, 6]], first)
            analysis = ProspectiveARCAdapter().generation_analysis(state, task)
            self.assertEqual(analysis["minimum_size"], 4)
            self.assertEqual(analysis["smaller_survivor_count"], 0)
            self.assertEqual(analysis["minimum_survivor_count"], 1)

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
