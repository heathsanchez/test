"""Breaker tests for the polarized-interaction / biextensional view.

The goal is not to assume Chu/Ludics/FCA structure.  These tests ask which
parts are actually present in the frozen Open Development implementation and
which are only useful abstractions.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations, product
from pathlib import Path
import tempfile
import unittest

from open_development.arc_discrimination import d4, form, grid
from open_development.prospective_genesis import ProspectiveARCAdapter, develop_stream, freeze_state
from open_development.runtime import Developer, EvidenceStore, Obligation, digest


def public(task):
    return {
        "train": task["train"],
        "test": [{"input": example["input"]} for example in task["test"]],
    }


def full_task(value, function):
    output = [list(row) for row in function(grid(value))]
    return {
        "train": [{"input": value, "output": output}],
        "test": [{"input": value, "output": output}],
    }


def d4_tasks(value):
    return {
        name: full_task(value, lambda g, name=name: d4(g, name))
        for name in ("id", "r90", "r180", "r270", "flip-h", "flip-v", "transpose", "anti")
    }


def capability_ids_by_d4(state):
    out = {}
    for rid, rec in state["capabilities"].items():
        body = rec["repair"]["payload"].get("body", {})
        if body.get("op") == "d4":
            out[body["name"]] = rid
    return out


def interaction_matrix(adapter, state, row_ids, tasks):
    return tuple(
        tuple(adapter.solves(state, rid, task) for task in tasks)
        for rid in row_ids
    )


def transpose(matrix):
    if not matrix:
        return ()
    if not matrix[0]:
        return tuple(() for _ in range(len(matrix[0])))
    return tuple(tuple(matrix[i][j] for i in range(len(matrix))) for j in range(len(matrix[0])))


def collapse_duplicate_rows(matrix):
    seen = {}
    for row in matrix:
        seen.setdefault(tuple(row), len(seen))
    return tuple(seen)


def collapse_duplicate_cols(matrix):
    if not matrix:
        return ()
    cols = tuple(tuple(matrix[i][j] for i in range(len(matrix))) for j in range(len(matrix[0])))
    seen = {}
    for col in cols:
        seen.setdefault(col, len(seen))
    return tuple(seen)


def biextensional_signature(matrix):
    """Iteratively remove duplicate rows/columns; return canonical dimensions+matrix."""
    current = tuple(tuple(bool(x) for x in row) for row in matrix)
    while True:
        row_seen = {}
        row_indices = []
        for i, row in enumerate(current):
            if row not in row_seen:
                row_seen[row] = len(row_indices)
                row_indices.append(i)
        current = tuple(current[i] for i in row_indices)

        if current:
            cols = tuple(tuple(current[i][j] for i in range(len(current)))
                         for j in range(len(current[0])))
        else:
            cols = ()
        col_seen = {}
        col_indices = []
        for j, col in enumerate(cols):
            if col not in col_seen:
                col_seen[col] = len(col_indices)
                col_indices.append(j)
        reduced = tuple(tuple(row[j] for j in col_indices) for row in current)
        if reduced == current:
            break
        current = reduced
    return (len(current), len(current[0]) if current else 0, current)


def prime_rows(matrix, rows):
    ncols = len(matrix[0]) if matrix else 0
    return frozenset(
        j for j in range(ncols)
        if all(matrix[i][j] for i in rows)
    )


def prime_cols(matrix, cols):
    return frozenset(
        i for i in range(len(matrix))
        if all(matrix[i][j] for j in cols)
    )


class InteractionSpaceBreakerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.sqlite"
        freeze_state(self.path)
        store = EvidenceStore(self.path)
        self.state = store.state()
        store.close()
        self.adapter = ProspectiveARCAdapter()
        self.base = [[1, 2, 3], [4, 5, 6]]
        self.tasks = d4_tasks(self.base)
        self.ids = capability_ids_by_d4(self.state)

    def tearDown(self):
        self.tmp.cleanup()

    def test_01_actual_d4_interaction_matrix_is_biextensional(self):
        names = tuple(self.tasks)
        rows = tuple(self.ids[name] for name in names)
        matrix = interaction_matrix(
            self.adapter, self.state, rows, tuple(self.tasks[name] for name in names)
        )
        sig = biextensional_signature(matrix)
        self.assertEqual(sig[0], 8)
        self.assertEqual(sig[1], 8)
        self.assertEqual(sum(sum(row) for row in matrix), 8)
        print("INTERACTION_MATRIX_D4", "rows", sig[0], "cols", sig[1], "true_entries", 8)

    def test_02_biextensional_collapse_removes_dual_raw_duplicates(self):
        names = tuple(self.tasks)
        baseline_rows = tuple(self.ids[name] for name in names)
        baseline_tasks = tuple(self.tasks[name] for name in names)
        baseline = interaction_matrix(self.adapter, self.state, baseline_rows, baseline_tasks)
        baseline_sig = biextensional_signature(baseline)

        duplicated = deepcopy(self.state)
        source = self.ids["flip-h"]
        duplicate_id = "interaction-copy-" + source
        duplicated["capabilities"][duplicate_id] = deepcopy(duplicated["capabilities"][source])
        rows = baseline_rows + (duplicate_id,)
        tasks = baseline_tasks + (deepcopy(self.tasks["flip-h"]),)
        matrix = interaction_matrix(self.adapter, duplicated, rows, tasks)
        raw = (len(matrix), len(matrix[0]))
        collapsed = biextensional_signature(matrix)

        self.assertEqual(raw, (9, 9))
        self.assertEqual(collapsed[:2], baseline_sig[:2])
        self.assertEqual(biextensional_signature(collapsed[2]), collapsed)
        print(
            "BIEXTENSIONAL_DUPLICATE_COLLAPSE",
            "raw", raw,
            "collapsed", collapsed[:2],
            "baseline", baseline_sig[:2],
        )

    def test_03_new_test_splits_previously_equal_real_capabilities(self):
        ids = (self.ids["id"], self.ids["flip-h"])
        symmetric = [[1, 1], [1, 1]]
        symmetric_task = full_task(symmetric, lambda g: g)
        before = interaction_matrix(self.adapter, self.state, ids, (symmetric_task,))
        self.assertEqual(biextensional_signature(before)[0], 1)

        separator = full_task(self.base, lambda g: g)
        after = interaction_matrix(
            self.adapter, self.state, ids, (symmetric_task, separator)
        )
        self.assertEqual(biextensional_signature(after)[0], 2)
        print(
            "DISCOVERY_BY_NEW_TEST",
            "row_classes_before", 1,
            "row_classes_after", 2,
        )

    def test_04_new_capability_splits_previously_equal_real_tasks(self):
        flip_h_task = self.tasks["flip-h"]
        flip_v_task = self.tasks["flip-v"]
        before = interaction_matrix(
            self.adapter, self.state, (self.ids["id"],), (flip_h_task, flip_v_task)
        )
        self.assertEqual(biextensional_signature(before)[1], 1)

        after = interaction_matrix(
            self.adapter,
            self.state,
            (self.ids["id"], self.ids["flip-h"]),
            (flip_h_task, flip_v_task),
        )
        self.assertEqual(biextensional_signature(after)[1], 2)
        print(
            "DUAL_SPLIT_BY_NEW_CAPABILITY",
            "column_classes_before", 1,
            "column_classes_after", 2,
        )

    def test_05_biextensional_collapse_is_transpose_dual(self):
        names = tuple(self.tasks)
        rows = tuple(self.ids[name] for name in names)
        matrix = interaction_matrix(
            self.adapter, self.state, rows, tuple(self.tasks[name] for name in names)
        )
        left = biextensional_signature(matrix)
        right = biextensional_signature(transpose(matrix))
        self.assertEqual((left[0], left[1]), (right[1], right[0]))
        self.assertEqual(left[2], transpose(right[2]))
        print("TRANSPOSE_DUALITY", "original", left[:2], "transposed", right[:2])

    def test_06_actual_interaction_relation_obeys_fca_galois_closure_laws(self):
        names = tuple(self.tasks)
        rows = tuple(self.ids[name] for name in names)
        matrix = interaction_matrix(
            self.adapter, self.state, rows, tuple(self.tasks[name] for name in names)
        )
        row_sets = [
            frozenset(combo)
            for r in range(len(rows) + 1)
            for combo in combinations(range(len(rows)), r)
        ]
        col_sets = [
            frozenset(combo)
            for r in range(len(names) + 1)
            for combo in combinations(range(len(names)), r)
        ]

        for a in row_sets:
            closed = prime_cols(matrix, prime_rows(matrix, a))
            self.assertTrue(a <= closed)
            self.assertEqual(
                prime_cols(matrix, prime_rows(matrix, closed)),
                closed,
            )
        for b in col_sets:
            closed = prime_rows(matrix, prime_cols(matrix, b))
            self.assertTrue(b <= closed)
            self.assertEqual(
                prime_rows(matrix, prime_cols(matrix, closed)),
                closed,
            )

        checked = 0
        for a in row_sets:
            ap = prime_rows(matrix, a)
            for b in col_sets:
                checked += 1
                bp = prime_cols(matrix, b)
                self.assertEqual(a <= bp, b <= ap)

        print(
            "FCA_GALOIS_LAWS",
            "row_subsets", len(row_sets),
            "col_subsets", len(col_sets),
            "adjunction_checks", checked,
        )

    def test_07_real_generated_admission_is_conservative_interaction_extension(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        task_a = full_task(self.base, first)
        row = {"task_id": "a", "task_sha256": digest(task_a), "task": public(task_a)}
        body = {
            "schema": "prospective-route-neutral-stream/v1",
            "selection_nonce": "interaction-extension",
            "tasks": [row],
            "route_labels_present": False,
        }
        decisions = develop_stream({**body, "stream_digest": digest(body)}, self.path)
        self.assertEqual(decisions["results"][0]["predicted_route"], "EXPANSION")

        store = EvidenceStore(self.path)
        after = store.state()
        store.close()
        new_ids = tuple(sorted(set(after["capabilities"]) - set(self.state["capabilities"])))
        self.assertEqual(len(new_ids), 1)

        names = tuple(self.tasks)
        old_rows = tuple(self.ids[name] for name in names)
        old_tasks = tuple(self.tasks[name] for name in names)
        old_matrix = interaction_matrix(self.adapter, self.state, old_rows, old_tasks)
        preserved = interaction_matrix(self.adapter, after, old_rows, old_tasks)
        self.assertEqual(old_matrix, preserved)

        extended_matrix = interaction_matrix(
            self.adapter,
            after,
            old_rows + new_ids,
            old_tasks + (task_a,),
        )
        old_sig = biextensional_signature(old_matrix)
        new_sig = biextensional_signature(extended_matrix)
        self.assertEqual(old_sig[:2], (8, 8))
        self.assertEqual(new_sig[:2], (9, 9))
        self.assertFalse(any(self.adapter.solves(self.state, rid, task_a) for rid in old_rows))
        self.assertTrue(self.adapter.solves(after, new_ids[0], task_a))
        print(
            "REAL_INTERACTION_EXTENSION",
            "old_quotient", old_sig[:2],
            "new_quotient", new_sig[:2],
            "old_submatrix_preserved", True,
            "minimum_new_rows_given_frozen_old_semantics", 1,
        )

    def test_08_reuse_encounter_does_not_extend_active_interaction_state(self):
        task = self.tasks["id"]
        row = {"task_id": "reuse", "task_sha256": digest(task), "task": public(task)}
        before_store = EvidenceStore(self.path)
        before = before_store.state()
        before_events = len(before_store.events())
        result = Developer(before_store, self.adapter).run(
            Obligation(self.adapter.name, row, 0, "method")
        )
        after = before_store.state()
        after_events = len(before_store.events())
        before_store.close()
        self.assertEqual(result.verdict, "verified")
        self.assertEqual(before, after)
        self.assertEqual(after_events, before_events + 1)
        self.assertEqual(set(after), {"capabilities", "observations", "policies"})
        print(
            "ACTIVE_STATE_NOT_SELF_DUAL",
            "reuse_changes_active_state", False,
            "assessment_appended_to_provenance", True,
            "persistent_active_obligation_space", False,
        )

    def test_09_raw_self_duality_is_not_implemented_by_current_state_schema(self):
        # A real expansion retains a positive capability, but the encountered
        # task is not installed as a dual active object.
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        task_a = full_task(self.base, first)
        row = {"task_id": "a", "task_sha256": digest(task_a), "task": public(task_a)}
        body = {
            "schema": "prospective-route-neutral-stream/v1",
            "selection_nonce": "interaction-asymmetry",
            "tasks": [row],
            "route_labels_present": False,
        }
        decisions = develop_stream({**body, "stream_digest": digest(body)}, self.path)
        self.assertEqual(decisions["results"][0]["predicted_route"], "EXPANSION")
        store = EvidenceStore(self.path)
        after = store.state()
        store.close()
        self.assertGreater(len(after["capabilities"]), len(self.state["capabilities"]))
        self.assertNotIn("obligations", after)
        self.assertNotIn("countercontexts", after)
        print(
            "CURRENT_IMPLEMENTATION_POLARITY_ASYMMETRY",
            "positive_capability_retained", True,
            "dual_task_object_retained", False,
        )

    def test_10_archival_history_collapses_when_active_causal_state_is_restored(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        second = lambda g: form(first(g), g, "concat-h")
        task_a = full_task(self.base, first)
        task_b = full_task([[7, 1, 3], [2, 8, 4]], second)

        cold_path = Path(self.tmp.name) / "cold.sqlite"
        history_path = Path(self.tmp.name) / "history.sqlite"
        freeze_state(cold_path)
        freeze_state(history_path)

        row_a = {"task_id": "a", "task_sha256": digest(task_a), "task": public(task_a)}
        body = {
            "schema": "prospective-route-neutral-stream/v1",
            "selection_nonce": "history-collapse",
            "tasks": [row_a],
            "route_labels_present": False,
        }
        decisions = develop_stream(
            {**body, "stream_digest": digest(body)}, history_path
        )
        g1 = decisions["results"][0]["generated_admissions"][0]
        history_store = EvidenceStore(history_path)
        history_store.revoke(g1, "restore active baseline")
        restored = history_store.state()
        history_event_count = len(history_store.events())
        history_store.close()

        cold_store = EvidenceStore(cold_path)
        cold = cold_store.state()
        cold_event_count = len(cold_store.events())
        cold_store.close()
        self.assertEqual(cold, restored)
        self.assertGreater(history_event_count, cold_event_count)

        def run_ab(path):
            rows = [
                {"task_id": "a2", "task_sha256": digest(task_a), "task": public(task_a)},
                {"task_id": "b2", "task_sha256": digest(task_b), "task": public(task_b)},
            ]
            payload = {
                "schema": "prospective-route-neutral-stream/v1",
                "selection_nonce": "history-future",
                "tasks": rows,
                "route_labels_present": False,
            }
            decisions = develop_stream({**payload, "stream_digest": digest(payload)}, path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()
            return [x["predicted_route"] for x in decisions["results"]], state

        cold_routes, cold_final = run_ab(cold_path)
        history_routes, history_final = run_ab(history_path)
        self.assertEqual(cold_routes, history_routes)
        self.assertEqual(cold_final, history_final)
        print(
            "ARCHIVAL_HISTORY_OPERATIONALLY_QUOTIENTED",
            "active_states_equal_before_future", True,
            "ledger_lengths_different", True,
            "future_routes_equal", cold_routes,
            "future_active_states_equal", True,
        )

    def test_11_controller_factors_through_declared_interaction_quotient(self):
        # Raw syntax still changes candidate multiplicity, but authority should
        # now depend on the frozen interaction classes rather than that multiplicity.
        duplicated = deepcopy(self.state)
        source = self.ids["flip-h"]
        duplicated["capabilities"]["interaction-copy-" + source] = deepcopy(
            duplicated["capabilities"][source]
        )
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        task = full_task(self.base, first)
        baseline = self.adapter.generation_analysis(self.state, task)
        changed = self.adapter.generation_analysis(duplicated, task)
        self.assertEqual(baseline["minimum_survivor_count"], 1)
        self.assertEqual(changed["minimum_survivor_count"], 2)
        self.assertEqual(baseline["minimum_interaction_class_count"], 1)
        self.assertEqual(changed["minimum_interaction_class_count"], 1)

        probes = [
            [[a, b], [c, d]]
            for a, b, c, d in product((0, 1), repeat=4)
        ]

        from open_development.prospective_genesis import generated_asts
        def behavior_set(state):
            return {
                tuple(self.adapter.execute_ast(state, ast, probe) for probe in probes)
                for ast in generated_asts(state)
            }

        self.assertEqual(behavior_set(self.state), behavior_set(duplicated))
        print(
            "INTERACTION_QUOTIENT_CONTROLLER_FACTORS",
            "behavior_sets_equal", True,
            "baseline_syntactic_minima", 1,
            "duplicate_syntactic_minima", 2,
            "baseline_interaction_classes", 1,
            "duplicate_interaction_classes", 1,
        )

    def test_12_binary_orthogonality_boundary_changes_only_by_new_incidence_in_fixture(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        task_a = full_task(self.base, first)
        old_rows = tuple(self.ids[name] for name in self.tasks)
        old_incidence = tuple(self.adapter.solves(self.state, rid, task_a) for rid in old_rows)
        self.assertEqual(sum(old_incidence), 0)

        row = {"task_id": "a", "task_sha256": digest(task_a), "task": public(task_a)}
        body = {
            "schema": "prospective-route-neutral-stream/v1",
            "selection_nonce": "orthogonality-revision",
            "tasks": [row],
            "route_labels_present": False,
        }
        develop_stream({**body, "stream_digest": digest(body)}, self.path)
        store = EvidenceStore(self.path)
        after = store.state()
        store.close()
        new_ids = tuple(sorted(set(after["capabilities"]) - set(self.state["capabilities"])))
        self.assertEqual(len(new_ids), 1)
        self.assertTrue(self.adapter.solves(after, new_ids[0], task_a))
        self.assertEqual(
            tuple(self.adapter.solves(after, rid, task_a) for rid in old_rows),
            old_incidence,
        )
        print(
            "ORTHOGONALITY_EXTENSION",
            "old_positive_incidence", sum(old_incidence),
            "new_positive_incidence", 1,
            "old_incidence_preserved", True,
        )

    def test_13_interaction_space_summary(self):
        print("INTERACTION_SPACE_BREAKERS_V1_COMPLETE")
        print(
            "SURVIVES: actual finite capability/task semantics admits a two-sided "
            "biextensional collapse and FCA Galois closure"
        )
        print(
            "SURVIVES: new tests split capability identity and new capabilities "
            "dually split test identity in the finite interaction matrix"
        )
        print(
            "SURVIVES: real generated admission is a conservative extension of "
            "the old interaction submatrix on the tested finite domain"
        )
        print(
            "BREAKS: current active implementation is not self-dual; it persists "
            "capabilities but not an active dual space of obligations/countercontexts"
        )
        print(
            "SURVIVES EXPERIMENTALLY: controller authority factors through the declared frozen interaction quotient even when semantic duplicate syntax changes raw multiplicity"
        )
        print(
            "REFINES: append-only provenance is audit history, not automatically "
            "operational developmental state once active causal state is restored"
        )


if __name__ == "__main__":
    unittest.main()
