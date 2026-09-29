#!/usr/bin/env python3
"""Crystal V36: source-admit the V34 expanding K return inside the sole V23 cell.

Purpose
-------
V35 showed arbitrarily deep *local-owner* shadows of the V34 expanding return.
This gate asks whether that return is merely a chamber artifact or whether an
actual natural source from the sole V23 affine residual can execute it before
the currently qualified simple exits.

The witness is exact and deterministic:
  t = 1,018,706
  n(t) = N0 + NC*t

The gate verifies:
1. the full V25 uniform D/S/M constructor interface remains nonterminal along
   every source-prefix cell through all 20 bits of t;
2. the actual orbit has no direct descent, quarter splice, or one-step
   inverse-odd lower-source merge before ordinary depth 127;
3. at depth 73 it reaches V34 chamber state 514835 with canonical owner above
   the original source and satisfying the exact expanding-return guard;
4. depths 73..84 execute the exact V34 11-step expanding K return, including
   the owner affine map F(m)=(19683*m+18403)/2048;
5. the same natural source is not a counterexample: at depth 127 it reaches a
   source-relative quarter splice.

This is bounded/source-exact causal evidence, not Collatz QED. It proves that
V35's expanding mechanism is genuinely reachable from the V23 source family,
while also showing one exact natural realization is transient.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json

import collatz_crystal_parameter_quotient_v25 as v25

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_return_separator_v34 as v34

T_PARAM = 1_018_706
EXPECTED_BASE_DEPTH = 73
EXPECTED_EXIT_DEPTH = 127
BASE = v34.BASE
MOD = v34.MOD

def shortcut(x: int) -> int:
    return (3*x + 1)//2 if x & 1 else x//2

n = v25.N0 + v25.NC*T_PARAM
assert T_PARAM.bit_length() == 20

# Reclose the already-qualified V25 uniform constructor interface on every
# parameter-prefix cell containing this exact natural source.
prefix_rows = []
for d in range(T_PARAM.bit_length() + 1):
    r = T_PARAM % (1 << d) if d else 0
    z = v25.classify_cell(d, r, with_merge=True)
    prefix_rows.append({
        "parameter_depth": d,
        "residue": r,
        "terminal": z["terminal"],
        "reverse_states": z.get("reverseStates", 0),
        "exit": z.get("exit"),
    })
    assert not z["terminal"], (d, r, z)

# Follow the actual source.  Simple source-order exits are checked directly;
# the V25 uniform reverse bank is handled independently above.
y = n
base_y = None
base_owner = None
return_owner = None
actual_rows = []
first_simple_exit = None

for k in range(EXPECTED_EXIT_DEPTH + 1):
    if y < n and first_simple_exit is None:
        first_simple_exit = {"kind": "D", "depth": k, "endpoint": y}
    if y % 8 == 5 and y <= 4*n and first_simple_exit is None:
        first_simple_exit = {"kind": "S", "depth": k, "endpoint": y}
    if y % 3 == 2:
        p = (2*y - 1)//3
        if 0 < p < n and first_simple_exit is None:
            assert shortcut(p) == y
            first_simple_exit = {
                "kind": "M1", "depth": k, "endpoint": y, "lower_source": p
            }

    if EXPECTED_BASE_DEPTH <= k <= EXPECTED_BASE_DEPTH + len(v34.expanding):
        actual_rows.append({
            "depth": k,
            "parity": y & 1,
            "residue_mod_3pow12": y % MOD,
            "endpoint": str(y),
        })

    if k == EXPECTED_BASE_DEPTH:
        assert y % MOD == BASE
        S, C, _w = v34.best[BASE]
        num = (1 << S)*y - C
        assert num % MOD == 0
        m = num//MOD
        assert m >= n
        assert m % v34.emod == v34.eg
        base_y = y
        base_owner = m

    if k == EXPECTED_BASE_DEPTH + len(v34.expanding):
        assert y % MOD == BASE
        S, C, _w = v34.best[BASE]
        num = (1 << S)*y - C
        assert num % MOD == 0
        return_owner = num//MOD

    if k < EXPECTED_EXIT_DEPTH:
        # The declared first simple exit must not have fired yet.
        assert first_simple_exit is None, first_simple_exit
    y = shortcut(y) if k < EXPECTED_EXIT_DEPTH else y

assert first_simple_exit is not None
assert first_simple_exit["kind"] == "S"
assert first_simple_exit["depth"] == EXPECTED_EXIT_DEPTH

# Exact path identity against V34's predeclared expanding return.
expected_states = [e[0] for e in v34.expanding] + [v34.expanding[-1][1]]
expected_bits = [e[2] for e in v34.expanding]
assert [r["residue_mod_3pow12"] for r in actual_rows] == expected_states
assert [r["parity"] for r in actual_rows[:-1]] == expected_bits

Ae, Be = v34.compose(v34.expanding)
assert Ae == Fraction(19683, 2048)
assert Be == Fraction(18403, 2048)
assert Fraction(return_owner) == Ae*base_owner + Be
assert return_owner > base_owner > n

# Base-owner parameterization used by V35.
Sbase, Cbase, _ = v34.best[BASE]
base_res = (-Cbase * pow(MOD, -1, 1 << Sbase)) % (1 << Sbase)
assert Sbase == 13 and base_res == 7935
assert (base_owner - base_res) % (1 << Sbase) == 0
owner_t = (base_owner - base_res)//(1 << Sbase)
assert owner_t % (1 << 11) == 1260

result = {
    "schema": "COLLATZ_CRYSTAL_SOURCE_ADMITTED_RETURN_V36",
    "parents": {
        "V25": "collatz-crystal-parameter-quotient-v25@3d33a5a44cbcf3546f44e4ecdd4d153bafa03fcc",
        "V34": "collatz-crystal-k-return-separator-v34@87a6036487431d22c4d8744cf109e056d88f3b82",
        "V35": "collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385",
    },
    "v23_source": {
        "parameter_t": T_PARAM,
        "parameter_bits": T_PARAM.bit_length(),
        "source": str(n),
    },
    "v25_prefix_interface": {
        "prefix_cells_checked": len(prefix_rows),
        "all_nonterminal": all(not r["terminal"] for r in prefix_rows),
        "total_reverse_states": sum(r["reverse_states"] for r in prefix_rows),
        "rows": prefix_rows,
    },
    "source_admitted_expanding_return": {
        "base_depth": EXPECTED_BASE_DEPTH,
        "base_state": BASE,
        "base_endpoint": str(base_y),
        "base_owner": str(base_owner),
        "base_owner_ge_source": base_owner >= n,
        "owner_parameter": str(owner_t),
        "owner_parameter_mod_2pow11": owner_t % (1 << 11),
        "guard": "owner_t == 1260 (mod 2^11)",
        "return_depth": EXPECTED_BASE_DEPTH + len(v34.expanding),
        "return_owner": str(return_owner),
        "return_map": "F(m)=(19683*m+18403)/2048",
        "strict_owner_expansion": return_owner > base_owner,
        "actual_return_trace": actual_rows,
    },
    "later_exit": first_simple_exit,
    "scientific_verdict": (
        "V35_EXPANDING_RETURN_IS_SOURCE_ADMITTED_ON_AN_EXACT_V23_NATURAL_SOURCE, "
        "BUT_THIS_REALIZATION_IS_TRANSIENT_AND_QUARTER_SPLICES_AT_DEPTH_127"
    ),
    "consequence": (
        "Do not reject V35 as a free-owner chamber artifact. Conversely, this "
        "witness is not a counterexample and does not promote any finite carry "
        "depth: the universal residual remains exclusion of an infinite "
        "aperiodic source-admitted protected execution."
    ),
    "formal_guardrail": (
        "SourceProductZeroTail.zero_tail_kernel_empty_iff_collatz already proves "
        "that emptying the unrestricted zero-tail live kernel is equivalent to "
        "positive Collatz; a new source-order invariant is still required."
    ),
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
