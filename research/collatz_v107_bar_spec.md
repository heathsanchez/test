# V107 — Consequential coalescence-bar experiment

Status: CANDIDATE. Global Collatz: UNKNOWN. No QED.

Protected output: a source-coupled certificate that a positive source coalesces with a strictly smaller positive source, or an exact unresolved residue family.

At depth k, each parity word corresponds to one residue r modulo 2^k. The shortcut iterate has an exact affine expression T^k(r+2^k q) = 3^o q + T^k(r), with o odd steps. When 3^o < 2^k, a computable lower bound on q gives a uniform direct-descent certificate for that residue cylinder. The remaining cases must be recorded as UNKNOWN, not rejected or proven impossible.

For every k, check exact parity-word uniqueness, the affine formula, and guarded direct-descent inequalities. Replay previously certified source-merger families before generating new obligations. Report residual cylinders by their first unproved constraint, not by trajectory rank. Do not extrapolate finite coverage to an infinite natural-source bar.

Success boundary: a new universal Lean theorem excluding every natural-compatible infinite residual branch, or a smaller exact source-relative obstruction. Finite numerical coverage alone is not success.

Authority: V66 future-coalescence quotient; V94–V95 reject automatic modulus growth; V103–V106 classify actual stream alternatives and reject unconditional return sign monotonicity.
