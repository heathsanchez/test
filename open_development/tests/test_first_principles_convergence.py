"""Fresh finite tests with no imported conceptual vocabulary.

This file asks only operational questions:
1. Which differences change witnessed outcomes?
2. Which observations can separate apparently identical descriptions?
3. What changes when a verified new ability is admitted?
4. What remains unchanged?
5. Does order matter for independent additions?
6. Does archival history matter once the active state is restored?
7. What happens when no justified change is available?

The tests deliberately avoid using any prior theoretical labels as premises.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations_with_replacement, product
from pathlib import Path
import tempfile
import unittest

from open_development.arc_discrimination import (
    ARCAdapter,
    D4,
    d4,
    form,
    freeze_state,
    grid,
)
from open_development.runtime import Developer, EvidenceStore, Obligation, digest


def make_task(value, fn):
    output = fn(grid(value))
    return {
        "train": [{"input": value, "output": [list(row) for row in output]}],
        "test": [{"input": value, "output": [list(row) for row in output]}],
    }


def public_task(task):
    return {
        "train": task["train"],
        "test": [{"input": example["input"]} for example in task["test"]],
    }


def ids_by_name(state):
    out = {}
    for rid, rec in state["capabilities"].items():
        body = rec["repair"]["payload"].get("body", {})
        if body.get("op") == "d4":
            out[body["name"]] = rid
    return out


def outcome_table(adapter, state, row_ids, tasks):
    return tuple(
        tuple(
            all(
                adapter._exec(state, rid, grid(example["input"])) == grid(example["output"])
                for example in task["train"]
            )
            for task in tasks
        )
        for rid in row_ids
    )


def collapse_table(matrix):
    rows = []
    for row in matrix:
        if row not in rows:
            rows.append(row)
    if not rows:
        return ()
    keep = []
    cols = tuple(tuple(row[j] for row in rows) for j in range(len(rows[0])))
    for j, col in enumerate(cols):
        if col not in [cols[k] for k in keep]:
            keep.append(j)
    return tuple(tuple(row[j] for j in keep) for row in rows)


def expr_eval(expr, value):
    op = expr[0]
    if op == "d4":
        return d4(value, expr[1])
    if op == "overlay":
        return form(expr_eval(expr[1], value), expr_eval(expr[2], value), "overlay")
    raise ValueError(expr)


def small_expression_family():
    base = [("d4", name) for name in D4]
    out = list(base)
    for left, right in combinations_with_replacement(base, 2):
        out.append(("overlay", left, right))
    return tuple(out)


def binary_grids(rows, cols):
    return tuple(
        tuple(
            tuple(bits[r * cols:(r + 1) * cols])
            for r in range(rows)
        )
        for bits in product((0, 1), repeat=rows * cols)
    )


def active_bodies(state):
    return tuple(sorted(
        digest({
            "body": rec["repair"]["payload"].get("body", {}),
            "contract": rec["repair"].get("contract"),
            "dependencies": rec["repair"].get("dependencies", []),
        })
        for rec in state["capabilities"].values()
    ))


class FirstPrinciplesConvergenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.sqlite"
        freeze_state(self.path)
        store = EvidenceStore(self.path)
        self.state = store.state()
        self.initial_events = len(store.events())
        store.close()
        self.adapter = ARCAdapter()
        self.base = [[1, 2, 3], [4, 5, 6]]
        self.ids = ids_by_name(self.state)
        self.tasks = tuple(
            make_task(self.base, lambda g, name=name: d4(g, name))
            for name in D4
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_01_duplicate_descriptions_add_no_new_witnessed_profile(self):
        row_ids = tuple(self.ids[name] for name in D4)
        baseline = outcome_table(self.adapter, self.state, row_ids, self.tasks)
        self.assertEqual((len(baseline), len(baseline[0])), (8, 8))
        self.assertEqual(sum(sum(row) for row in baseline), 8)

        duplicated = deepcopy(self.state)
        source = self.ids["flip-h"]
        duplicate_id = "fresh-copy-" + source
        duplicated["capabilities"][duplicate_id] = deepcopy(
            duplicated["capabilities"][source]
        )
        duplicate_task = deepcopy(self.tasks[D4.index("flip-h")])
        raw = outcome_table(
            self.adapter,
            duplicated,
            row_ids + (duplicate_id,),
            self.tasks + (duplicate_task,),
        )
        collapsed = collapse_table(raw)
        self.assertEqual((len(raw), len(raw[0])), (9, 9))
        self.assertEqual((len(collapsed), len(collapsed[0])), (8, 8))
        self.assertEqual(collapsed, baseline)
        print(
            "FACT_01_DUPLICATE_DESCRIPTION",
            "raw", (9, 9),
            "outcome_distinct", (8, 8),
        )

    def test_02_finite_agreement_does_not_license_global_identity(self):
        exprs = small_expression_family()
        seen = binary_grids(2, 2)
        heldout = binary_grids(2, 3) + binary_grids(3, 2)

        groups = {}
        for expr in exprs:
            signature = tuple(expr_eval(expr, value) for value in seen)
            groups.setdefault(signature, []).append(expr)

        splits = []
        for members in groups.values():
            if len(members) < 2:
                continue
            wider = {}
            for expr in members:
                signature = tuple(expr_eval(expr, value) for value in heldout)
                wider.setdefault(signature, []).append(expr)
            if len(wider) > 1:
                splits.append(tuple(tuple(group) for group in wider.values()))

        self.assertGreater(len(splits), 0)
        print(
            "FACT_02_FINITE_AGREEMENT_INSUFFICIENT",
            "expressions", len(exprs),
            "classes_on_2x2_binary", len(groups),
            "classes_that_split_on_rectangles", len(splits),
        )

    def test_03_a_new_observation_can_reveal_a_hidden_difference(self):
        exprs = small_expression_family()
        seen = binary_grids(2, 2)
        heldout = binary_grids(2, 3) + binary_grids(3, 2)

        groups = {}
        for expr in exprs:
            signature = tuple(expr_eval(expr, value) for value in seen)
            groups.setdefault(signature, []).append(expr)

        chosen = None
        for members in groups.values():
            if len(members) < 2:
                continue
            for query in heldout:
                outputs = [expr_eval(expr, query) for expr in members]
                if len({repr(value) for value in outputs}) > 1:
                    chosen = (members, query, outputs)
                    break
            if chosen is not None:
                break

        self.assertIsNotNone(chosen)
        members, query, outputs = chosen
        target_output = outputs[0]
        survivors = [
            expr for expr in members
            if expr_eval(expr, query) == target_output
        ]
        self.assertLess(len(survivors), len(members))
        print(
            "FACT_03_SEPARATOR_EXISTS",
            "before", len(members),
            "after_one_answer", len(survivors),
            "query_shape", (len(query), len(query[0])),
        )

    def test_04_observational_failure_to_separate_is_not_proof_of_equality(self):
        left = ("d4", "id")
        right = ("d4", "id")
        probes = binary_grids(2, 2)
        self.assertTrue(all(expr_eval(left, q) == expr_eval(right, q) for q in probes))

        # The test engine itself only observed non-separation.  Equality here is
        # licensed separately because the descriptions are structurally identical.
        observed_status = "not-separated"
        structural_status = "same-description" if left == right else "not-certified"
        self.assertEqual(observed_status, "not-separated")
        self.assertEqual(structural_status, "same-description")
        print(
            "FACT_04_NO_SEPARATOR_IS_NOT_AUTHORITY",
            "observed", observed_status,
            "independent_certificate", structural_status,
        )

    def test_05_verified_addition_preserves_every_old_behavior_on_exhaustive_probes(self):
        target = make_task(
            self.base,
            lambda g: form(g, d4(g, "flip-h"), "concat-h"),
        )
        row = {"task_id": "a", "task_sha256": digest(target), "task": public_task(target)}

        before = deepcopy(self.state)
        store = EvidenceStore(self.path)
        result = Developer(store, self.adapter).run(
            Obligation(self.adapter.name, row, 1, "method")
        )
        after = store.state()
        store.close()

        self.assertEqual(result.verdict, "verified")
        self.assertEqual(len(result.retained), 1)
        probes = binary_grids(2, 2)
        old_ids = tuple(self.ids[name] for name in D4)
        checked = 0
        for rid in old_ids:
            for probe in probes:
                checked += 1
                self.assertEqual(
                    self.adapter._exec(before, rid, probe),
                    self.adapter._exec(after, rid, probe),
                )
        learned = result.retained[0]
        self.assertTrue(all(
            self.adapter._exec(after, learned, grid(example["input"])) == grid(example["output"])
            for example in target["train"]
        ))
        print(
            "FACT_05_ADDITION_WITH_PRESERVATION",
            "old_checks", checked,
            "new_records", len(result.retained),
        )

    def test_06_two_independent_verified_additions_reach_the_same_active_state(self):
        task_a = make_task(
            self.base,
            lambda g: form(g, d4(g, "flip-h"), "concat-h"),
        )
        task_b = make_task(
            [[7, 1, 3], [2, 8, 4]],
            lambda g: form(g, d4(g, "flip-v"), "concat-v"),
        )

        def run(order):
            path = Path(self.tmp.name) / ("-".join(order) + ".sqlite")
            freeze_state(path)
            store = EvidenceStore(path)
            for name, task in (
                (("a", task_a) if order[0] == "a" else ("b", task_b)),
                (("a", task_a) if order[1] == "a" else ("b", task_b)),
            ):
                row = {"task_id": name, "task_sha256": digest(task), "task": public_task(task)}
                result = Developer(store, self.adapter).run(
                    Obligation(self.adapter.name, row, 1, "method")
                )
                self.assertEqual(result.verdict, "verified")
                self.assertEqual(len(result.retained), 1)
            state = store.state()
            store.close()
            return state

        ab = run(("a", "b"))
        ba = run(("b", "a"))
        self.assertEqual(active_bodies(ab), active_bodies(ba))
        print(
            "FACT_06_INDEPENDENT_ORDER",
            "same_active_semantics", True,
            "active_count", len(ab["capabilities"]),
        )

    def test_07_archival_history_does_not_change_future_after_active_state_is_restored(self):
        cold_path = Path(self.tmp.name) / "cold.sqlite"
        history_path = Path(self.tmp.name) / "history.sqlite"
        freeze_state(cold_path)
        freeze_state(history_path)

        task_a = make_task(
            self.base,
            lambda g: form(g, d4(g, "flip-h"), "concat-h"),
        )
        row_a = {"task_id": "a", "task_sha256": digest(task_a), "task": public_task(task_a)}

        warm = EvidenceStore(history_path)
        result = Developer(warm, self.adapter).run(
            Obligation(self.adapter.name, row_a, 1, "method")
        )
        self.assertEqual(len(result.retained), 1)
        warm.revoke(result.retained[0], "restore active state")
        restored = warm.state()
        warm_events = len(warm.events())
        warm.close()

        cold = EvidenceStore(cold_path)
        cold_state = cold.state()
        cold_events = len(cold.events())
        cold.close()

        self.assertEqual(restored, cold_state)
        self.assertGreater(warm_events, cold_events)

        future = make_task(
            [[7, 1, 3], [2, 8, 4]],
            lambda g: form(g, d4(g, "flip-v"), "concat-v"),
        )

        def continue_from(path, tag):
            store = EvidenceStore(path)
            row = {"task_id": tag, "task_sha256": digest(future), "task": public_task(future)}
            result = Developer(store, self.adapter).run(
                Obligation(self.adapter.name, row, 1, "method")
            )
            state = store.state()
            store.close()
            return result.verdict, active_bodies(state)

        cold_result = continue_from(cold_path, "future")
        history_result = continue_from(history_path, "future")
        self.assertEqual(cold_result, history_result)
        print(
            "FACT_07_ARCHIVE_NOT_ACTIVE_CAUSE",
            "different_ledger_lengths", True,
            "same_future", True,
        )

    def test_08_when_no_declared_change_is_justified_active_state_does_not_move(self):
        impossible = {
            "train": [{
                "input": self.base,
                "output": [[9, 9, 9], [9, 9, 9]],
            }],
            "test": [{
                "input": self.base,
                "output": [[9, 9, 9], [9, 9, 9]],
            }],
        }
        row = {
            "task_id": "unsupported",
            "task_sha256": digest(impossible),
            "task": public_task(impossible),
        }
        store = EvidenceStore(self.path)
        before = store.state()
        result = Developer(store, self.adapter).run(
            Obligation(self.adapter.name, row, 1, "method")
        )
        after = store.state()
        store.close()

        self.assertEqual(result.verdict, "unknown")
        self.assertEqual(result.retained, ())
        self.assertEqual(before, after)
        print(
            "FACT_08_NO_JUSTIFIED_MOVE",
            "verdict", result.verdict,
            "active_state_unchanged", True,
        )

    def test_09_first_principles_summary(self):
        print("FIRST_PRINCIPLES_CONVERGENCE_V1_COMPLETE")
        print("OBSERVED_1 outcome-equivalent duplication adds no new finite witnessed profile")
        print("OBSERVED_2 finite non-separation can be false outside the observed domain")
        print("OBSERVED_3 a separating observation can refine an unresolved set")
        print("OBSERVED_4 non-separation alone is not authority for equality")
        print("OBSERVED_5 a verified new ability can be added while preserving old behavior")
        print("OBSERVED_6 two tested independent additions commute at active semantic state")
        print("OBSERVED_7 archival history alone did not affect the tested future once active state was restored")
        print("OBSERVED_8 when no declared change was justified, active state did not move")


if __name__ == "__main__":
    unittest.main()
