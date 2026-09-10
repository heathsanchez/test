"""Breaker tests for the continuation-law / invariance hypothesis.

These tests are intentionally adversarial. They distinguish what follows from
finite mathematics from what requires extra structure. They do not alter the
developmental kernel and they do not promote gauge/physics language unless the
corresponding structure is actually present.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import inf, log
import unittest

from open_development.arc_discrimination import form, grid


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

    def test_16_breaker_summary(self):
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
            "STRONGER CANDIDATE: behavioral equivalence of the full "
            "encounter-plus-development transition system"
        )


if __name__ == "__main__":
    unittest.main()
