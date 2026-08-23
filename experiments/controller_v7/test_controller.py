from controller import (
    Budget,
    GeneratorSpec,
    GeneratorRun,
    ResearchState,
    ImportArtifact,
    CandidateAction,
    choose_next,
    generator_boundary_exhausted,
    observational_classes,
    robust_class_split_fraction,
    adversarially_expand_predictions,
    buffer_import,
    update_hypotheses,
)


def F(*xs):
    return frozenset(xs)


def A(name, lifecycle, mode, preds, generator="local", slot="depth1", **kw):
    return CandidateAction(name, lifecycle, mode, tuple(preds), generator, slot, **kw)


B = Budget(10, 10, 10, 10000, 100)
H = ("SEARCH_A", "SEARCH_B", "REPRESENTATION")
G = (
    GeneratorSpec("local", "local", ("depth1", "depth2")),
    GeneratorSpec("map", "structural", ("residual_map",)),
)
OPEN = (
    GeneratorRun("local", frozenset({"depth1"})),
    GeneratorRun("map", frozenset({"residual_map"})),
)
CLOSED = (
    GeneratorRun("local", frozenset({"depth1", "depth2"})),
    GeneratorRun("map", frozenset({"residual_map"})),
)


def main():
    # 1. Duplicate/repeated attempts cannot pad a search-exhaustion claim because
    # V7 closes over frozen named search slots, not an integer attempt quota.
    assert not generator_boundary_exhausted(G, OPEN)
    assert generator_boundary_exhausted(G, CLOSED)

    # 2. Pending or leaked generator slots block exhaustion.
    pending = (
        GeneratorRun("local", frozenset({"depth1"}), frozenset({"depth2"})),
        GeneratorRun("map", frozenset({"residual_map"})),
    )
    assert not generator_boundary_exhausted(G, pending)

    leaked = (
        GeneratorRun("local", frozenset({"depth1", "depth2"}), leaked=True),
        GeneratorRun("map", frozenset({"residual_map"})),
    )
    assert not generator_boundary_exhausted(G, leaked)

    # 3. SEARCH_A and SEARCH_B are observational duplicates in the current audited
    # action language, so they count as one rival class rather than two labels.
    a = A("a", "DISCOVER", "EXPLOIT", [F("x"), F("x"), F("y")], slot="depth1")
    b = A("b", "DISCOVER", "EXPLOIT", [F("p"), F("p"), F("q")], slot="depth2")
    classes = observational_classes([a, b], 3)
    assert len(classes) == 2
    assert any(set(c) == {0, 1} for c in classes)
    assert robust_class_split_fraction(a, [a, b], 3) == 1.0

    # 4. Adding a duplicate hypothesis label therefore creates no extra information
    # credit relative to an equivalent two-rival problem.
    base = A("base", "DISCOVER", "EXPLOIT", [F("x"), F("y")], slot="depth1")
    assert robust_class_split_fraction(base, [base], 2) == 1.0
    assert robust_class_split_fraction(a, [a, b], 3) == 1.0

    # 5. Independent criticism can only reduce or preserve discrimination.
    sep = A(
        "sep", "DISCOVER", "DISCRIMINATE", [F("a"), F("b"), F("c")], slot="depth1"
    )
    widened = adversarially_expand_predictions(sep, (F("b"), F("a"), F("a")))
    assert robust_class_split_fraction(widened, [widened], 3) <= robust_class_split_fraction(
        sep, [sep], 3
    )

    # 6. A zero-information pool is still candidate-search failure while any frozen
    # search slot remains open. Only slot-complete audited failure can yield REFRAME.
    zero = A("zero", "DISCOVER", "EXPLOIT", [F("x"), F("x"), F("x")], slot="depth1")
    s = ResearchState("stall", H, repeated_local_failures=5)
    assert choose_next(s, B, [zero], G, OPEN).value == "EXPAND_CANDIDATES"
    assert choose_next(s, B, [zero], G, CLOSED).value == "REFRAME"

    # 7. Candidate provenance must point to a predeclared search slot.
    bad = A("bad", "DISCOVER", "EXPLOIT", [F("a"), F("b"), F("c")], slot="made_up")
    try:
        choose_next(s, B, [bad], G, OPEN)
    except ValueError:
        pass
    else:
        raise AssertionError("undeclared generator slot must fail")

    # 8. Protected-outcome leakage is removed from both evidentiary choice and the
    # observational language used to score rival classes.
    leaked_action = A(
        "leaked",
        "DISCOVER",
        "DISCRIMINATE",
        [F("a"), F("b"), F("c")],
        slot="depth1",
        protected_outcome_access=True,
    )
    weak = A("weak", "DISCOVER", "EXPLOIT", [F("a"), F("a"), F("b")], slot="depth1")
    assert choose_next(ResearchState("leak", H), B, [leaked_action, weak], G, OPEN).value == "weak"

    # 9. Outside material remains an anytime source, but only structural and
    # differentially testable imports enter the rival buffer.
    art = ImportArtifact("paper", "TRANSFER_SCOPE", True, True)
    assert buffer_import(H, art) == H + ("TRANSFER_SCOPE",)

    # 10. Green result -> attack -> transfer -> reconstruction -> retention.
    exploit = A(
        "exploit", "DISCOVER", "EXPLOIT", [F("a"), F("b"), F("c")], slot="depth1"
    )
    green = ResearchState("green", H, target_verified=True)
    assert choose_next(green, B, [exploit], G, OPEN).value == "GENERATE_ATTACKS"

    attack = A(
        "attack",
        "VERIFY",
        "DISCRIMINATE",
        [F("a"), F("b"), F("c")],
        slot="depth1",
        is_ablation_or_control=True,
    )
    assert choose_next(green, B, [attack], G, OPEN).value == "attack"

    after_attack = ResearchState("after_attack", H, target_verified=True, attack_passed=True)
    assert choose_next(after_attack, B, [exploit], G, OPEN).value == "GENERATE_TRANSFER_TESTS"
    transfer = A(
        "transfer",
        "TRANSFER",
        "DISCRIMINATE",
        [F("a"), F("b"), F("c")],
        slot="depth1",
        is_transfer_test=True,
    )
    assert choose_next(after_attack, B, [transfer], G, OPEN).value == "transfer"

    after_transfer = ResearchState(
        "after_transfer", H, target_verified=True, attack_passed=True, transfer_passed=True
    )
    assert (
        choose_next(after_transfer, B, [exploit], G, OPEN).value
        == "GENERATE_RECONSTRUCTION_TESTS"
    )
    recon = A(
        "recon",
        "TRANSFER",
        "INSPECT",
        [F("a"), F("b"), F("c")],
        slot="depth1",
        is_reconstruction_test=True,
    )
    assert choose_next(after_transfer, B, [recon], G, OPEN).value == "recon"

    done = ResearchState(
        "done",
        H,
        target_verified=True,
        attack_passed=True,
        transfer_passed=True,
        reconstruction_passed=True,
    )
    assert choose_next(done, B, [], G, OPEN).value == "RETAIN"

    # 11. Surprise remains a model miss, not an invitation to rewrite history.
    kept, surprise = update_hypotheses(ResearchState("surprise", H), sep, "never_predicted")
    assert surprise and kept == H

    print("controller_v7_invariants=PASS")


if __name__ == "__main__":
    main()
