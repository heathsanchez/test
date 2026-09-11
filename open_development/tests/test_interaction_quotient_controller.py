"""Qualification tests for the interaction-quotient controller experiment.

The controller may quotient only relative to its explicitly frozen interaction
probe suite.  These tests check the intended benefit (representation-invariant
authority), active separator synthesis, and whether the chosen probe suite
accidentally merges programs that separate on a broader held-out probe family.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations, product
from pathlib import Path
import tempfile
import unittest

from open_development.arc_discrimination import d4, form, grid
from open_development.prospective_genesis import (
    INTERACTION_PROBES,
    ProspectiveARCAdapter,
    ast_key,
    freeze_state,
    generated_asts,
)
from open_development.runtime import EvidenceStore, Obligation, digest


def full_task(value, function):
    output = [list(row) for row in function(grid(value))]
    return {
        "train": [{"input": value, "output": output}],
        "test": [{"input": value, "output": output}],
    }


def public(task):
    return {
        "train": task["train"],
        "test": [{"input": example["input"]} for example in task["test"]],
    }


class InteractionQuotientControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.sqlite"
        freeze_state(self.path)
        store = EvidenceStore(self.path)
        self.state = store.state()
        store.close()
        self.adapter = ProspectiveARCAdapter()

    def tearDown(self):
        self.tmp.cleanup()

    def _duplicate_flip_h(self):
        duplicated = deepcopy(self.state)
        source = next(
            rid for rid, rec in duplicated["capabilities"].items()
            if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "flip-h"}
        )
        duplicate_id = "interaction-copy-" + source
        duplicated["capabilities"][duplicate_id] = deepcopy(
            duplicated["capabilities"][source]
        )
        return duplicated

    def test_duplicate_syntax_no_longer_changes_developmental_authority(self):
        first = lambda g: form(g, d4(g, "flip-h"), "concat-h")
        task = full_task([[1, 2, 3], [4, 5, 6]], first)
        duplicated = self._duplicate_flip_h()

        analysis = self.adapter.generation_analysis(duplicated, task)
        self.assertEqual(analysis["minimum_survivor_count"], 2)
        self.assertEqual(analysis["minimum_interaction_class_count"], 1)

        row = {"task_id": "duplicate", "task_sha256": digest(task), "task": public(task)}
        obligation = Obligation(self.adapter.name, row, 1, "method")
        evidence = self.adapter.assess(duplicated, obligation)
        self.assertEqual(evidence.residual["class"], "GENERATED_FORMATION_REQUIRED")

        proposals = list(self.adapter.propose(duplicated, obligation, evidence.residual))
        self.assertEqual(len(proposals), 1)
        verified = self.adapter.verify(duplicated, obligation, proposals[0])
        self.assertEqual(verified.verdict, "verified")
        print(
            "INTERACTION_QUOTIENT_AUTHORITY_PASS",
            "syntactic_minima", analysis["minimum_survivor_count"],
            "interaction_classes", analysis["minimum_interaction_class_count"],
            "proposal", proposals[0].id,
        )

    def test_synthesized_probe_is_first_frozen_separator_and_resolves_either_branch(self):
        value = [[0, 0], [0, 1]]
        task = full_task(
            value,
            lambda g: form(g, d4(g, "r90"), "concat-h"),
        )
        analysis = self.adapter.generation_analysis(self.state, task)
        self.assertGreater(analysis["minimum_interaction_class_count"], 1)
        separator = analysis["separator_probe"]
        self.assertIsNotNone(separator)
        index = separator["probe_index"]
        probe = separator["input"]

        reps = analysis["minimum_class_representatives"]
        for earlier in INTERACTION_PROBES[:index]:
            outputs = {
                repr(self.adapter.execute_ast(self.state, ast, earlier))
                for ast in reps
            }
            self.assertEqual(len(outputs), 1)
        selected_outputs = [
            self.adapter.execute_ast(self.state, ast, probe)
            for ast in reps
        ]
        self.assertGreater(len({repr(output) for output in selected_outputs}), 1)

        resolved_class_ids = set()
        for chosen_output in selected_outputs:
            augmented = deepcopy(task)
            augmented["train"].append({
                "input": [list(row) for row in probe],
                "output": [list(row) for row in chosen_output],
            })
            resolved = self.adapter.generation_analysis(self.state, augmented)
            self.assertEqual(resolved["minimum_interaction_class_count"], 1)
            resolved_class_ids.add(resolved["interaction_class_ids"][0])

        self.assertGreater(len(resolved_class_ids), 1)
        print(
            "SYNTHESIZED_DISTINGUISHING_QUERY_PASS",
            "initial_classes", analysis["minimum_interaction_class_count"],
            "probe_index", index,
            "branches_resolved", len(resolved_class_ids),
        )

    def test_declared_probe_quotient_does_not_hide_broader_counterexample(self):
        # Falsification attempt.  Group every generated AST by the declared
        # 2x2-binary interaction profile, then search a broader held-out family:
        # all binary 2x3 and 3x2 grids.  If a declared class splits there, the
        # current quotient is only a bounded observational quotient and must not
        # be treated as global semantic equality.
        asts = generated_asts(self.state)

        def signature(ast, probes):
            return tuple(
                self.adapter.execute_ast(self.state, ast, probe)
                for probe in probes
            )

        declared = {}
        for ast in asts:
            declared.setdefault(signature(ast, INTERACTION_PROBES), []).append(ast)

        heldout = []
        for cells in product((0, 1), repeat=6):
            heldout.append((tuple(cells[:3]), tuple(cells[3:])))
        for cells in product((0, 1), repeat=6):
            heldout.append((
                (cells[0], cells[1]),
                (cells[2], cells[3]),
                (cells[4], cells[5]),
            ))

        split_classes = []
        for members in declared.values():
            if len(members) < 2:
                continue
            heldout_profiles = {}
            for ast in members:
                heldout_profiles.setdefault(signature(ast, heldout), []).append(ast)
            if len(heldout_profiles) > 1:
                split_classes.append([
                    [ast_key(ast) for ast in group]
                    for group in heldout_profiles.values()
                ])

        print(
            "INTERACTION_QUOTIENT_HELDOUT_SPLIT_CENSUS",
            "declared_classes", len(declared),
            "syntactic_asts", len(asts),
            "heldout_probes", len(heldout),
            "split_classes", len(split_classes),
        )
        self.assertEqual(
            split_classes,
            [],
            msg="frozen 2x2 interaction quotient merges programs distinguished by held-out rectangular probes",
        )


if __name__ == "__main__":
    unittest.main()
