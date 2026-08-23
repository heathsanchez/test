from controller import (
    Budget,
    GeneratorSpec,
    GeneratorRun,
    ResearchState,
    ImportArtifact,
    CandidateAction,
    choose_next,
    robust_worst_case_elimination,
    robust_split_fraction,
    adversarially_expand_predictions,
    buffer_import,
    generator_boundary_exhausted,
    update_hypotheses,
)


def F(*xs):
    return frozenset(xs)


def A(name, lifecycle, mode, preds, generator="local", **kw):
    return CandidateAction(name, lifecycle, mode, tuple(preds), generator=generator, **kw)


B = Budget(10, 10, 10, 10000, 100)
H = ("SEARCH", "REPRESENTATION", "SURROGATE")
G = (
    GeneratorSpec("local", "local", 2),
    GeneratorSpec("map", "structural", 1),
)
OPEN = (
    GeneratorRun("local", 1, 1),
    GeneratorRun("map", 1, 1),
)
CLOSED = (
    GeneratorRun("local", 2, 2),
    GeneratorRun("map", 1, 1),
)


def main():
    # 1. V6 removes V5's hand-set exhaustion bit. A same-frame failure can justify
    # reframing only after every required frozen generator quota is audibly closed.
    zero = A("zero", "DISCOVER", "EXPLOIT", [F("x"), F("x"), F("x")])
    s = ResearchState("open", H, repeated_local_failures=5)
    assert choose_next(s, B, [zero], G, OPEN).value == "EXPAND_CANDIDATES"
    assert choose_next(s, B, [zero], G, CLOSED).value == "REFRAME"

    # 2. Pending candidates, protected-outcome leakage, or unresolved surprise all
    # invalidate an exhaustion claim.
    assert generator_boundary_exhausted(G, CLOSED)
    assert not generator_boundary_exhausted(G, CLOSED, unresolved_surprise=True)
    assert not generator_boundary_exhausted(
        G,
        (GeneratorRun("local", 2, 1, 1), GeneratorRun("map", 1, 1)),
    )
    assert not generator_boundary_exhausted(
        G,
        (GeneratorRun("local", 2, 2, 0, True), GeneratorRun("map", 1, 1)),
    )

    # 3. Discrimination is normalized, so changing hypothesis-set cardinality does
    # not automatically make a generator look better simply by inflating raw count.
    sep = A("sep", "DISCOVER", "DISCRIMINATE", [F("a"), F("b"), F("c")])
    assert robust_worst_case_elimination(sep, 3) == 2
    assert robust_split_fraction(sep, 3) == 1.0

    # 4. Independent prediction criticism can only reduce or preserve information.
    audited = adversarially_expand_predictions(
        sep, (F("b"), F("a"), F("a"))
    )
    assert robust_split_fraction(audited, 3) <= robust_split_fraction(sep, 3)

    # 5. Protected-outcome leakage disqualifies an otherwise perfect action.
    leaked = A(
        "leaked",
        "DISCOVER",
        "DISCRIMINATE",
        [F("a"), F("b"), F("c")],
        protected_outcome_access=True,
    )
    weak = A("weak", "DISCOVER", "EXPLOIT", [F("x"), F("x"), F("y")])
    assert choose_next(ResearchState("leak", H), B, [leaked, weak], G, OPEN).value == "weak"

    # 6. Outside papers/comments/repos/observations may arrive before a stall, but
    # only structural + differentially testable imports enter the rival buffer.
    art = ImportArtifact("paper", "TRANSFER_SCOPE", True, True)
    assert buffer_import(H, art) == H + ("TRANSFER_SCOPE",)
    vague = ImportArtifact("interesting", "HANDWAVE", True, False)
    assert buffer_import(H, vague) == H

    # 7. Green is not done. Attack is a hard gate: ordinary exploitation is blocked
    # until an ablation/control candidate exists and is run.
    success = ResearchState("green", H, target_verified=True)
    exploit = A("keep_optimizing", "DISCOVER", "EXPLOIT", [F("a"), F("b"), F("c")])
    assert choose_next(success, B, [exploit], G, OPEN).value == "GENERATE_ATTACKS"
    attack = A(
        "ablate",
        "VERIFY",
        "DISCRIMINATE",
        [F("a"), F("b"), F("c")],
        is_ablation_or_control=True,
    )
    assert choose_next(success, B, [exploit, attack], G, OPEN).value == "ablate"

    # 8. Passing attack forces transfer; passing transfer forces reconstruction.
    after_attack = ResearchState("attacked", H, target_verified=True, attack_passed=True)
    assert choose_next(after_attack, B, [exploit], G, OPEN).value == "GENERATE_TRANSFER_TESTS"
    transfer = A(
        "heldout",
        "TRANSFER",
        "DISCRIMINATE",
        [F("a"), F("b"), F("c")],
        is_transfer_test=True,
    )
    assert choose_next(after_attack, B, [transfer], G, OPEN).value == "heldout"

    after_transfer = ResearchState(
        "xfer", H, target_verified=True, attack_passed=True, transfer_passed=True
    )
    assert (
        choose_next(after_transfer, B, [exploit], G, OPEN).value
        == "GENERATE_RECONSTRUCTION_TESTS"
    )
    recon = A(
        "reconstruct",
        "TRANSFER",
        "INSPECT",
        [F("a"), F("b"), F("c")],
        is_reconstruction_test=True,
    )
    assert choose_next(after_transfer, B, [recon], G, OPEN).value == "reconstruct"

    # 9. Retention occurs only after causal attack, transfer, and reconstruction.
    done = ResearchState(
        "done",
        H,
        target_verified=True,
        attack_passed=True,
        transfer_passed=True,
        reconstruction_passed=True,
    )
    assert choose_next(done, B, [], G, OPEN).value == "RETAIN"

    # 10. A surprise remains a model miss; it cannot be forced into current rivals.
    kept, surprise = update_hypotheses(ResearchState("surprise", H), sep, "unpredicted")
    assert surprise and kept == H

    print("controller_v6_invariants=PASS")


if __name__ == "__main__":
    main()
