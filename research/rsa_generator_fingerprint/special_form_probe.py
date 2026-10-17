#!/usr/bin/env python3
"""Bounded exact RSA-270 special-power screen, NOT an SNFS no-go theorem."""
import math
import json
from pathlib import Path

N = int(
    "233108530344407544527637656910680524145619812480305449042948611968495918245135782867888369318577116418213919268572658314913060672626911354027609793166341626693946596196427744273886601876896313468704059066746903123910748277606548649151920812699309766587514735456594993207"
)
assert len(str(N)) == 270 and N.bit_length() == 895 and N % 991889 == 10237
REMAINDER_BOUND = 1 << 64

def search(n, max_base=4096, max_coeff=64, min_degree=4):
    found, best, tests = [], [], 0
    log_n = math.log(n)
    for base in range(2, max_base + 1):
        log_b = math.log(base)
        for coeff in range(1, max_coeff + 1):
            # Logarithm merely seeds the position; exact power comparisons adjust it.
            e = max(0, min(1024, int((log_n - math.log(coeff)) / log_b)))
            while e > 0 and coeff * pow(base, e) > n:
                e -= 1
            while e < 1024 and coeff * pow(base, e + 1) <= n:
                e += 1
            # Powers grow monotonically. Only bracketing exponents are nearest.
            for exponent in (e, e + 1):
                if not min_degree <= exponent <= 1024:
                    continue
                tests += 1
                residual = n - coeff * pow(base, exponent)
                mag = abs(residual)
                if mag <= REMAINDER_BOUND:
                    found.append(dict(coeff=coeff, base=base, exponent=exponent, residual=str(residual)))
                if len(best) < 8 or mag < best[-1][0]:
                    best.append((mag, base, coeff, exponent))
                    best.sort()
                    best = best[:8]
    return found, tests, best

def main():
    hits, tested, best = search(N)
    positive1, _, _ = search(2**895 - 1, max_base=8, max_coeff=4)
    positive2, _, _ = search(3*7**315 + 5, max_base=8, max_coeff=4)
    assert any(x["base"] == 2 and x["exponent"] == 895 and x["residual"] == "-1" for x in positive1)
    assert any(x["base"] == 7 and x["coeff"] == 3 and x["exponent"] == 315 and x["residual"] == "5" for x in positive2)
    result = {
        "epistemic_status": "LOCAL_EXACT_BOUNDED_NEGATIVE_NOT_GENERAL_SNFS",
        "class": "N=c*b^e+r, 2<=b<=4096, 1<=c<=64, 4<=e<=1024, |r|<=2^64",
        "input_digits": len(str(N)), "input_bits": N.bit_length(),
        "input_mod_991889": N % 991889,
        "tested_bracketing_expressions": tested,
        "hits": hits,
        "smallest_residual_bit_length": best[0][0].bit_length(),
        "closest_candidates": [
            dict(residual_bits=v.bit_length(), base=b, coeff=c, exponent=e)
            for v, b, c, e in best
        ],
        "positive_controls": "2/2 exact constructions detected",
        "limitation": "Does not test general SNFS polynomials, RNG weakness, or GNFS complexity.",
    }
    output = Path(__file__).with_name("special_form_result.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
