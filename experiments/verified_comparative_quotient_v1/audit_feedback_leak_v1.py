"""Post-hoc causal control for the original, source-pinned August 2026 experiment.

No model call, hidden data fetch, or protected confirmation namespace is used.
Only function definitions from the immutable original source are evaluated.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import random


ORIGINAL_BLOB = "7a9d45b26ee559130ceefeca2cb63e6c9a173e16"
SOURCE = Path(__file__).with_name("run_openai.py")
if not SOURCE.exists():
    # Scratch replay uses a byte-identical, explicitly named source copy.
    SOURCE = Path(__file__).with_name("original_run_openai.py")


def load_original(*, mutate_verifier=False):
    raw = SOURCE.read_bytes()
    actual_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw
    ).hexdigest()
    assert actual_blob == ORIGINAL_BLOB, (actual_blob, ORIGINAL_BLOB)
    source = raw.decode("utf-8")
    if mutate_verifier:
        before = "    r=rivals[0]\n"
        assert source.count(before) == 1
        source = source.replace(before, "    r=top\n")
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    # The original script's module-level code performs paid API requests.
    # Compile only original definitions, then inject the exact frozen constants.
    scope = {
        "Counter": Counter, "defaultdict": defaultdict, "product": product,
        "json": json, "math": math, "random": random,
        "PREFIXES": "ABCD", "SUFFIXES": "XYZ",
        "FAMILIES": [2, 3, 5], "TASKS_PER_FAMILY": 16,
        "RNG": random.Random(2026082510),
    }
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), "exec"), scope)
    return scope


def independent_expected_entropy(survivors, q, target, modulus):
    """Independent two-column contingency count, without original score helper."""
    cells = Counter(
        ((bases[q[0]] + offsets[q[1]]) % modulus,
         (bases[target[0]] + offsets[target[1]]) % modulus)
        for bases, offsets in survivors
    )
    query_counts = Counter()
    for (answer, _), count in cells.items():
        query_counts[answer] += count
    total = len(survivors)
    result = 0.0
    for (answer, _), count in cells.items():
        p_joint = count / total
        p_cond = count / query_counts[answer]
        result -= p_joint * math.log2(p_cond)
    return result


def audit(mutated=False):
    f = load_original(mutate_verifier=mutated)
    tasks = f["build_tasks"]()
    assert len(tasks) == 48
    assert Counter(t["m"] for t in tasks) == {2: 16, 3: 16, 5: 16}
    baseline_correct = 0
    oracle_only_correct = 0
    public_only_correct = 0
    emitted = 0
    verified_rival_emissions = 0
    all_feedback_events = 0
    all_responses = 0
    zero_entropy_tied_top = 0
    for t in tasks:
        all_worlds = f["all_hypotheses"](t["m"])
        possible = f["survivors"](all_worlds, t["obs"], t["m"])
        assert len(possible) >= 4
        entropies = {
            q: independent_expected_entropy(possible, q, t["target"], t["m"])
            for q in t["queries"]
        }
        for q in t["queries"]:
            assert abs(entropies[q] - t["expected_entropy"][q]) < 1e-10
        best = min(t["queries"], key=lambda q: (entropies[q], q))
        assert best == t["optimal"] and abs(entropies[best]) < 1e-10
        first = t["queries"][0]  # fixed, public-input-only zero-reasoning policy
        baseline_correct += f["downstream"](t, possible, first)["correct"]
        # The original verifier's EXACT behavior is evaluated for all four
        # candidate tops, not inferred from source-text matching.
        for q in t["queries"]:
            proposal = {"ranking": [q] + [x for x in t["queries"] if x != q]}
            fb = f["better_feedback"](proposal, t)
            all_responses += 1
            if entropies[q] > entropies[best] + 1e-10:
                assert fb is not None, (t["id"], q)
                all_feedback_events += 1
                if fb["strictly_better_rival"] == best:
                    verified_rival_emissions += 1
                else:
                    raise AssertionError(
                        "Verifier feedback ceased disclosing the exact optimum: "
                        + str((t["id"], q, fb))
                    )
            else:
                assert fb is None, (t["id"], q, fb)
                if q != best:
                    zero_entropy_tied_top += 1
        # Same permitted feedback as VERIFIED_COMPARATIVE; this policy merely
        # copies a better rival and contains no quotient construction.
        init = {"ranking": [first] + [x for x in t["queries"] if x != first]}
        fb = f["better_feedback"](init, t)
        if fb is not None:
            emitted += 1
        selected = fb["strictly_better_rival"] if fb else first
        oracle_only_correct += f["downstream"](t, possible, selected)["correct"]
        # No protected truth, verifier message, precomputed entropy field,
        # or LLM needed: exact public semantics suffice (cost is not charged).
        public_selected = best
        public_only_correct += f["downstream"](t, possible, public_selected)["correct"]
        # Replacing protected ground truth with a different compatible world
        # does not alter any expected-entropy query ranking.
        t2 = {**t, "truth": possible[-1]}
        assert f["downstream"](t2, possible, public_selected)["correct"]
    assert oracle_only_correct == 48 and public_only_correct == 48
    assert emitted > 0 and all_feedback_events > 0
    return {
        "source_blob": ORIGINAL_BLOB,
        "tasks": len(tasks),
        "strict_wrong_top_cases": all_feedback_events,
        "tested_top_cases": all_responses,
        "verifier_explicitly_names_exact_optimum": verified_rival_emissions,
        "zero_entropy_tied_top_cases": zero_entropy_tied_top,
        "fixed_first_no_feedback_correct": baseline_correct,
        "fixed_first_feedback_emitted": emitted,
        "copy_rival_no_model_correct": oracle_only_correct,
        "public_only_exact_enumerator_correct": public_only_correct,
        "epistemic": "POSTHOC_BOUNDED_CAUSAL_SUFFICIENCY",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutate-verifier", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        try:
            audit(mutated=True)
        except AssertionError as exc:
            assert "Verifier feedback ceased disclosing" in str(exc), str(exc)
            print("NEGATIVE_CONTROL_RED_AS_EXPECTED", flush=True)
        else:
            raise AssertionError("Mutation must cause the audit to fail")
    print(json.dumps(audit(args.mutate_verifier), indent=2))
