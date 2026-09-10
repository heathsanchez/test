"""Breaker tests for the continuation-law / invariance hypothesis.

These tests are intentionally adversarial. They distinguish what follows from
finite mathematics from what requires extra structure. They do not alter the
developmental kernel and they do not promote gauge/physics language unless the
corresponding structure is actually present.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations, product
from math import inf, log
from pathlib import Path
import tempfile
import unittest

from open_development.arc_discrimination import form, grid
from open_development.prospective_genesis import (ProspectiveARCAdapter, ast_key, develop_stream, freeze_state, generated_asts)
from open_development.runtime import Developer, EvidenceStore, Obligation, digest


@dataclass(frozen=True)
class Machine:
    states: tuple[str, ...]
    inputs: tuple[str, ...]
    step: dict[tuple[str, str], tuple[int, str]]


def trace(machine: Machine, state: str, word: tuple[str, ...]):
    outputs = []
    current = state
    for symbol in word:
        evidence, current = machine.step[(current, symbol)]
        outputs.append(evidence)
    return tuple(outputs), current


def words(alphabet: tuple[str, ...], max_length: int):
    yield ()
    for n in range(1, max_length + 1):
        yield from product(alphabet, repeat=n)


def mealy_partition(machine: Machine):
    """Coarsest deterministic Mealy behavioral partition by refinement."""
    blocks = [frozenset(machine.states)]
    changed = True
    while changed:
        changed = False
        block_index = {s: i for i, block in enumerate(blocks) for s in block}
        new_blocks = []
        for block in blocks:
            buckets = {}
            for state in block:
                signature = tuple(
                    (machine.step[(state, symbol)][0],
                     block_index[machine.step[(state, symbol)][1]])
                    for symbol in machine.inputs
                )
                buckets.setdefault(signature, set()).add(state)
            if len(buckets) > 1:
                changed = True
            new_blocks.extend(
                frozenset(value)
                for _, value in sorted(buckets.items(), key=lambda item: repr(item[0]))
            )
        blocks = new_blocks
    return tuple(sorted(blocks, key=lambda block: tuple(sorted(block))))


def canonical_partition(blocks):
    return tuple(sorted(
        (tuple(sorted(block)) for block in blocks),
        key=lambda block: (block[0], len(block), block),
    ))


def all_partitions(n: int):
    if n == 0:
        return ((),)
    output = []

    def rec(labels, max_label):
        if len(labels) == n:
            blocks = {}
            for i, label in enumerate(labels):
                blocks.setdefault(label, []).append(i)
            output.append(canonical_partition(blocks.values()))
            return
        for label in range(max_label + 2):
            labels.append(label)
            rec(labels, max(max_label, label))
            labels.pop()

    rec([0], 0)
    return tuple(dict.fromkeys(output))


def refine_partition(partition, labels):
    output = []
    for block in partition:
        by_label = {}
        for element in block:
            by_label.setdefault(labels[element], []).append(element)
        output.extend(tuple(group) for _, group in sorted(by_label.items()))
    return canonical_partition(output)


def z3_torus_counts():
    """Flat Z3 gauge fields modulo gauge transformations on a 2x2 torus."""
    vertices = range(4)

    def vertex(x, y):
        return 2 * (y % 2) + (x % 2)

    links = [(v, direction) for v in vertices for direction in (0, 1)]
    link_index = {link: i for i, link in enumerate(links)}

    def xplus(v):
        return vertex(v % 2 + 1, v // 2)

    def yplus(v):
        return vertex(v % 2, v // 2 + 1)

    def flat(field):
        for v in vertices:
            plaquette = (
                field[link_index[(v, 0)]]
                + field[link_index[(xplus(v), 1)]]
                - field[link_index[(yplus(v), 0)]]
                - field[link_index[(v, 1)]]
            ) % 3
            if plaquette:
                return False
        return True

    gauges = tuple(product(range(3), repeat=4))

    def gauge(field, transformation):
        output = [0] * 8
        for v in vertices:
            output[link_index[(v, 0)]] = (
                field[link_index[(v, 0)]]
                + transformation[v]
                - transformation[xplus(v)]
            ) % 3
            output[link_index[(v, 1)]] = (
                field[link_index[(v, 1)]]
                + transformation[v]
                - transformation[yplus(v)]
            ) % 3
        return tuple(output)

    flats = [field for field in product(range(3), repeat=8) if flat(field)]
    classes = {min(gauge(field, g) for g in gauges) for field in flats}
    return len(flats), len(classes)


def relative_entropy(q, p):
    total = 0.0
    for qi, pi in zip(q, p):
        if qi == 0:
            continue
        if pi == 0:
            return inf
        total += float(qi) * log(float(qi / pi))
    return total


class ContinuationInvariantBreakerTests(unittest.TestCase):
    def test_01_reachable_set_is_not_the_invariant(self):
        first = Machine(("A", "B"), ("a",), {
            ("A", "a"): (0, "B"),
            ("B", "a"): (0, "A"),
        })
        second = Machine(("A", "B"), ("a",), {
            ("A", "a"): (0, "B"),
            ("B", "a"): (1, "A"),
        })
        reachable_first = {trace(first, "A", ("a",) * n)[1] for n in range(3)}
        reachable_second = {trace(second, "A", ("a",) * n)[1] for n in range(3)}
        self.assertEqual(reachable_first, {"A", "B"})
        self.assertEqual(reachable_second, {"A", "B"})
        self.assertNotEqual(
            trace(first, "A", ("a", "a"))[0],
            trace(second, "A", ("a", "a"))[0],
        )

    def test_02_execution_behavior_need_not_be_developmental_congruence(self):
        # Same present execution behavior, but an update allowed to inspect a
        # hidden realization tag can send the two representatives to future
        # laws with distinct behavior.
        present = {"left": (0, 0, 0), "right": (0, 0, 0)}
        after_same_evidence = {"left": (0, 0, 0), "right": (1, 1, 1)}
        self.assertEqual(present["left"], present["right"])
        self.assertNotEqual(after_same_evidence["left"], after_same_evidence["right"])

    def test_03_developmental_update_can_fail_to_factor_through_old_quotient(self):
        # q(a)=q(b), but q2(U(a)) != q2(U(b)); therefore no Ubar can satisfy
        # q2 o U = Ubar o q.
        q = {"a": 0, "b": 0}
        update = {"a": "c", "b": "d"}
        q2 = {"c": 0, "d": 1}
        self.assertEqual(q["a"], q["b"])
        self.assertNotEqual(q2[update["a"]], q2[update["b"]])

    def test_04_state_law_split_compiles_to_fixed_extended_dynamics(self):
        # A visibly changing law index can be absorbed into an enlarged state.
        states = tuple(f"{x}{law}" for x in (0, 1) for law in (0, 1))
        steps = {}
        for x in (0, 1):
            for law in (0, 1):
                state = f"{x}{law}"
                for symbol in ("stay", "toggle"):
                    evidence = x ^ law
                    next_law = law ^ (symbol == "toggle")
                    next_x = evidence
                    steps[(state, symbol)] = (
                        evidence, f"{next_x}{int(next_law)}"
                    )
        fixed = Machine(states, ("stay", "toggle"), steps)

        def adaptive(x, law, word):
            output = []
            for symbol in word:
                evidence = x ^ law
                output.append(evidence)
                x = evidence
                if symbol == "toggle":
                    law ^= 1
            return tuple(output)

        checked = 0
        for x in (0, 1):
            for law in (0, 1):
                for word in words(("stay", "toggle"), 5):
                    checked += 1
                    self.assertEqual(
                        trace(fixed, f"{x}{law}", word)[0],
                        adaptive(x, law, word),
                    )
        self.assertEqual(checked, 252)

    def test_05_future_transition_behavior_refines_one_step_alias(self):
        machine = Machine(("a", "b", "c", "d"), ("e",), {
            ("a", "e"): (0, "c"),
            ("b", "e"): (0, "d"),
            ("c", "e"): (0, "c"),
            ("d", "e"): (1, "d"),
        })
        self.assertEqual(
            machine.step[("a", "e")][0],
            machine.step[("b", "e")][0],
        )
        self.assertNotEqual(
            trace(machine, "a", ("e", "e"))[0],
            trace(machine, "b", ("e", "e"))[0],
        )
        partition = mealy_partition(machine)
        self.assertFalse(any("a" in block and "b" in block for block in partition))

    def test_06_pure_msi_refinement_is_flat_and_idempotent(self):
        failures = 0
        idempotence_failures = 0
        pair_count = 0
        counts = {}
        for n in range(1, 6):
            partitions = all_partitions(n)
            observables = tuple(product((0, 1), repeat=n))
            counts[n] = (len(partitions), len(observables))
            for partition in partitions:
                for first in observables:
                    refined = refine_partition(partition, first)
                    if refine_partition(refined, first) != refined:
                        idempotence_failures += 1
                    for second in observables:
                        pair_count += 1
                        left = refine_partition(
                            refine_partition(partition, first), second
                        )
                        right = refine_partition(
                            refine_partition(partition, second), first
                        )
                        if left != right:
                            failures += 1
        print(
            "MSI_FLATNESS_COUNTS",
            counts,
            "pairs",
            pair_count,
            "commutation_failures",
            failures,
            "idempotence_failures",
            idempotence_failures,
        )
        self.assertEqual(failures, 0)
        self.assertEqual(idempotence_failures, 0)

    def test_07_current_arc_overlay_breaks_nonbackground_color_equivariance(self):
        # The current implementation defines overlay by numeric max. Swapping
        # ARC colors 1 and 2 while fixing background 0 is therefore not a
        # symmetry of this primitive.
        left = grid([[1, 0], [0, 2]])
        right = grid([[2, 0], [1, 0]])
        permutation = {0: 0, 1: 2, 2: 1}

        def permute(value):
            return tuple(
                tuple(permutation.get(cell, cell) for cell in row)
                for row in value
            )

        permute_after = permute(form(left, right, "overlay"))
        overlay_after = form(permute(left), permute(right), "overlay")
        print("ARC_COLOR_EQUIVARIANCE_COUNTEREXAMPLE", permute_after, overlay_after)
        self.assertNotEqual(permute_after, overlay_after)

    def test_08_symmetric_minimum_tie_breaker_is_not_equivariant(self):
        candidates = ("A", "B")
        swap = {"A": "B", "B": "A"}
        choose = lambda values: sorted(values)[0]
        choose_then_swap = swap[choose(candidates)]
        swap_then_choose = choose(tuple(swap[value] for value in candidates))
        self.assertNotEqual(choose_then_swap, swap_then_choose)

    def test_09_local_adequacy_does_not_imply_global_gluing(self):
        # Odd-cycle 2-coloring: each local edge inequality is satisfiable, but
        # all three constraints cannot be satisfied simultaneously.
        edges = ((0, 1), (1, 2), (2, 0))
        for i, j in edges:
            self.assertTrue(any(
                assignment[i] != assignment[j]
                for assignment in product((0, 1), repeat=3)
            ))
        global_solutions = [
            assignment
            for assignment in product((0, 1), repeat=3)
            if all(assignment[i] != assignment[j] for i, j in edges)
        ]
        self.assertEqual(global_solutions, [])

    def test_10_contradictory_constraints_require_infeasibility_not_guessing(self):
        adequate = [value for value in (0, 1) if value == 0 and value == 1]
        self.assertEqual(adequate, [])

    def test_11_complete_support_is_monotone_but_budgeted_search_need_not_be(self):
        smaller = ("good",)
        larger = ("bad", "good")
        solves = lambda candidate: candidate == "good"

        self.assertTrue(any(map(solves, smaller)))
        self.assertTrue(any(map(solves, larger)))

        # Fixed one-candidate budget plus changed enumeration order loses the
        # effective success even though the semantic language only grew.
        self.assertTrue(solves(smaller[0]))
        self.assertFalse(solves(larger[0]))

    def test_12_closed_context_loop_can_have_nontrivial_holonomy(self):
        fibre = 0
        for transport in (
            lambda value: value,
            lambda value: value,
            lambda value: 1 - value,
        ):
            fibre = transport(fibre)
        self.assertEqual(fibre, 1)

    def test_13_z3_torus_has_flat_local_fields_with_nine_global_classes(self):
        flat_count, class_count = z3_torus_counts()
        print("Z3_TORUS", "flat", flat_count, "gauge_classes", class_count)
        self.assertEqual(flat_count, 243)
        self.assertEqual(class_count, 9)

    def test_14_kl_reweighting_cannot_create_zero_support_at_finite_cost(self):
        prior = (Fraction(1), Fraction(0))
        unchanged = (Fraction(1), Fraction(0))
        expanded = (Fraction(1, 2), Fraction(1, 2))
        self.assertEqual(relative_entropy(unchanged, prior), 0.0)
        self.assertEqual(relative_entropy(expanded, prior), inf)

    def test_15_finite_residual_geometry_can_have_a_strict_separator(self):
        reachable = ((0, 0), (1, 0), (0, 1))
        target = (1, 1)
        separator = (1, 1)
        reachable_sup = max(
            separator[0] * x + separator[1] * y for x, y in reachable
        )
        target_value = separator[0] * target[0] + separator[1] * target[1]
        self.assertGreater(target_value, reachable_sup)


    def test_16_actual_kernel_has_order_dependent_development_on_chain_fixture(self):
        # This uses the real ProspectiveARCAdapter/Developer path, not a toy
        # transition. A is a generated prerequisite for B under the frozen
        # size/depth grammar. Processing A then B therefore changes the future
        # continuation available for C; processing B then A does not retroactively
        # revisit B.
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        second = lambda g: form(first(g), g, "concat-h")

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

        task_a = full_task([[1, 2, 3], [4, 5, 6]], first)
        task_b = full_task([[7, 1, 3], [2, 8, 4]], second)
        task_c = full_task([[9, 2, 5], [6, 3, 7]], second)

        def make_stream(named_tasks):
            rows = [
                {"task_id": name, "task_sha256": digest(task), "task": public(task)}
                for name, task in named_tasks
            ]
            body = {
                "schema": "prospective-route-neutral-stream/v1",
                "selection_nonce": "breaker-order",
                "tasks": rows,
                "route_labels_present": False,
            }
            return {**body, "stream_digest": digest(body)}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ab_path = root / "ab.sqlite"
            ba_path = root / "ba.sqlite"
            freeze_state(ab_path)
            freeze_state(ba_path)

            ab = develop_stream(make_stream((("a", task_a), ("b", task_b))), ab_path)
            ba = develop_stream(make_stream((("b", task_b), ("a", task_a))), ba_path)

            self.assertEqual(
                [row["predicted_route"] for row in ab["results"]],
                ["EXPANSION", "EXPANSION"],
            )
            self.assertEqual(
                [row["predicted_route"] for row in ba["results"]],
                ["UNKNOWN", "EXPANSION"],
            )

            ab_store = EvidenceStore(ab_path)
            ba_store = EvidenceStore(ba_path)
            ab_state = ab_store.state()
            ba_state = ba_store.state()
            ab_store.close()
            ba_store.close()
            self.assertNotEqual(digest(ab_state), digest(ba_state))

            adapter = ProspectiveARCAdapter()
            c_row = {"task_id": "c", "task_sha256": digest(task_c), "task": public(task_c)}
            c_obligation = Obligation(adapter.name, c_row, 0, "method")
            self.assertEqual(adapter.assess(ab_state, c_obligation).verdict, "verified")
            self.assertNotEqual(adapter.assess(ba_state, c_obligation).verdict, "verified")
            print(
                "ACTUAL_DEVELOPMENTAL_COMMUTATOR",
                "AB_routes", [row["predicted_route"] for row in ab["results"]],
                "BA_routes", [row["predicted_route"] for row in ba["results"]],
                "qC_after_AB", adapter.assess(ab_state, c_obligation).verdict,
                "qC_after_BA", adapter.assess(ba_state, c_obligation).verdict,
            )

    def test_17_exact_recursive_revocation_returns_chain_fixture_to_cold_behavior(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        second = lambda g: form(first(g), g, "concat-h")

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

        task_a = full_task([[1, 2, 3], [4, 5, 6]], first)
        task_b = full_task([[7, 1, 3], [2, 8, 4]], second)
        task_c = full_task([[9, 2, 5], [6, 3, 7]], second)
        rows = [
            {"task_id": name, "task_sha256": digest(task), "task": public(task)}
            for name, task in (("a", task_a), ("b", task_b))
        ]
        body = {
            "schema": "prospective-route-neutral-stream/v1",
            "selection_nonce": "breaker-revoke",
            "tasks": rows,
            "route_labels_present": False,
        }
        stream = {**body, "stream_digest": digest(body)}

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            baseline_store = EvidenceStore(path)
            baseline = baseline_store.state()
            baseline_events = len(baseline_store.events())
            baseline_store.close()

            decisions = develop_stream(stream, path)
            g1 = decisions["results"][0]["generated_admissions"][0]
            g2 = decisions["results"][1]["generated_admissions"][0]

            store = EvidenceStore(path)
            removed = store.revoke(g1, "breaker exact recursive closure")
            restored_active = store.state()
            history_is_longer = len(store.events()) > baseline_events
            store.close()

            self.assertIn(g1, removed)
            self.assertIn(g2, removed)
            self.assertEqual(restored_active, baseline)
            self.assertTrue(history_is_longer)

            adapter = ProspectiveARCAdapter()
            c_row = {"task_id": "c", "task_sha256": digest(task_c), "task": public(task_c)}
            c_obligation = Obligation(adapter.name, c_row, 0, "method")
            self.assertNotEqual(adapter.assess(restored_active, c_obligation).verdict, "verified")
            print(
                "REVOCATION_LOOP",
                "active_state_returns_to_baseline", True,
                "provenance_history_persists", history_is_longer,
                "qC_after_revoke", adapter.assess(restored_active, c_obligation).verdict,
            )

    def test_18_repeated_verified_encounter_is_active_state_idempotent(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")

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

        task = full_task([[1, 2, 3], [4, 5, 6]], first)
        row = {"task_id": "a", "task_sha256": digest(task), "task": public(task)}
        body = {
            "schema": "prospective-route-neutral-stream/v1",
            "selection_nonce": "breaker-idempotence",
            "tasks": [row],
            "route_labels_present": False,
        }
        stream = {**body, "stream_digest": digest(body)}

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            decisions = develop_stream(stream, path)
            self.assertEqual(decisions["results"][0]["predicted_route"], "EXPANSION")

            store = EvidenceStore(path)
            before = store.state()
            result = Developer(store, ProspectiveARCAdapter()).run(
                Obligation(ProspectiveARCAdapter.name, row, 0, "method")
            )
            after = store.state()
            store.close()

            self.assertEqual(result.verdict, "verified")
            self.assertEqual(result.retained, ())
            self.assertEqual(before, after)
            print("REPEATED_ENCOUNTER_IDEMPOTENT", digest(before), digest(after))


    def test_19_semantic_duplicate_changes_actual_generator_version_space(self):
        # A second retained capability with identical executable semantics but a
        # different identifier should be representational redundancy if IDs are
        # gauge-like. The current generator counts the two call ASTs separately.
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()

            adapter = ProspectiveARCAdapter()
            task = full_task([[1, 2, 3], [4, 5, 6]], first)
            baseline = adapter.generation_analysis(state, task)
            self.assertEqual(baseline["minimum_survivor_count"], 1)

            flip_id = next(
                rid for rid, rec in state["capabilities"].items()
                if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "flip-h"}
            )
            duplicated = deepcopy(state)
            duplicate_id = "gauge-copy-" + flip_id
            duplicated["capabilities"][duplicate_id] = deepcopy(
                duplicated["capabilities"][flip_id]
            )

            changed = adapter.generation_analysis(duplicated, task)
            self.assertEqual(changed["minimum_size"], baseline["minimum_size"])
            self.assertGreater(changed["minimum_survivor_count"], 1)

            print(
                "SEMANTIC_DUPLICATE_BREAKS_SYNTACTIC_VERSION_SPACE",
                "baseline_minima", baseline["minimum_survivor_count"],
                "duplicate_minima", changed["minimum_survivor_count"],
                "baseline_candidates", baseline["candidate_count"],
                "duplicate_candidates", changed["candidate_count"],
            )

    def test_20_behavioral_quotient_collapses_duplicate_generator_minima(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()

            adapter = ProspectiveARCAdapter()
            flip_id = next(
                rid for rid, rec in state["capabilities"].items()
                if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "flip-h"}
            )
            duplicated = deepcopy(state)
            duplicated["capabilities"]["gauge-copy-" + flip_id] = deepcopy(
                duplicated["capabilities"][flip_id]
            )

            task = full_task([[1, 2, 3], [4, 5, 6]], first)
            analysis = adapter.generation_analysis(duplicated, task)
            self.assertGreater(analysis["minimum_survivor_count"], 1)

            probes = [
                [[0, 1], [2, 3]],
                [[4, 0, 5], [6, 7, 8]],
                [[9, 8], [7, 6], [5, 4]],
            ]
            signatures = set()
            for ast in analysis["minimum_survivors"]:
                signature = tuple(
                    adapter.execute_ast(duplicated, ast, value) for value in probes
                )
                signatures.add(signature)

            self.assertEqual(len(signatures), 1)
            print(
                "BEHAVIORAL_QUOTIENT_RECOVERS_ONE_MINIMUM_CLASS",
                "syntactic_minima", analysis["minimum_survivor_count"],
                "behavioral_classes", len(signatures),
            )

    def test_21_capability_map_reordering_is_harmless_in_actual_generator(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()

            reordered = deepcopy(state)
            reordered["capabilities"] = dict(
                reversed(list(reordered["capabilities"].items()))
            )

            task = full_task([[1, 2, 3], [4, 5, 6]], first)
            adapter = ProspectiveARCAdapter()
            left = adapter.generation_analysis(state, task)
            right = adapter.generation_analysis(reordered, task)
            self.assertEqual(left, right)
            print("CAPABILITY_MAP_ORDER_INVARIANT", left["version_space_id"])

    def test_22_overlay_operand_canonicalization_is_behavior_preserving(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()

            flip_id = next(
                rid for rid, rec in state["capabilities"].items()
                if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "flip-h"}
            )
            left = {"op": "input"}
            right = {"op": "call", "callee": flip_id, "arg": {"op": "input"}}
            raw_a = {"op": "overlay", "left": left, "right": right}
            raw_b = {"op": "overlay", "left": right, "right": left}

            adapter = ProspectiveARCAdapter()
            probe = [[1, 0, 2], [3, 4, 0]]
            self.assertEqual(
                adapter.execute_ast(state, raw_a, probe),
                adapter.execute_ast(state, raw_b, probe),
            )

            keys = {ast_key(ast) for ast in generated_asts(state)}
            present = int(ast_key(raw_a) in keys) + int(ast_key(raw_b) in keys)
            self.assertEqual(present, 1)
            canonical = raw_a if ast_key(left) <= ast_key(right) else raw_b
            self.assertIn(ast_key(canonical), keys)
            print(
                "OVERLAY_GAUGE_FIXING",
                "raw_equivalent_representatives", 2,
                "generated_representatives", present,
            )

    def test_23_same_current_task_behavior_can_hide_future_developmental_difference(self):
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")
        second = lambda g: form(first(g), g, "concat-h")

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

        task_a = full_task([[1, 2, 3], [4, 5, 6]], first)
        task_b = full_task([[7, 1, 3], [2, 8, 4]], second)
        identity_task = full_task([[1, 2], [3, 4]], lambda g: g)

        def row(name, task):
            return {"task_id": name, "task_sha256": digest(task), "task": public(task)}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cold_path = root / "cold.sqlite"
            warm_path = root / "warm.sqlite"
            freeze_state(cold_path)
            freeze_state(warm_path)

            # Develop only A in the warm history.
            a_row = row("a", task_a)
            body = {
                "schema": "prospective-route-neutral-stream/v1",
                "selection_nonce": "gauge-minimality",
                "tasks": [a_row],
                "route_labels_present": False,
            }
            develop_stream({**body, "stream_digest": digest(body)}, warm_path)

            cold_store = EvidenceStore(cold_path)
            warm_store = EvidenceStore(warm_path)
            cold_state = cold_store.state()
            warm_state = warm_store.state()

            adapter = ProspectiveARCAdapter()
            identity_public = public(identity_task)
            cold_solvers = adapter.solving_records(cold_state, identity_public)
            warm_solvers = adapter.solving_records(warm_state, identity_public)
            self.assertTrue(cold_solvers)
            self.assertTrue(warm_solvers)
            cold_output = adapter.execute(
                cold_state, cold_solvers[0], identity_task["test"][0]["input"], []
            )
            warm_output = adapter.execute(
                warm_state, warm_solvers[0], identity_task["test"][0]["input"], []
            )
            self.assertEqual(cold_output, warm_output)

            b_row = row("b", task_b)
            cold_result = Developer(cold_store, adapter).run(
                Obligation(adapter.name, b_row, 1, "method")
            )
            warm_result = Developer(warm_store, adapter).run(
                Obligation(adapter.name, b_row, 1, "method")
            )
            cold_store.close()
            warm_store.close()

            self.assertNotEqual(cold_result.verdict, "verified")
            self.assertEqual(warm_result.verdict, "verified")
            self.assertTrue(warm_result.retained)
            print(
                "CURRENT_BEHAVIOR_EQUAL_FUTURE_DEVELOPMENT_DIFFERS",
                "identity_output_equal", True,
                "cold_B", cold_result.verdict,
                "warm_B", warm_result.verdict,
            )


    def test_24_bounded_behavior_set_is_unchanged_by_semantic_duplicate(self):
        # Stronger full-abstraction breaker: duplicate syntax changes candidate
        # multiplicity but not the extensional behavior set of the bounded
        # generator on an exhaustive 2x2 binary probe domain.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()

            flip_id = next(
                rid for rid, rec in state["capabilities"].items()
                if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "flip-h"}
            )
            duplicated = deepcopy(state)
            duplicated["capabilities"]["gauge-copy-" + flip_id] = deepcopy(
                duplicated["capabilities"][flip_id]
            )

            adapter = ProspectiveARCAdapter()
            probes = [
                [[a, b], [c, d]]
                for a, b, c, d in product((0, 1), repeat=4)
            ]

            def behavior_set(local_state):
                signatures = set()
                for ast in generated_asts(local_state):
                    signatures.add(tuple(
                        adapter.execute_ast(local_state, ast, probe)
                        for probe in probes
                    ))
                return signatures

            baseline_behaviors = behavior_set(state)
            duplicate_behaviors = behavior_set(duplicated)
            self.assertEqual(baseline_behaviors, duplicate_behaviors)
            self.assertNotEqual(
                len(generated_asts(state)),
                len(generated_asts(duplicated)),
            )
            print(
                "FULL_ABSTRACTION_PRECONDITION",
                "baseline_syntax", len(generated_asts(state)),
                "duplicate_syntax", len(generated_asts(duplicated)),
                "behavior_classes", len(baseline_behaviors),
                "behavior_sets_equal", True,
            )

    def test_25_controller_is_not_fully_abstract_for_bounded_behavior(self):
        # Same bounded extensional behavior set, different controller outcome:
        # unique minimum becomes an unresolved syntactic tie. This pinpoints
        # the representation dependence in selection/version-space accounting,
        # not in the operational meaning of the generated programs.
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()

            flip_id = next(
                rid for rid, rec in state["capabilities"].items()
                if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "flip-h"}
            )
            duplicated = deepcopy(state)
            duplicated["capabilities"]["gauge-copy-" + flip_id] = deepcopy(
                duplicated["capabilities"][flip_id]
            )

            adapter = ProspectiveARCAdapter()
            task = full_task([[1, 2, 3], [4, 5, 6]], first)
            baseline = adapter.generation_analysis(state, task)
            changed = adapter.generation_analysis(duplicated, task)

            self.assertEqual(baseline["minimum_survivor_count"], 1)
            self.assertGreater(changed["minimum_survivor_count"], 1)

            probes = [
                [[a, b], [c, d]]
                for a, b, c, d in product((0, 1), repeat=4)
            ]
            baseline_behaviors = {
                tuple(adapter.execute_ast(state, ast, probe) for probe in probes)
                for ast in generated_asts(state)
            }
            duplicate_behaviors = {
                tuple(adapter.execute_ast(duplicated, ast, probe) for probe in probes)
                for ast in generated_asts(duplicated)
            }
            self.assertEqual(baseline_behaviors, duplicate_behaviors)
            print(
                "CONTROLLER_FULL_ABSTRACTION_FAILURE",
                "behavior_sets_equal", True,
                "baseline_minima", baseline["minimum_survivor_count"],
                "duplicate_minima", changed["minimum_survivor_count"],
            )

    def test_26_backward_revocation_probe_detects_causal_history(self):
        # History-preserving semantics is stricter than present output behavior:
        # after learning A, an identity task behaves exactly as before, yet the
        # learned occurrence can be reversed; in the cold state that backward
        # move does not exist.
        first = lambda g: form(g, tuple(tuple(reversed(row)) for row in g), "concat-h")

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

        task_a = full_task([[1, 2, 3], [4, 5, 6]], first)
        identity_task = full_task([[1, 2], [3, 4]], lambda g: g)
        row_a = {"task_id": "a", "task_sha256": digest(task_a), "task": public(task_a)}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cold_path = root / "cold.sqlite"
            warm_path = root / "warm.sqlite"
            freeze_state(cold_path)
            freeze_state(warm_path)

            body = {
                "schema": "prospective-route-neutral-stream/v1",
                "selection_nonce": "history-probe",
                "tasks": [row_a],
                "route_labels_present": False,
            }
            decisions = develop_stream(
                {**body, "stream_digest": digest(body)}, warm_path
            )
            g1 = decisions["results"][0]["generated_admissions"][0]

            adapter = ProspectiveARCAdapter()
            cold_store = EvidenceStore(cold_path)
            warm_store = EvidenceStore(warm_path)
            cold_state = cold_store.state()
            warm_state = warm_store.state()

            identity_public = public(identity_task)
            cold_id = adapter.solving_records(cold_state, identity_public)[0]
            warm_id = adapter.solving_records(warm_state, identity_public)[0]
            cold_out = adapter.execute(
                cold_state, cold_id, identity_task["test"][0]["input"], []
            )
            warm_out = adapter.execute(
                warm_state, warm_id, identity_task["test"][0]["input"], []
            )
            self.assertEqual(cold_out, warm_out)

            with self.assertRaises(KeyError):
                cold_store.revoke(g1, "backward probe cold")
            removed = warm_store.revoke(g1, "backward probe warm")
            self.assertIn(g1, removed)
            cold_store.close()
            warm_store.close()
            print(
                "HISTORY_PRESERVING_SEPARATOR",
                "present_output_equal", True,
                "cold_backward_move", False,
                "warm_backward_move", True,
            )


    def test_27_actual_independent_development_square_commutes_behaviorally(self):
        # Two generated capabilities with disjoint generated ancestry should
        # commute operationally even though their admission certificates are
        # produced in different histories.
        horizontal = lambda g: form(
            g, tuple(tuple(reversed(row)) for row in g), "concat-h"
        )
        vertical = lambda g: form(g, tuple(reversed(g)), "concat-v")

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        def public(task):
            return {
                "train": task["train"],
                "test": [{"input": x["input"]} for x in task["test"]],
            }

        tasks = {
            "h": full_task([[1, 2, 3], [4, 5, 6]], horizontal),
            "v": full_task([[7, 1, 3], [2, 8, 4]], vertical),
        }

        def run_order(root, order):
            path = root / ("".join(order) + ".sqlite")
            freeze_state(path)
            rows = [
                {"task_id": name, "task_sha256": digest(tasks[name]), "task": public(tasks[name])}
                for name in order
            ]
            body = {
                "schema": "prospective-route-neutral-stream/v1",
                "selection_nonce": "independence-square",
                "tasks": rows,
                "route_labels_present": False,
            }
            decisions = develop_stream({**body, "stream_digest": digest(body)}, path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()
            return decisions, state

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hv, state_hv = run_order(root, ("h", "v"))
            vh, state_vh = run_order(root, ("v", "h"))
            self.assertEqual(
                [x["predicted_route"] for x in hv["results"]],
                ["EXPANSION", "EXPANSION"],
            )
            self.assertEqual(
                [x["predicted_route"] for x in vh["results"]],
                ["EXPANSION", "EXPANSION"],
            )
            self.assertEqual(
                set(state_hv["capabilities"]),
                set(state_vh["capabilities"]),
            )
            adapter = ProspectiveARCAdapter()
            for name, task in tasks.items():
                self.assertTrue(adapter.solving_records(state_hv, public(task)))
                self.assertTrue(adapter.solving_records(state_vh, public(task)))
            print(
                "ACTUAL_INDEPENDENCE_SQUARE",
                "HV_routes", [x["predicted_route"] for x in hv["results"]],
                "VH_routes", [x["predicted_route"] for x in vh["results"]],
                "operational_capability_ids_equal", True,
            )

    def test_28_three_independent_developments_form_operational_cube(self):
        horizontal_flip = lambda g: form(
            g, tuple(tuple(reversed(row)) for row in g), "concat-h"
        )
        vertical_flip = lambda g: form(g, tuple(reversed(g)), "concat-v")
        rotate_180 = lambda g: tuple(
            tuple(reversed(row)) for row in reversed(g)
        )
        horizontal_rot = lambda g: form(g, rotate_180(g), "concat-h")

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        def public(task):
            return {
                "train": task["train"],
                "test": [{"input": x["input"]} for x in task["test"]],
            }

        tasks = {
            "a": full_task([[1, 2, 3], [4, 5, 6]], horizontal_flip),
            "b": full_task([[7, 1, 3], [2, 8, 4]], vertical_flip),
            "c": full_task([[9, 2, 5], [6, 3, 7]], horizontal_rot),
        }

        endpoints = []
        routes = {}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for order in permutations(("a", "b", "c")):
                path = root / ("".join(order) + ".sqlite")
                freeze_state(path)
                rows = [
                    {"task_id": name, "task_sha256": digest(tasks[name]), "task": public(tasks[name])}
                    for name in order
                ]
                body = {
                    "schema": "prospective-route-neutral-stream/v1",
                    "selection_nonce": "independence-cube",
                    "tasks": rows,
                    "route_labels_present": False,
                }
                decisions = develop_stream({**body, "stream_digest": digest(body)}, path)
                routes["".join(order)] = [x["predicted_route"] for x in decisions["results"]]
                store = EvidenceStore(path)
                state = store.state()
                store.close()
                endpoints.append(set(state["capabilities"]))

            self.assertTrue(all(value == ["EXPANSION"] * 3 for value in routes.values()))
            self.assertTrue(all(endpoint == endpoints[0] for endpoint in endpoints[1:]))
            print(
                "ACTUAL_OPERATIONAL_3_CUBE",
                "permutations", len(routes),
                "all_routes_expansion", True,
                "all_operational_endpoints_equal", True,
            )

    def test_29_behavioral_class_quotient_repairs_duplicate_without_hiding_real_ambiguity(self):
        # Prototype only: quotient minimum syntax by extensional signatures over
        # an exhaustive small probe domain. A semantic duplicate should collapse;
        # the known genuinely ambiguous training fixture should not.
        first = lambda g: form(
            g, tuple(tuple(reversed(row)) for row in g), "concat-h"
        )

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        probes = [
            [[a, b], [c, d]]
            for a, b, c, d in product((0, 1), repeat=4)
        ]

        def quotient_count(adapter, state, survivors):
            signatures = {
                tuple(adapter.execute_ast(state, ast, probe) for probe in probes)
                for ast in survivors
            }
            return len(signatures)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            state = store.state()
            store.close()
            adapter = ProspectiveARCAdapter()

            flip_id = next(
                rid for rid, rec in state["capabilities"].items()
                if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "flip-h"}
            )
            duplicated = deepcopy(state)
            duplicated["capabilities"]["gauge-copy-" + flip_id] = deepcopy(
                duplicated["capabilities"][flip_id]
            )
            duplicate_task = full_task([[1, 2, 3], [4, 5, 6]], first)
            duplicate_analysis = adapter.generation_analysis(duplicated, duplicate_task)
            self.assertGreater(duplicate_analysis["minimum_survivor_count"], 1)
            duplicate_classes = quotient_count(
                adapter, duplicated, duplicate_analysis["minimum_survivors"]
            )
            self.assertEqual(duplicate_classes, 1)

            ambiguous_task = full_task(
                [[0, 0], [0, 1]],
                lambda g: form(
                    g,
                    tuple(zip(*g[::-1])),
                    "concat-h",
                ),
            )
            ambiguous_analysis = adapter.generation_analysis(state, ambiguous_task)
            self.assertGreater(ambiguous_analysis["minimum_survivor_count"], 1)
            ambiguity_classes = quotient_count(
                adapter, state, ambiguous_analysis["minimum_survivors"]
            )
            self.assertGreater(ambiguity_classes, 1)
            print(
                "BEHAVIORAL_CLASS_VERSION_SPACE_SEPARATOR",
                "duplicate_syntax", duplicate_analysis["minimum_survivor_count"],
                "duplicate_classes", duplicate_classes,
                "real_ambiguity_syntax", ambiguous_analysis["minimum_survivor_count"],
                "real_ambiguity_classes", ambiguity_classes,
            )

    def test_30_actual_admission_is_conservative_on_old_operational_semantics(self):
        # A real generated admission extends the active language. Verify
        # exhaustively over 2x2 binary grids that all pre-existing D4
        # capabilities preserve their exact semantics after the extension.
        first = lambda g: form(
            g, tuple(tuple(reversed(row)) for row in g), "concat-h"
        )

        def full_task(value, function):
            output = [list(row) for row in function(grid(value))]
            return {
                "train": [{"input": value, "output": output}],
                "test": [{"input": value, "output": output}],
            }

        def public(task):
            return {
                "train": task["train"],
                "test": [{"input": x["input"]} for x in task["test"]],
            }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite"
            freeze_state(path)
            store = EvidenceStore(path)
            before = store.state()
            old_ids = tuple(sorted(before["capabilities"]))
            store.close()

            task = full_task([[1, 2, 3], [4, 5, 6]], first)
            row = {"task_id": "a", "task_sha256": digest(task), "task": public(task)}
            body = {
                "schema": "prospective-route-neutral-stream/v1",
                "selection_nonce": "conservative-extension",
                "tasks": [row],
                "route_labels_present": False,
            }
            decisions = develop_stream({**body, "stream_digest": digest(body)}, path)
            self.assertEqual(decisions["results"][0]["predicted_route"], "EXPANSION")

            store = EvidenceStore(path)
            after = store.state()
            store.close()
            adapter = ProspectiveARCAdapter()
            probes = [
                [[a, b], [c, d]]
                for a, b, c, d in product((0, 1), repeat=4)
            ]
            for rid in old_ids:
                for probe in probes:
                    self.assertEqual(
                        adapter.execute(before, rid, probe, []),
                        adapter.execute(after, rid, probe, []),
                    )
            self.assertGreater(len(after["capabilities"]), len(before["capabilities"]))
            print(
                "ACTUAL_CONSERVATIVE_EXTENSION",
                "old_capabilities", len(old_ids),
                "new_capabilities", len(after["capabilities"]) - len(old_ids),
                "old_semantics_preserved_on_probes", len(old_ids) * len(probes),
            )

    def test_31_automatic_minimal_developmental_separator_search(self):
        # Search the warm generated language for the smallest two-example task
        # that is generatively available after G1 but absent in the cold
        # language. This is a finite analogue of finding a distinguishing
        # experiment/formula rather than hand-naming the next task.
        first = lambda g: form(
            g, tuple(tuple(reversed(row)) for row in g), "concat-h"
        )

        def full_task(values, function):
            train = []
            for value in values:
                output = function(grid(value))
                train.append({"input": value, "output": [list(row) for row in output]})
            return {"train": train, "test": [train[0]]}

        def public(task):
            return {
                "train": task["train"],
                "test": [{"input": x["input"]} for x in task["test"]],
            }

        task_a = full_task(
            (
                [[1, 2, 3], [4, 5, 6]],
                [[7, 8, 9], [1, 3, 5]],
            ),
            first,
        )
        row_a = {"task_id": "a", "task_sha256": digest(task_a), "task": public(task_a)}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cold_path = root / "cold.sqlite"
            warm_path = root / "warm.sqlite"
            freeze_state(cold_path)
            freeze_state(warm_path)
            body = {
                "schema": "prospective-route-neutral-stream/v1",
                "selection_nonce": "automatic-separator",
                "tasks": [row_a],
                "route_labels_present": False,
            }
            decisions = develop_stream({**body, "stream_digest": digest(body)}, warm_path)
            g1 = decisions["results"][0]["generated_admissions"][0]

            cold_store = EvidenceStore(cold_path)
            warm_store = EvidenceStore(warm_path)
            cold = cold_store.state()
            warm = warm_store.state()
            cold_store.close()
            warm_store.close()
            adapter = ProspectiveARCAdapter()

            probe_values = (
                [[9, 2, 5], [6, 3, 7]],
                [[4, 1, 8], [2, 9, 3]],
            )
            found = None
            for ast in generated_asts(warm):
                if g1 not in str(ast):
                    continue
                outputs = [
                    adapter.execute_ast(warm, ast, value)
                    for value in probe_values
                ]
                if any(output is None for output in outputs):
                    continue
                task = {
                    "train": [
                        {"input": value, "output": [list(row) for row in output]}
                        for value, output in zip(probe_values, outputs)
                    ],
                    "test": [{"input": probe_values[0], "output": [list(row) for row in outputs[0]]}],
                }
                warm_analysis = adapter.generation_analysis(warm, task)
                cold_analysis = adapter.generation_analysis(cold, task)
                if (
                    warm_analysis["minimum_survivor_count"] == 1
                    and cold_analysis["minimum_size"] is None
                ):
                    found = (
                        ast,
                        warm_analysis["minimum_size"],
                        warm_analysis["candidate_count"],
                        cold_analysis["candidate_count"],
                    )
                    break

            self.assertIsNotNone(found)
            ast, size, warm_count, cold_count = found
            print(
                "AUTOMATIC_DEVELOPMENTAL_SEPARATOR",
                "minimum_size", size,
                "warm_candidates", warm_count,
                "cold_candidates", cold_count,
                "ast", ast_key(ast),
            )

    def test_32_breaker_summary(self):
        print("CONTINUATION_INVARIANT_BREAKERS_V1_COMPLETE")
        print(
            "BREAKS: execution-behavior equivalence alone is not a "
            "developmental congruence unless update factors through it"
        )
        print(
            "BREAKS: state-versus-law decomposition is not invariant; "
            "adaptive law can be absorbed into extended state"
        )
        print(
            "BREAKS: arbitrary non-background color relabeling is not a "
            "symmetry of current numeric-max ARC overlay"
        )
        print(
            "SURVIVES: pure MSI kernel-intersection refinement is finite-flat "
            "and idempotent"
        )
        print(
            "SURVIVES CONDITIONALLY: holonomy, gauge and KL/support language "
            "are mathematically valid only when their extra structure exists"
        )
        print(
            "BREAKS IN REAL GENERATOR: semantically duplicate capability IDs can turn one minimum into a syntactic version-space tie"
        )
        print(
            "SURVIVES IN REAL GENERATOR: capability map ordering is irrelevant and commutative overlay admits canonical representative fixing"
        )
        print(
            "NO CURRENT FP ANALOGUE ESTABLISHED: duplicate orbit multiplicity is not compensated; it changes the generator version space"
        )
        print(
            "NO CURRENT BRST ANALOGUE ESTABLISHED: no nilpotent cohomological operator was defined or tested by the implementation"
        )
        print(
            "BREAKS IN REAL CONTROLLER: equal bounded generated behavior sets can yield different syntactic version-space outcomes"
        )
        print(
            "SURVIVES: backward revocation distinguishes causal developmental history even when present task output agrees"
        )
        print(
            "TESTED NEXT: independent real developments commute operationally; three independent developments form a coherent finite cube if the fixture passes"
        )
        print(
            "TESTED NEXT: behavioral-class quotient can remove pure duplicate syntax while retaining genuine ambiguity if the separator passes"
        )
        print(
            "TESTED NEXT: real generated admission is an operational conservative extension on preserved capabilities if the preservation census passes"
        )
        print(
            "STRONGER CANDIDATE: a fully abstract, history-sensitive equivalence of the full encounter-plus-development process"
        )


if __name__ == "__main__":
    unittest.main()
