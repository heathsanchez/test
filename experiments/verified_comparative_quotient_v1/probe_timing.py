"""Minimal finite-world decision-time check; no security provenance asserted.

The instrument table represents an independently trusted source only by
ASSUMPTION. Replacing it with an owner-writable table invalidates any external
authority claim. This module tests logic and distinguishes phase timing.
"""


def possible_worlds(instruments, worlds, transcript):
    return tuple(
        w for w in worlds
        if all(instruments[name][w] == response for name, response in transcript)
    )


def common_optimal_actions(optimal, worlds):
    worlds = tuple(worlds)
    if not worlds:
        return frozenset()  # fail closed on impossible transcripts
    return frozenset.intersection(*(optimal[w] for w in worlds))


def evaluate_probe(instruments, name, worlds):
    answers = {}
    for world in worlds:
        outcome = instruments[name][world]
        answers.setdefault(outcome, []).append(world)
    return {outcome: tuple(ws) for outcome, ws in answers.items()}


def check_admissible_probe(instruments, name, cost):
    return name in instruments and cost > 0


def lawful_choice(optimal, worlds):
    common = common_optimal_actions(optimal, worlds)
    return sorted(common)[0] if common else None


def legitimate_measurement(instruments, world):
    return instruments["diagnostic"][world]


def oracle_relabelled_as_bit(optimal, world):
    return 0 if "A" in optimal[world] else 1
