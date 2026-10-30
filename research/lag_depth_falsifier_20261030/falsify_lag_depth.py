#!/usr/bin/env python3
"""Finite countermodel for the NP-verifier claim in Lag–Depth Grammar.

No stochastic simulation, oracle, nonlocal transition, or third-party package.
Every observation is an input bit read by an ordinary linear-time verifier.
"""

import argparse
import hashlib
import json
import unittest


def witness_containing_all_words(n: int) -> str:
    """Concatenate all n-bit words as a legitimate polynomial-size witness.

    Its length is n * 2**n; we choose an input x of that same length.
    The verifier runs in time O(|x|), not O(2**|x|).
    """
    assert n >= 2
    return "".join(f"{i:0{n}b}" for i in range(1 << n))


def linear_time_verifier(x: str, witness: str) -> tuple[bool, str, int]:
    """NP verifier: check equal lengths and even witness parity, reading left to right.

    The observable local trace is just each witnessed input symbol. It uses one
    streaming pass with two parity states (plus finite-length input accounting).
    """
    if len(x) != len(witness):
        return False, "", 0
    parity = 0
    trace = []
    steps = 0
    for bit in witness:
        if bit not in "01":
            return False, "".join(trace), steps
        parity ^= int(bit)
        trace.append(bit)
        steps += 1
    return parity == 0, "".join(trace), steps


def sat_verifier_for_tautologies(witness: str) -> tuple[bool, str, int]:
    """A standard SAT witness checker on CNF ∧_i (v_i ∨ ¬v_i).

    This is a concrete SAT instance of N tautological clauses; the witness has
    N freely chosen Boolean variables. Reading witness bits produces the local
    trace; checking one clause per variable takes another N steps. No oracle.
    """
    trace = []
    steps = 0
    for value in witness:
        if value not in "01":
            return False, "".join(trace), steps
        trace.append(value)
        steps += 1
        assignment = value == "1"
        clause_true = assignment or (not assignment)
        steps += 1
        if not clause_true:
            return False, "".join(trace), steps
    return True, "".join(trace), steps


def grammar_support(trace: str, m: int) -> int:
    assert m >= 0
    length = m + 1
    return len({trace[i : i + length] for i in range(max(0, len(trace) - m))})


def sample(n: int) -> dict:
    witness = witness_containing_all_words(n)
    x = "0" * len(witness)
    accepted, trace, steps = linear_time_verifier(x, witness)
    counts = {str(m): grammar_support(trace, m) for m in range(n)}
    return {
        "word_length": n,
        "input_length": len(x),
        "verifier_steps": steps,
        "accepted": accepted,
        "witness_sha256": hashlib.sha256(witness.encode()).hexdigest(),
        "grammar_support_by_depth": counts,
        "full_depth_support": counts[str(n - 1)],
        "expected_full_support": 1 << n,
    }


class FiniteLagDepthCounterexample(unittest.TestCase):
    def test_linear_verifier_accepts_and_reads_at_most_input_length(self):
        for n in range(2, 11):
            s = sample(n)
            self.assertTrue(s["accepted"])
            self.assertEqual(s["verifier_steps"], s["input_length"])
            self.assertEqual(s["input_length"], n * (1 << n))

    def test_all_words_present_at_every_depth_up_to_n(self):
        for n in range(2, 11):
            s = sample(n)
            for m in range(n):
                self.assertEqual(s["grammar_support_by_depth"][str(m)], 1 << (m + 1))

    def test_finite_traces_censor_every_process(self):
        for trace in ["", "0", "0011011", "0101" * 7]:
            length = len(trace)
            for m in range(length, length + 3):
                self.assertEqual(grammar_support(trace, m), 0)
            for m in range(length):
                self.assertLessEqual(grammar_support(trace, m), min(1 << (m + 1), length - m))

    def test_standard_sat_verifier_also_has_full_exponential_support(self):
        for n in range(2, 11):
            witness = witness_containing_all_words(n)
            accepted, trace, steps = sat_verifier_for_tautologies(witness)
            self.assertTrue(accepted)
            self.assertEqual(steps, 2 * len(witness))
            for m in range(n):
                self.assertEqual(grammar_support(trace, m), 1 << (m + 1))

    def test_original_uniform_bound_cannot_hold(self):
        # No input-independent depth cutoff bounds all such polynomial-time
        # verifier traces: n can exceed any proposed fixed cutoff.
        for cutoff in range(2, 11):
            s = sample(cutoff)
            self.assertEqual(s["full_depth_support"], 1 << cutoff)
            self.assertGreater(s["full_depth_support"], 0)


def negative_control() -> None:
    """Deliberately assert the paper's nontrivial uniform-vanishing claim.

    Must raise AssertionError. If it passes, the control is broken.
    """
    n = 7
    m = n - 1
    witness = witness_containing_all_words(n)
    assert grammar_support(witness, m) == 0, "original universal-bound claim falsified"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    parser.add_argument("--json", action="store_true")
    options, remaining = parser.parse_known_args()
    if options.negative_control:
        negative_control()
    elif options.json:
        print(json.dumps([sample(n) for n in range(2, 11)], indent=2, sort_keys=True))
    else:
        unittest.main(argv=[__file__, *remaining])
