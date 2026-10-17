# P-256 V13 — complete FreeLIP 11x26 historical sampler including rejected internal draws

Date: 2026-10-17 NZ. Freeze BEFORE V13 result or implementation. Parent V12 exact independently qualified [CI 39014510101](https://github.com/heathsanchez/test/actions/runs/39014510101), commit eeb6f629f3183c65fc6431d8b8c5fe5109fcc06b. Independent known 1997 C source [FreeLIP v1.1](https://github.com/lrobot/freelip/commit/00898a4814d2cc1244bf348682be6ed10dda35f0): `zrstart` + `zrandom(2^26)` repeated until a state falls under the rejection bound, `zrandomb(p)` uses ceil(bitlen(p)/26)+1 = **11 26-bit limbs** (high-limb-first), integer reduction mod p.

## Objective
Prior V12 proved no P-256 Gx origin from any 107-bit state of the **no-internal-rejection** source sampler, using 106 quotient-invariant bits, a weighted 5D lattice and a separate stdlib proof. V13 must eliminate the **actual rejected-draw exception** or classify it UNKNOWN; no random seed enumeration, no heuristic probability, no assertion that NSA used this routine.

## Source arithmetic and frozen max-gap lemma
`M=2^107−1`, `A=3^121 mod M`, `u=2^26`, `state_next=A*state mod M`. FreeLIP `zrandom(u)` rejects a state `s >= bound=M−(u−1)`. A rejected state can be written `s=M−k`, `1≤k≤u−1`. After d raw PRNG advances, `s'=M−(A^d k mod M)`. A second rejected state occurs exactly if `1≤(A^d k mod M)≤u−1`. For **each d=1..22 inclusive**, prove there are **no positive k,r <= u−1** satisfying `A^d*k−r = q*M` by enumerating all nonzero 2D lattice points (basis `(1,A^d mod M),(0,M)`) in the exact ball `k²+r²≤2(u−1)²`. Use LLL only to find a unimodular basis; independent exact rational integer-bound sphere enumeration is proof authority. If any pair found or enumeration truncated, stop and classify relative schedules UNKNOWN; do not automatically widen d.

If no two rejected states occur within d≤22, an 11-output `zrandomb(p)` call contains **at most one rejected internal draw**, because between its first and second rejected draws there could be at most eleven accepted outputs and therefore at most 12 raw steps. If rejection occurs before the *first* accepted output, it is absorbed into arbitrary initial state and V12 already excludes the resulting consecutive 11 accepted outputs. The only genuinely distinct new schedules have one rejected state at raw index j=1..10, immediately before accepted output-call j. Accepted output i then comes from raw PRNG index `i+(1 if i>=j else 0)`; rejected raw index j must lie in `[bound,M)`, all eleven accepted state values in `[0,bound)`.

## Exact all-state inversion, 20 source schedules
Reuse V12's proven 106 P-256 bit invariants (digits 2 low26, 3 low18, 5 low26, 6 low26, 7 low10) over all 2^30 possible modular reduction quotients. For each `j=1..10` and orientations `msf,lsf` (source-native msf, lsf countercontrol), derive the observed raw PRNG index `i+(i>=j)`, form the 5D **weighted** exact state lattice, verify LLL output via unimodular matrix and exact Gram-Schmidt, and enumerate ALL candidates inside enclosing ball by exact `isqrt` integer-bounded intervals. Reconstruct full 11 returned 26-bit limbs, require original `Gx` (not just the 106 invariant bits), verify rejected state and accepted states. Hard budget <=2,000,000 enumerator nodes per schedule; > budget => UNKNOWN_RESOURCE, not zero.
Original P-256 mod-p coordinate:
`GX=0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296`;
`P=0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff`.

## Controls
- V12 no-rejection 11-limb msf/lsf remains validated and unmodified.
- Planted rejection paths using a deliberately high rejected state `M−1` at raw temporal index j=1,7,10; for each orientation build accepted-output sequence from exact source recurrence and prove the inverse-state lattice recovers its genuine hidden state, accepted/rejected status, and full reduced x.
- Independently verify rejection-band membership and source state mapping against direct Python recurrence; include an ablation with one mutated output word which cannot count as a legitimate source match.
- Check positive known-history P-192/prime239v1 26-bit eleven-limb sampler controls by reference to earlier pinned positive V1; no claim the original NSA P-256 code has been found.

## Status criteria
- If all 22 2D max-gap tests pass and all 20 schedule inversions finish with zero exact full-coordinate matches while honoring rejected states, then source-independent verifier may qualify **NO_FREELIP_11x26_ORIGIN_OF_P256_Gx_FOR_ANY_107_BIT_STATE_WITH_SOURCE_REJECTION**. This covers the exact 26-bit FreeLIP/early-NTL sampling/reduction algorithm for any seed/warmup; does not exclude other limb widths (30/62), different point procedures, SHA-derived/scalar points, or source-level differences.
- If any match, `CANDIDATE_NUMERICAL_GENERATOR_MATCH` requiring authentic C replay, coordinates both x/y, and provenance before historical promotion.
- If gap proof or any inverse incomplete, `UNKNOWN_RESOURCE` with original negative lineage unchanged.

Native independent GitHub CI plus immutable source and independent proof artifact required before a WARRANTED label. Strong comparator not executed; no private-key issue, NSA selection explanation or world-first novelty claimed. No external writes, production deploy or mainline merge.
