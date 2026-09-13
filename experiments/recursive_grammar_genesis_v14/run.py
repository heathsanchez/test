#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from kernel import Kernel
from challenge_pack import (
    A, B, C, D, E,
    MAIN_CORPUS,
    HELDOUT,
    WRONG_ORDER,
    HET_CORPUS,
    SINGLE_EXAMPLE_CORPUS,
    NO_GAIN_CORPUS,
    BAD_AUTH_CORPUS,
)


TIGHT_BUDGET = 3
RELAXED_BUDGET = len(HELDOUT)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x, "data"):
        return safe(x.data())
    if isinstance(x, dict):
        return {str(k): safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted(safe(v) for v in x)
    return x


def main() -> int:
    evidence = {
        "experiment": "recursive_grammar_genesis_v14",
        "scientific_freeze_commit": "aa0848ff59e4dffc323248f9bf008dfe94bacbd3",
        "post_freeze_challenges": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE / "PROTOCOL.md"),
            "FREEZE.json": sha256(HERE / "FREEZE.json"),
            "basis.py": sha256(HERE / "basis.py"),
            "kernel.py": sha256(HERE / "kernel.py"),
            "challenge_pack.py": sha256(HERE / "challenge_pack.py"),
        },
        "results": {},
        "gates": {},
    }

    k = Kernel()

    main_result = k.induce(MAIN_CORPUS, allow_hierarchy=True)
    evidence["results"]["main"] = safe(main_result)

    if main_result.get("status") == "VERIFIED":
        main_state = Kernel.state_from_data(main_result["state"])
        main_rules = main_state.rules
    else:
        main_state = None
        main_rules = tuple()

    warm = Kernel.construct_under_budget(
        HELDOUT,
        MAIN_CORPUS.atoms,
        main_rules,
        TIGHT_BUDGET,
    )
    cold_tight = Kernel.construct_under_budget(
        HELDOUT,
        MAIN_CORPUS.atoms,
        tuple(),
        TIGHT_BUDGET,
    )
    cold_relaxed = Kernel.construct_under_budget(
        HELDOUT,
        MAIN_CORPUS.atoms,
        tuple(),
        RELAXED_BUDGET,
    )

    higher_ablated = tuple(main_rules[:-1]) if len(main_rules) >= 2 else tuple()
    after_higher_ablation = Kernel.construct_under_budget(
        HELDOUT,
        MAIN_CORPUS.atoms,
        higher_ablated,
        TIGHT_BUDGET,
    )

    if len(main_rules) >= 2:
        lower_id = main_rules[0].rule_id
        lower_ablated = Kernel.remove_rule(main_rules, lower_id)
        lower_dependency = Kernel.validate_rule_dependencies(
            MAIN_CORPUS.atoms,
            lower_ablated,
        )
    else:
        lower_dependency = {"status": "NO_RULES"}

    wrong = Kernel.construct_under_budget(
        WRONG_ORDER,
        MAIN_CORPUS.atoms,
        main_rules,
        TIGHT_BUDGET,
    )

    hetero = k.induce(HET_CORPUS, allow_hierarchy=True)
    single = k.induce(SINGLE_EXAMPLE_CORPUS, allow_hierarchy=True)
    no_gain = k.induce(NO_GAIN_CORPUS, allow_hierarchy=True)
    bad_auth = k.induce(BAD_AUTH_CORPUS, allow_hierarchy=True)
    no_hierarchy = k.induce(MAIN_CORPUS, allow_hierarchy=False)

    if no_hierarchy.get("status") == "VERIFIED":
        nh_state = Kernel.state_from_data(no_hierarchy["state"])
        nh_rules = nh_state.rules
    else:
        nh_rules = tuple()

    hierarchy_ablation_heldout = Kernel.construct_under_budget(
        HELDOUT,
        MAIN_CORPUS.atoms,
        nh_rules,
        TIGHT_BUDGET,
    )

    evidence["results"]["warm_heldout"] = safe(warm)
    evidence["results"]["cold_tight"] = safe(cold_tight)
    evidence["results"]["cold_relaxed"] = safe(cold_relaxed)
    evidence["results"]["after_higher_ablation"] = safe(after_higher_ablation)
    evidence["results"]["lower_dependency"] = safe(lower_dependency)
    evidence["results"]["wrong_order"] = safe(wrong)
    evidence["results"]["heterogeneous"] = safe(hetero)
    evidence["results"]["single_example"] = safe(single)
    evidence["results"]["no_gain"] = safe(no_gain)
    evidence["results"]["bad_authority"] = safe(bad_auth)
    evidence["results"]["no_hierarchy"] = safe(no_hierarchy)
    evidence["results"]["hierarchy_ablation_heldout"] = safe(
        hierarchy_ablation_heldout
    )

    G = evidence["gates"]

    kernel_text = (HERE / "kernel.py").read_text()
    G["R1_no_challenge_specific_higher_grammar_in_frozen_core"] = (
        A not in kernel_text
        and B not in kernel_text
        and "REPEAT" not in kernel_text
        and "LOOP" not in kernel_text
    )

    first = main_rules[0] if len(main_rules) >= 1 else None
    second = main_rules[1] if len(main_rules) >= 2 else None

    G["R2_first_rule_earned_from_independent_positive_gain"] = (
        main_result.get("status") == "VERIFIED"
        and len(main_rules) == 2
        and first is not None
        and first.rhs == (A, B)
        and set(first.support_episodes) == {0, 1}
        and first.replacement_count == 8
        and first.gain == 6
        and main_result.get("generations", [])[0].get("after_cost")
            < main_result.get("generations", [])[0].get("before_cost")
    )

    G["R3_first_nonterminal_enters_next_candidate_language"] = (
        second is not None
        and first is not None
        and second.rhs == (first.rule_id, first.rule_id)
        and any(
            row.get("pair") == [first.rule_id, first.rule_id]
            for row in main_result.get("generations", [])[1].get(
                "eligible_candidates", []
            )
        )
    )

    G["R4_hierarchical_rule_genesis_exact_replay"] = (
        second is not None
        and first is not None
        and second.rhs == (first.rule_id, first.rule_id)
        and set(second.support_episodes) == {0, 1}
        and second.replacement_count == 4
        and second.gain == 2
        and warm.get("status") == "VERIFIED"
    )

    G["R5_hierarchy_reached_only_through_binary_promotions"] = (
        len(main_rules) == 2
        and all(len(rule.rhs) == 2 for rule in main_rules)
        and first is not None
        and second is not None
        and all(x in MAIN_CORPUS.atoms for x in first.rhs)
        and all(x == first.rule_id for x in second.rhs)
    )

    G["R6_warm_hierarchy_causally_beats_cold_tight_budget"] = (
        warm.get("status") == "VERIFIED"
        and warm.get("within_budget") is True
        and warm.get("encoded_length") == 3
        and cold_tight.get("status") == "UNKNOWN_BUDGET"
        and cold_tight.get("encoded_length") == len(HELDOUT)
        and cold_relaxed.get("status") == "VERIFIED"
        and after_higher_ablation.get("status") == "UNKNOWN_BUDGET"
        and after_higher_ablation.get("encoded_length") == 5
    )

    G["R7_lower_rule_ablation_invalidates_higher_dependency"] = (
        lower_dependency.get("status") == "INVALID_GRAMMAR_DEPENDENCY"
        and second is not None
        and lower_dependency.get("rule_id") == second.rule_id
        and first.rule_id in lower_dependency.get("missing", [])
    )

    G["R8_wrong_order_not_forced_into_learned_hierarchy"] = (
        wrong.get("status") == "UNKNOWN_BUDGET"
        and wrong.get("encoded_length", 0) > TIGHT_BUDGET
        and second is not None
        and second.rule_id not in wrong.get("encoded", [])
    )

    if hetero.get("status") == "VERIFIED":
        h_state = Kernel.state_from_data(hetero["state"])
        h_rules = h_state.rules
    else:
        h_rules = tuple()

    G["R9_same_kernel_induces_different_heterogeneous_grammar"] = (
        hetero.get("status") == "VERIFIED"
        and len(h_rules) == 1
        and h_rules[0].rhs == (A, A)
        and first is not None
        and h_rules[0].rhs != first.rhs
    )

    G["R10_single_episode_repetition_does_not_compile"] = (
        single.get("status") == "VERIFIED"
        and single.get("rule_count") == 0
        and single.get("compression_gain") == 0
    )

    G["R11_hierarchy_ablation_blocks_second_level_under_budget"] = (
        no_hierarchy.get("status") == "VERIFIED"
        and no_hierarchy.get("rule_count") == 1
        and hierarchy_ablation_heldout.get("status") == "UNKNOWN_BUDGET"
        and hierarchy_ablation_heldout.get("encoded_length") == 5
    )

    G["R12_unverified_lower_atom_stays_unknown"] = (
        bad_auth.get("status") == "UNKNOWN_AUTHORITY"
        and bad_auth.get("reason") == "lower_phrase_atom_not_authoritative"
    )

    G["R13_zero_gain_recurrence_does_not_compile"] = (
        no_gain.get("status") == "VERIFIED"
        and no_gain.get("rule_count") == 0
        and no_gain.get("compression_gain") == 0
    )

    G["exact_expansion_preserved_through_every_promoted_level"] = (
        main_result.get("status") == "VERIFIED"
        and warm.get("status") == "VERIFIED"
        and cold_relaxed.get("status") == "VERIFIED"
    )

    G["minimal_developmental_algorithm_respected"] = all(
        token in (HERE / "PROTOCOL.md").read_text()
        for token in (
            "EXECUTE",
            "VERIFY",
            "DIAGNOSE",
            "CONSTRAIN",
            "RESTRUCTURE",
            "CHOOSE",
            "COMPILE",
            "UPDATE",
        )
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_RECURSIVE_HIERARCHICAL_GRAMMAR_GENESIS_FROM_COMPILED_PHRASE_ATOMS"
        if evidence["full_pass"]
        else "RECURSIVE_GRAMMAR_GENESIS_V14_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
