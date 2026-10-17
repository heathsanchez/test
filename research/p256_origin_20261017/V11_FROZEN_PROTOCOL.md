# V11 frozen: entire 107-bit FreeLIP state inversion, 10 consecutive 26-bit outputs (not a small-seed scan)

Date 2026-10-17 NZ. Base: V10 latest evidence at ebf1714255f7a3d9b11671fa54ecbfdd46b44f75. Publicly known target is P-256 published Gx; NOT a fresh blind outcome. P-256's true point origin UNKNOWN.

## Scientific question

FreeLIP v1.1 from original [1997 source mirror](https://github.com/lrobot/freelip/commit/00898a4814d2cc1244bf348682be6ed10dda35f0), `lip.c` `zrandom` and `zrstarts` produce state
`s_{i+1}=A*s_i mod M` where `M=2^107-1`, `A=3^121 mod M`. For `zrandom(2^26)` with no rejection, one output is low 26 bits `s_i mod 2^26`. This experiment replaces guessed starting seeds with **any hidden state** `s_i ∈ [0,M)`. Can the *full P-256 published Gx* equal the base-field reduction mod p of exactly ten **consecutive** 26-bit FreeLIP output limbs, packed msf or lsf? Note original `zrandomb(p)` usually packs **eleven** 26-bit limbs at this size, so a 10-limb negative does NOT exclude the authentic historical 11-limb path. The previous V1/V2 bounded negatives excluded only named small/time seeds; this is a different (fully quantified) test.

Predeclared target `GX = 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296`, `P = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff`. Work only on `bits=26,nlimbs=10,no_rejection,msf/lsf`. Since `raw ∈ [0,2^260)` and `raw ≡ GX (mod P)`, enumerate every `q` with `raw=GX+q*P<2^260`. Split raw into 10 26-bit words according to each order. No hidden arbitrary resource restriction or seed subset.

## Proposed inverse method

Let `u=2^26`, `t_i` known 26-bit limbs, `s_0=t_0+u*h_0`, `H=ceil(M/u)`. Define `a_i=A^i mod M`, `c_i=inv(u,M)*(t_i-a_i*t_0) mod M`. Then `h_i ≡ a_i*h_0 - c_i mod M` and exact state bounds `0≤h_i≤(M-1-t_i)//u`. Lattice L is row span of `(1,a_1,...,a_4)` and `M*e_i` for i=1..4. A lattice point l corresponds to `(h0, h1+c1, ..., h4+c4)`. A feasible point lies in an explicit 5D integer box; every one lies within a provable Euclidean sphere about its center. Reduce the lattice basis with SymPy exact integer LLL; enumerate **all** reduced lattice points in the enclosing exact sphere using exact Gram-Schmidt bound recursion, then filter the true box; verify every full ten-limb output against direct independent modular recurrence. Enumeration must provide a complete count and no resource truncation before a NO_SOLUTION certificate. If exact enumeration is not finished, classification UNKNOWN_RESOURCE, never NO_SOLUTION.

Controls: synthesize P-256-shaped 10-limb point from **seed=20000, offset=7**, separately for msf and lsf; inverse must recover a state reproducing all outputs. Compare recovered (potentially multiple) states and true state. Mutated one-byte target must not trigger a false positive. The original prime239v1 seed20420 remains independently verified under its different 11-limb grammar, not replayed here. Include local random seeds 7,20420 with outputs not constrained to P to validate algebraic state inversion. Prove method soundness through exact equality and completeness through exact covering sphere, not probabilistic heuristic Babai alone. Check counts and exact source SHA.

Predeclared conclusion:
- If match, CANDIDATE_RAW_NUMERICAL_MATCH, NOT unique historical origin, not cryptographic vulnerability. Test on original 1997 C and source-distinct 11-limb path later before any larger claim.
- If rigorous all-q no-solution, WARRANTED_BOUNDED_NO_STATE_10_LIMB_GX (under the exact output grammar, no-rejection assumption). This would exclude **all** 107-bit states for that grammar, not all possible FreeLIP / NIST G generators.
- Otherwise UNKNOWN_SEARCH/UNKNOWN_RESOURCE with precise failure and retained controls.

Other prospective untouched base-point targets remain untested; no extra generator search, new source-based hypotheses or 11-limb upgrade without a separate freeze. Strong matched-LLM comparator NOT_RUN. P-256 provenance remains UNKNOWN.
