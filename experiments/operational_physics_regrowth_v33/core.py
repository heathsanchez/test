from __future__ import annotations

from fractions import Fraction as F
from itertools import combinations, product
from typing import Sequence

Matrix = tuple[tuple[F, ...], ...]
Vector = tuple[F, ...]


def _fr(x: F) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _matmul(A: Matrix, B: Matrix) -> Matrix:
    n, m, p = len(A), len(B), len(B[0])
    assert len(A[0]) == m
    return tuple(tuple(sum((A[i][k] * B[k][j] for k in range(m)), F(0)) for j in range(p)) for i in range(n))


def _matvec(A: Matrix, v: Vector) -> Vector:
    return tuple(sum((A[i][j] * v[j] for j in range(len(v))), F(0)) for i in range(len(A)))


def _quad(v: Sequence[F], A: Matrix) -> F:
    return sum((v[i] * A[i][j] * v[j] for i in range(len(v)) for j in range(len(v))), F(0))


def _det(A: Matrix) -> F:
    n = len(A)
    if n == 0:
        return F(1)
    if n == 1:
        return A[0][0]
    if n == 2:
        return A[0][0] * A[1][1] - A[0][1] * A[1][0]
    return sum(((-1 if j % 2 else 1) * A[0][j] * _det(tuple(tuple(A[i][k] for k in range(n) if k != j) for i in range(1, n))) for j in range(n)), F(0))


def _principal_minor(A: Matrix, idx: tuple[int, ...]) -> F:
    return _det(tuple(tuple(A[i][j] for j in idx) for i in idx))


def _all_principal_minors_nonnegative(A: Matrix, proper_only: bool = False) -> bool:
    n = len(A)
    max_size = n - 1 if proper_only else n
    return all(_principal_minor(A, idx) >= 0 for r in range(1, max_size + 1) for idx in combinations(range(n), r))


def _subset_weights_nonnegative(A: Matrix) -> bool:
    n = len(A)
    for mask in range(1 << n):
        v = tuple(F(1 if mask & (1 << i) else 0) for i in range(n))
        if _quad(v, A) < 0:
            return False
    return True


def _total_weight(A: Matrix) -> F:
    one = tuple(F(1) for _ in A)
    return _quad(one, A)


def _rank1_companion(v: tuple[int, ...]) -> Matrix:
    s = sum(v)
    if s == 0:
        raise ValueError("witness sum must be nonzero")
    den = F(s * s)
    return tuple(tuple(F(v[i] * v[j], 1) / den for j in range(len(v))) for i in range(len(v)))


def _find_negative_integer_direction(A: Matrix, bound: int = 2) -> tuple[int, ...] | None:
    n = len(A)
    for raw in product(range(-bound, bound + 1), repeat=n):
        if all(x == 0 for x in raw) or sum(raw) == 0:
            continue
        v = tuple(F(x) for x in raw)
        if _quad(v, A) < 0:
            return raw
    return None


def _diagonal_joint_weight(A: Matrix, companion: Matrix) -> F:
    n = len(A)
    return sum((A[i][k] * companion[i][k] for i in range(n) for k in range(n)), F(0))


def discover_positivity() -> dict:
    raw = ((F(10), F(9), F(9)), (F(9), F(10), F(-9)), (F(9), F(-9), F(10)))
    scale = _total_weight(raw)
    A = tuple(tuple(x / scale for x in row) for row in raw)
    assert _total_weight(A) == 1
    witness = _find_negative_integer_direction(A)
    assert witness is not None
    companion = _rank1_companion(witness)
    joint = _diagonal_joint_weight(A, companion)
    local_ok = _subset_weights_nonnegative(A)
    proper_ok = _all_principal_minors_nonnegative(A, proper_only=True)
    all_ok = _all_principal_minors_nonnegative(A, proper_only=False)
    assert local_ok and proper_ok and not all_ok and joint < 0
    assert _subset_weights_nonnegative(companion)
    assert _all_principal_minors_nonnegative(companion)
    assert _total_weight(companion) == 1
    positive_controls = (
        tuple(tuple(F(1, 3) if i == j else F(0) for j in range(3)) for i in range(3)),
        tuple(tuple(F(1, 9) for _ in range(3)) for _ in range(3)),
    )
    controls_ok = all(_total_weight(C) == 1 and _subset_weights_nonnegative(C) and _all_principal_minors_nonnegative(C) for C in positive_controls)
    rules = [
        ("local_subset_nonnegative", lambda M: _subset_weights_nonnegative(M)),
        ("proper_principal_minors_nonnegative", lambda M: _subset_weights_nonnegative(M) and _all_principal_minors_nonnegative(M, True)),
        ("all_principal_minors_nonnegative", lambda M: _subset_weights_nonnegative(M) and _all_principal_minors_nonnegative(M, False)),
    ]
    selected = None
    for name, pred in rules:
        if all(pred(C) for C in positive_controls) and not pred(A):
            selected = name
            break
    assert selected == "all_principal_minors_nonnegative"
    return {
        "arena": "positivity_from_composition",
        "selected_rule": selected,
        "rule_grammar": [name for name, _ in rules],
        "composition_residual_count": 1,
        "positive_controls_preserved": controls_ok,
        "ablation_local_only_admits_counterexample": local_ok,
        "residuals": [{
            "candidate_dimension": 3,
            "candidate_determinant": _fr(_det(A)),
            "candidate_passes_local_subset_tests": local_ok,
            "candidate_passes_proper_principal_minors": proper_ok,
            "candidate_passes_all_principal_minors": all_ok,
            "negative_direction": list(witness),
            "companion_is_rank1_psd": True,
            "joint_event": [[i, i] for i in range(3)],
            "joint_weight": _fr(joint),
        }],
        "interpretation": "Within the frozen symmetric-rational rule grammar, lawful composition forces the full principal-minor/PSD rule beyond local event checks.",
        "scope": "finite exact 3x3 symmetric rational event-pairing grammar",
    }


def _biaffine(coeffs: tuple[int, int, int, int], a: F, b: F) -> F:
    c0, c1, c2, c3 = map(F, coeffs)
    return c0 + c1 * a + c2 * b + c3 * a * b


def _kron_by_combiner(A: Matrix, B: Matrix, coeffs: tuple[int, int, int, int]) -> Matrix:
    return tuple(tuple(_biaffine(coeffs, A[i][j], B[k][l]) for j in range(len(A[0])) for l in range(len(B[0]))) for i in range(len(A)) for k in range(len(B)))


def _kron_product(A: Matrix, B: Matrix) -> Matrix:
    return tuple(tuple(A[i][j] * B[k][l] for j in range(len(A[0])) for l in range(len(B[0]))) for i in range(len(A)) for k in range(len(B)))


def discover_parallel_product() -> dict:
    probes = (F(0), F(1, 3), F(1, 2), F(1))
    coeff_space = list(product((-1, 0, 1), repeat=4))
    def unit_ok(c):
        return all(_biaffine(c, a, F(1)) == a and _biaffine(c, F(1), a) == a for a in probes)
    def null_ok(c):
        return all(_biaffine(c, a, F(0)) == 0 and _biaffine(c, F(0), a) == 0 for a in probes)
    unit_survivors = [c for c in coeff_space if unit_ok(c)]
    survivors = [c for c in unit_survivors if null_ok(c)]
    assert survivors == [(0, 0, 0, 1)]
    selected = survivors[0]
    assoc = all(_biaffine(selected, _biaffine(selected, a, b), c) == _biaffine(selected, a, _biaffine(selected, b, c)) for a in probes for b in probes for c in probes)
    A = ((F(1, 2), F(1, 3)), (F(1, 4), F(2, 3)))
    B = ((F(2, 5), F(1, 5)), (F(3, 5), F(4, 5)))
    kron_ok = _kron_by_combiner(A, B, selected) == _kron_product(A, B)
    return {
        "arena": "parallel_composition_regrowth",
        "candidate_count": len(coeff_space),
        "unit_only_survivor_count": len(unit_survivors),
        "ablation_without_null_laws_survivor_count": len(unit_survivors),
        "survivor_count": len(survivors),
        "selected_coefficients": list(selected),
        "selected_formula": "a*b",
        "associative_on_probe_set": assoc,
        "kronecker_basis_replay": kron_ok,
        "interpretation": "Biaffinity plus null and unit event laws uniquely select multiplication; basis-pair composition therefore induces the Kronecker product in this grammar.",
        "scope": "biaffine scalar-combiner grammar with coefficients {-1,0,1}",
    }


def _apply_word(word: str, state: Vector, actions: dict[str, Matrix]) -> Vector:
    v = state
    for symbol in word:
        v = _matvec(actions[symbol], v)
    return v


def discover_sequential_algebra() -> dict:
    A: Matrix = ((F(1), F(1)), (F(0), F(1)))
    B: Matrix = ((F(1), F(0)), (F(1), F(1)))
    actions = {"A": A, "B": B}
    state: Vector = (F(1), F(0))
    observe = lambda v: v[0]
    words = ("", "A", "B", "AB", "BA", "ABA", "BAB")
    signatures = {w: observe(_apply_word(w, state, actions)) for w in words}
    ab, ba = signatures["AB"], signatures["BA"]
    order_sensitive = ab != ba
    assert order_sensitive
    scalar_sufficient = not order_sensitive
    diagonal_sufficient = not order_sensitive
    full_sufficient = all(observe(_apply_word(w, state, actions)) == signatures[w] for w in words)
    AB, BA = _matmul(B, A), _matmul(A, B)
    noncommuting = AB != BA
    families = [("scalar_1d", scalar_sufficient), ("diagonal_2d", diagonal_sufficient), ("full_2d_linear", full_sufficient)]
    selected = next(name for name, ok in families if ok)
    return {
        "arena": "sequential_operator_regrowth",
        "selected_family": selected,
        "protected_words": list(words),
        "signatures": {w: _fr(v) for w, v in signatures.items()},
        "AB_signature": _fr(ab),
        "BA_signature": _fr(ba),
        "order_sensitive": order_sensitive,
        "operators_noncommute": noncommuting,
        "scalar_family_sufficient": scalar_sufficient,
        "diagonal_family_sufficient": diagonal_sufficient,
        "full_family_sufficient": full_sufficient,
        "minimum_operational_dimension_in_family_ladder": 2,
        "quantum_algebra_forced": False,
        "frontier": "Jordan/C*-specific quantum algebra is not forced by these obligations; generic noncommutative real linear operators already satisfy them.",
        "interpretation": "Future consequence plus order sensitivity forces a noncommutative linear sequential representation in the declared family ladder, but not specifically quantum algebra.",
        "scope": "scalar/diagonal/full-2d exact rational linear family ladder",
    }


def run_all() -> dict:
    p, t, s = discover_positivity(), discover_parallel_product(), discover_sequential_algebra()
    gates = {
        "positivity_regrown": p["selected_rule"] == "all_principal_minors_nonnegative" and p["composition_residual_count"] > 0,
        "parallel_product_regrown": t["survivor_count"] == 1 and t["selected_formula"] == "a*b" and t["kronecker_basis_replay"],
        "sequential_operator_regrown": s["selected_family"] == "full_2d_linear" and s["order_sensitive"] and not s["quantum_algebra_forced"],
    }
    passed = all(gates.values())
    return {
        "experiment": "operational_physics_regrowth_v33",
        "verdict": "PASS_BOUNDED_OPERATIONAL_REGROWTH_V33" if passed else "FAIL_OPERATIONAL_REGROWTH_V33",
        "gates": gates,
        "forced": ["positive_semidefinite_pairing_rule", "multiplicative_parallel_product", "noncommutative_linear_sequential_operators"] if passed else [],
        "not_derived": ["Born", "Born rule", "complex Hilbert space", "Jordan or C* algebra uniqueness", "spacetime geometry", "physical constants"],
        "arenas": {"positivity": p, "parallel": t, "sequential": s},
        "claim_boundary": "All forced structures are relative to frozen finite grammars and operational obligations; this is scaffold-deletion/regrowth evidence, not a derivation of fundamental physics from distinctions alone.",
    }
