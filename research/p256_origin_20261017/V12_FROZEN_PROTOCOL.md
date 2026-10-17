# V12 frozen: inverse of authentic FreeLIP 11 × 26-bit output geometry from invariant P-256 bit slices

Date 2026-10-17 NZ. Parent: independently qualified V11 GitHub Actions #39013725537 at 20b07b0f77b3d6ef84574e2f4055c854711eafb9. No origin/crypto-security claim.

## Current original-source problem
In the 1997 FreeLIP/early NTL PRNG `M=2^107−1`, `A=3^121 mod M`, `state_{i+1}=A*state_i mod M`. `zrandom(2^26)` exposes the low 26 bits of an accepted state. The historical `zrandomb(p)` uses p's 26-bit limb length plus one: P-256 => **11 limbs** (temporal high limb first). It then reduces the generated raw integer modulo p. Prior V11 completely excluded only 10 limbs; this deliberately tests the 11-limb case over **every possible** initial state (not small seeds), but excludes internal PRNG rejection-skips (a separate grammar). Both msf (source-native) and lsf (countercontrol) orders.

## Source-pinned special-modulus observation
Set exact P-256 `p=2^256−2^224+2^192+2^96−1`, target public `GX=0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296`. Any 11×26-bit raw integer reproducing GX mod p is `raw=GX+q*p` with `q=0,…,2^30−1`. Write 11 base-`2^26` digits `d_0,…,d_10` in increasing significance.

For every q, the following *low-bit observation masks* are hypothesized to be invariant (must be proved with integer inequalities rather than assumed from a few q samples):
- digit d2: bottom 26 bits fixed;
- digit d3: bottom 18 bits fixed;
- digit d5: bottom 26 bits fixed;
- digit d6: bottom 26 bits fixed;
- digit d7: bottom 10 bits fixed.
They total **106 constrained bits** across five PRNG state outputs. Source of invariance: `p ≡ −1 (mod 2^96)`, `p ≡ 2^96−1 (mod 2^192)`, and exact endpoint inequalities preventing carry across the affected slices for `0≤q<2^30`. The source-native temporal order is d10, d9, …, d0 (msf); exploratory reversed order is d0, …, d10.

## State inversion / completeness
For each observed temporal index i with masked low b_i bits, `s_i=t_i+2^{b_i} h_i`, with `0≤h_i≤floor((M−1)/2^{b_i})`. Choose the earliest observed i0, let `a_i=A^(i−i0) mod M`. Then `h_i ≡ C_i h0−c_i (mod M)`, `C_i= a_i * 2^{b0} * inv(2^{bi}) mod M`, `c_i=(t_i−a_i*t0)*inv(2^{bi}) mod M`.

Use the **integer-weighted lattice** whose row 0 is `(2^{b0}, 2^{b1} C1, …)` and rows i>0 are `2^{bi} M e_i`. Every feasible state falls inside a box of side lengths `2^{bi}*floor((M−1)/2^{bi})`. Enclose the box in its exact Euclidean sphere. Reduce lattice with SymPy `lll_transform`, independently verify the basis change is unimodular, and enumerate ALL integer coefficients in the enclosing sphere using exact rational Gram-Schmidt and rigorously *overestimated* integer sqrt intervals (no floats). Filter true boxes, reconstruct each full 11-output word sequence and its reduction modulo p. Stop and classify UNKNOWN_RESOURCE rather than assert zero if the declared cap of 2,000,000 visited nodes is exceeded.

## Calibration, read-only bounds and decisions
1. Prove the five advertised masked digit invariants over the WHOLE q domain using exact endpoint arithmetic (no 2^30 iteration); separately test q boundaries including 0, Q, and ordinary carry thresholds.
2. Known-state positive tests: real FreeLIP source recurrence seed 20000 at offset7, plus seed 20420 at offset29, each packed in msf/lsf, and verify weighted lattice returns the true state from *its own five masked output observations*. Validate original 1997 source's 11-limb prime239v1 seed20420 control separately as previously qualified, not a new explanation.
3. Work with the two actual invariant observation vectors, each orientation. If a source-consistent first-output state is recovered, replay all eleven outputs exactly; compare generated raw modulo p to the published P256 Gx. Record all states, indices and duplicates. No claim of historical origin from a numerical match alone.
4. If exhaustive inverse + full replay yields no match for both orientations, warrant only `NO_FREELIP_STATE_11x26_NO_REJECTION` (actual source packing under declared 26-bit mode), not all FreeLIP output widths, rejected internal draws or historical generator operations.
5. Small, separately checkable certificate is preferred; if the candidate list is large retain exact code and independent verifier with complete bounds. Independent GitHub Actions + artifact required before external qualification; preserve local result and no false-green. No outside repo modification, LLM comparator or public media claim.

No post-hoc feature masks: if these fixed observations are insufficient, record UNKNOWN and freeze a new V13 before adding distinctions. P-224/P-384/P-521 heldouts remain untouched.
