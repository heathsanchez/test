#!/usr/bin/env python3
"""Crystal V36: Chess-style source-headroom regime gate.

Parent:
  collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385

Chess V54/V55 established a transferable method point: a local intervention
whose sign reverses across regimes must be conditioned on the engine-native
resource coordinate, not averaged globally.

For the Collatz residual, V31 already gives the exact lower-cost K law

    2^d p = x + E.

Relative to a fixed minimal-bad source n, K is a genuine lower-source exit iff
p<n, equivalently x+E < 2^d n.  Thus source-relative owner headroom is the
earned regime coordinate.  This gate compiles that threshold over every K
transition, derives the analogous threshold for every B(cost-20) transition,
checks the V34 expanding/contracting same-state returns against the source
floor, and falsifies the tempting but insufficient "unread source bits" proxy.

The experiment is diagnostic, not a Collatz proof.  In particular V35's
arbitrarily long finite expanding return shadows survive the exact source-floor
K gate once their least representatives exceed the V23 floor.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_rewind_v31 as v31
    import collatz_crystal_k_density_tradeoff_v32 as v32
    import collatz_crystal_k_boundary_v33 as v33
    import collatz_crystal_k_return_separator_v34 as v34
    import collatz_crystal_expanding_shadow_v35 as v35

N0 = 38_911_100_780_481_085_467
MOD = 3**12

def ceil_div(a: int, b: int) -> int:
    assert b > 0
    return -(-a // b)

def ceil_fraction(x: Fraction) -> int:
    return -(-x.numerator // x.denominator)

def least_ge_residue(residue: int, modulus: int, floor: int) -> int:
    if residue >= floor:
        return residue
    return residue + ceil_div(floor - residue, modulus) * modulus

# ---------------------------------------------------------------------------
# 1. Complete K source-floor gate.
# ---------------------------------------------------------------------------
lower = []
for row in v31.lower_rows:
    d = row["cost_drop"]
    E = row["E"]
    # p=(x+E)/2^d.  No lower-source exit means p>=N0.
    x_min_no_exit = (1 << d) * N0 - E
    lower.append({
        "d": d,
        "E": E,
        "x_min_no_exit": x_min_no_exit,
    })

same = []
for row in v31.same_rows:
    delta = row["delta"]
    # p=x-delta.  No lower-source exit means p>=N0.
    x_min_no_exit = N0 + delta
    same.append({
        "delta": delta,
        "x_min_no_exit": x_min_no_exit,
    })

assert len(lower) == 3832
assert len(same) == 450

lower_by_d = {}
for d in range(1, 6):
    xs = [r["x_min_no_exit"] for r in lower if r["d"] == d]
    Es = sorted({r["E"] for r in lower if r["d"] == d})
    assert xs
    lower_by_d[str(d)] = {
        "count": len(xs),
        "E_values": Es,
        "x_min_no_exit_min": min(xs),
        "x_min_no_exit_max": max(xs),
        "ratio_min_num": min(xs),
        "ratio_min_den": N0,
        "ratio_max_num": max(xs),
        "ratio_max_den": N0,
    }

assert [len([r for r in lower if r["d"] == d]) for d in range(1,6)] == [3702,107,13,9,1]
assert min(r["x_min_no_exit"] for r in lower if r["d"] == 1) == 2*N0 - 11
assert max(r["x_min_no_exit"] for r in lower if r["d"] == 1) == 2*N0 + 9
assert min(r["x_min_no_exit"] for r in lower if r["d"] == 5) == 32*N0 + 33
assert min(r["x_min_no_exit"] for r in same) == N0 + 2
assert max(r["x_min_no_exit"] for r in same) == N0 + 8

# ---------------------------------------------------------------------------
# 2. Every B transition is exactly a 12-odd / cost-20 local contraction.
#    Compile the exact source-relative start threshold needed merely to avoid
#    direct descent of the block endpoint below N0.
# ---------------------------------------------------------------------------
b_rows = []
for u, (_S, _C, w) in sorted(v32.best.items()):
    for bit in (0, 1):
        nw = v32.next_window(w, bit)
        cls, _target = v32.classify_word(nw)
        if cls != "B":
            continue
        rawS = sum(nw)
        rawC = v32.cocycle(nw)
        assert bit == 0
        assert rawS == 20
        # endpoint=(3^12*x+rawC)/2^20.
        # endpoint>=N0 iff x >= ceil((2^20*N0-rawC)/3^12).
        x_min_no_direct = ceil_div((1 << rawS)*N0 - rawC, MOD)
        b_rows.append({
            "source_state": u,
            "raw_cost": rawS,
            "raw_cocycle": rawC,
            "x_min_no_direct": x_min_no_direct,
        })

assert len(b_rows) == 15947
assert {r["raw_cost"] for r in b_rows} == {20}
b_min = min(r["x_min_no_direct"] for r in b_rows)
b_max = max(r["x_min_no_direct"] for r in b_rows)
assert b_max - b_min == 21

# ---------------------------------------------------------------------------
# 3. V33 zero-slack boundary retained only for its graph classification.
#    (V33 owner intercept arithmetic was superseded by V34.)
# ---------------------------------------------------------------------------
assert len(v33.recurrent) == 66
for cc, ee in v33.recurrent:
    assert len(cc) == 19 and len(ee) == 19
    assert sum(e[2] for e in ee) == 12
    assert sum(e[4] for e in ee) == 0
    assert {e[3] for e in ee} == {"I"}

tight_multiplier = Fraction(3**12, 2**19)
assert tight_multiplier > 1

# ---------------------------------------------------------------------------
# 4. Same chamber state, opposite returns: source-floor regime really changes
#    consequence.  Contracting return becomes an actual source exit below an
#    exact owner threshold; expanding return never does for m>=N0.
# ---------------------------------------------------------------------------
Ae, Be = v34.Ae, v34.Be
Ac, Bc = v34.Ac, v34.Bc
assert Ae > 1 and Be > 0
assert 0 < Ac < 1 and Bc < 0

contracting_no_exit_threshold = ceil_fraction((Fraction(N0) - Bc) / Ac)
assert contracting_no_exit_threshold == 86_371_586_335_064_384_399

exp_guard_min = least_ge_residue(v34.eg, v34.emod, N0)
con_guard_min = least_ge_residue(v34.cg, v34.cmod, N0)
exp_after = Ae*exp_guard_min + Be
con_after = Ac*con_guard_min + Bc
assert exp_after.denominator == 1 and con_after.denominator == 1
assert exp_after > N0
assert con_after < N0

# ---------------------------------------------------------------------------
# 5. "Unread source bits" is not the regime coordinate.  Reconstruct the V26
#    fixed natural witness: its source tail is certainly zero after bit-length
#    460, but its first simple OrdinaryExit occurs only at depth 518.
# ---------------------------------------------------------------------------
T_V26 = 685408643048678703309842726690675779814441196540003599299583389096836936979689649632335566636234945811040497388265518
NC = 3_782_158_995_862_761_504_768
source_v26 = N0 + NC*T_V26
source_bits = source_v26.bit_length()
assert source_bits == 460

def T(x: int) -> int:
    return (3*x + 1)//2 if x & 1 else x//2

first_simple_exit = None
y = source_v26
for depth in range(0, 700):
    if 0 < y < source_v26:
        first_simple_exit = ("D", depth)
        break
    if y % 8 == 5 and y <= 4*source_v26:
        first_simple_exit = ("S", depth)
        break
    if y % 3 == 2:
        p = (2*y - 1)//3
        if 0 < p < source_v26:
            assert T(p) == y
            first_simple_exit = ("M1", depth)
            break
    y = T(y)

assert first_simple_exit == ("M1", 518)
assert source_bits < first_simple_exit[1]

# ---------------------------------------------------------------------------
# 6. Falsifier: the exact source-headroom gate still does NOT close V35.
#    For every checked nested expanding shadow whose least start is above N0,
#    all canonical K target owners along the shadow also remain >=N0.
# ---------------------------------------------------------------------------
R = v35.R_ONE
M = v35.B
shadow_rows = []
first_above = None
for repeats in range(1, v35.CHECK_R + 1):
    start = v35.owner(R)
    cur = start
    min_owner = cur
    min_k_target = None
    for _ in range(repeats):
        for e in v34.expanding:
            a, b = v34.owner_map(e[0], e[1], e[2])
            nxt = a*cur + b
            assert nxt.denominator == 1
            cur = nxt.numerator
            min_owner = min(min_owner, cur)
            if e[3] == "K":
                min_k_target = cur if min_k_target is None else min(min_k_target, cur)
    above = start > N0
    if above and first_above is None:
        first_above = repeats
    if above:
        assert min_owner >= N0
        assert min_k_target is not None and min_k_target >= N0
    shadow_rows.append({
        "repeats": repeats,
        "start_owner": str(start),
        "start_above_source_floor": above,
        "minimum_owner_on_shadow": str(min_owner),
        "minimum_K_target_owner": str(min_k_target),
        "source_floor_gate_survives": bool(above and min_k_target >= N0),
    })
    R, M = v35.next_shadow_residue(R, M)

assert first_above == 5
assert all(
    row["source_floor_gate_survives"]
    for row in shadow_rows
    if row["start_above_source_floor"]
)

result = {
    "schema": "COLLATZ_CRYSTAL_SOURCE_HEADROOM_GATE_V36",
    "parent": "collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385",
    "chess_transfer": {
        "principle": (
            "When one local mechanism has opposite consequences across regimes, "
            "promote the native resource coordinate and gate the mechanism there; "
            "do not average the regimes."
        ),
        "collatz_coordinate": "source-relative canonical-owner headroom",
    },
    "K_source_floor_gate": {
        "law_lower_cost": "2^d*p=x+E; lower-source exit iff x+E < 2^d*n",
        "law_same_cost": "p=x-delta; lower-source exit iff x-delta < n",
        "lower_cost_transitions": len(lower),
        "same_cost_transitions": len(same),
        "lower_cost_by_drop": lower_by_d,
        "same_cost_threshold_min": min(r["x_min_no_exit"] for r in same),
        "same_cost_threshold_max": max(r["x_min_no_exit"] for r in same),
    },
    "B_source_floor_gate": {
        "transitions": len(b_rows),
        "all_raw_cost": 20,
        "law": "endpoint=(3^12*x+C)/2^20; no direct source descent requires endpoint>=n",
        "x_min_no_direct_min": b_min,
        "x_min_no_direct_max": b_max,
        "ratio_min_num": b_min,
        "ratio_min_den": N0,
        "ratio_max_num": b_max,
        "ratio_max_den": N0,
        "threshold_width_in_integers": b_max-b_min,
    },
    "zero_slack_boundary": {
        "recurrent_components": 66,
        "shape": "each is a pure-I 19-step / 12-odd / D=0 cycle",
        "tight_multiplier_num": tight_multiplier.numerator,
        "tight_multiplier_den": tight_multiplier.denominator,
        "tight_gap_num": tight_multiplier.numerator-tight_multiplier.denominator,
    },
    "same_state_return_regime": {
        "base_state": v34.BASE,
        "contracting_return_no_exit_start_threshold": contracting_no_exit_threshold,
        "contracting_threshold_ratio_num": contracting_no_exit_threshold,
        "contracting_threshold_ratio_den": N0,
        "least_expanding_guard_owner_at_or_above_floor": exp_guard_min,
        "least_expanding_guard_owner_after_return": exp_after.numerator,
        "least_contracting_guard_owner_at_or_above_floor": con_guard_min,
        "least_contracting_guard_owner_after_return": con_after.numerator,
        "consequence": (
            "At essentially the same source-scale start, the expanding guard jumps "
            "well above the floor while the contracting guard is already an "
            "OrdinaryExit. The guard/headroom regime is consequential."
        ),
    },
    "tail_zero_falsifier": {
        "v26_source_bit_length": source_bits,
        "first_simple_ordinary_exit": {
            "kind": first_simple_exit[0],
            "depth": first_simple_exit[1],
        },
        "consequence": (
            "SourceProduct tail=0 / exhausted unread source bits is not sufficient: "
            "the concrete natural witness remains no-simple-exit for 58 further steps."
        ),
    },
    "v35_shadow_falsifier": {
        "checked_repeats": v35.CHECK_R,
        "first_least_shadow_start_above_v23_floor": first_above,
        "all_above_floor_shadows_pass_K_source_floor_gate": True,
        "first_rows": shadow_rows[:8],
        "last_row": shadow_rows[-1],
        "consequence": (
            "Source headroom is an earned coordinate but not a standalone closeout. "
            "Arbitrarily deep finite expanding guarded shadows remain compatible with "
            "the exact K source-floor gate on the checked recurrence."
        ),
    },
    "scientific_verdict": (
        "SOURCE_HEADROOM_IS_CONSEQUENTIAL; TAIL_ZERO_PROXY_REJECTED; "
        "HEADROOM_GATE_ALONE_REJECTED_AS_UNIVERSAL_CLOSEOUT"
    ),
    "next_residual": {
        "name": "HEADROOM_GATED_APERIODIC_RETURN_LANGUAGE",
        "statement": (
            "Compile the recurrent D=0 19/12 identity cycles together with the first "
            "source-headroom-admissible B/lower-K reset. Quotient by protected source "
            "consequence, not chamber state alone. The target is to show that a fixed "
            "positive natural no-Exit source cannot realize infinitely many gated "
            "reset epochs without its nested source/carry guard becoming non-natural."
        ),
        "smallest_next_experiment": (
            "Build the induced low-headroom-to-low-headroom return transducer: each "
            "zero-slack identity cycle may repeat only until the exact B/K source "
            "threshold is reached; then record the first legal reset and its new "
            "source-relative band. Search this guarded macro graph for recurrent "
            "natural-compatible SCCs and emit the first separator if any survive."
        ),
        "forbidden_shortcuts": [
            "raw carry-depth increase",
            "tail-zero-only finite automaton",
            "state-only owner rank",
            "treat local contraction as original-source descent",
        ],
    },
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
