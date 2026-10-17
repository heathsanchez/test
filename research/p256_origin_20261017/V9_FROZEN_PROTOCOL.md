# V9: P-224 pre-7026 exact candidate census — frozen experiment

**Date:** 2026-10-17 NZ. **Authority:** isolated read-only external-source analysis, parent V8 exact source SHA `6df818d531984d07eddc7120ada374f350428c7f` and [successful CI 38992735686](https://github.com/heathsanchez/test/actions/runs/38992735686). **Status at freeze:** CANDIDATE; NO V9 COMPUTATION YET.

## Source authorities and information already disclosed

- [Anthropic's 2026-10-16 report](https://www.anthropic.com/research/ecdsa-curve-origins) gives the Unix timestamp `1998-04-03 12:52:07 UTC`, the 48-bit `srand48` / `lrand48` recurrence with 20 outputs of `state >> 40` per candidate, and the accepted P-224 seed at **candidate index 7026**. It *claims* that the stream skipped **three earlier viable prime-order curves**, but **does not identify their indices in ordinary accompanying text** (figure may). The prior known count of three is a nonblind corroboration target, not new discovery.
- The NIST X9.62-derived prime-field `c=SHA1` relation and `b²c ≡ -27 (mod p)`, `a = -3`, field prime P224 and published `b` have source-reproduced positive checks in [V6 result](https://github.com/heathsanchez/test/blob/6df818d531984d07eddc7120ada374f350428c7f/research/p256_origin_20261017/V6_RESULTS.json).
- [V8 group-isomorphism witness](https://github.com/heathsanchez/test/blob/6df818d531984d07eddc7120ada374f350428c7f/research/p256_origin_20261017/V8_FROZEN_PROTOCOL.md): for P224 `p ≡ 1 (mod 4)`, the ±`b` curves are isomorphic over `F_p`, so **one exact point-count per canonical root pair** is sufficient for the prime-order predicate. This mathematical fact does not identify historical root sign.
- [V5 successful PARI/GP replay](https://github.com/heathsanchez/test/actions/runs/38985936321) used `ellsea(E,1)` plus `isprime(n)`, with caveat that a zero may be an early small-subgroup rejection rather than a full #E certificate.

## Frozen question

Of the **entire fixed 1..7025 candidate index range**, how many distinct P-224 parameters could pass the explicitly declared curve-admission predicate? Can the result explain why 7026 was historically chosen? No post-result changing acceptance conditions. This is a retrospective all-prefix census, not genuinely blind future science.

## Stage A: exact 1..7026 candidate construction

1. Implement the published 48-bit C LCG recurrence independently in Python. Per candidate, draw 20 `state >> 40` bytes, indexing from 1. Require official **7026** seed match. Independently match host libc `srand48/lrand48` on the first and last 20 bytes when available.
2. For every earlier seed, use the **same V6** 223-bit truncated SHA-1 `c` construction; retain arithmetic steps and SHA-256 of the frozen source script and resulting serialized complete candidate table.
3. Classify per index: `c==0`, `-27*c^-1 (mod p)` Legendre nonresidue, valid square root pair, discriminant zero, and standard admissible nonsingular curve. One canonical `min(b,p-b)` root is used **only for cardinality**, not a historical root-choice claim.
4. Verifier-independent spot checks for SHA-1 seed coefficient `7026`, both roots, and sample replay at indices `1,2,876,7025` (876 is not asserted prime order for P224).
5. Preserve all candidates and statuses including arithmetic rejections, failure, and UNKNOWN.

## Stage B: prime-order census

1. For each canonical nonsingular curve, attempt `PARI/GP ellsea(ellinit([-3,b],p),1)` with per-worker budget of 25 minutes and total 8 workers max (shard by `index mod 8`). Install Ubuntu `pari-gp` + `pari-seadata`; record versions and errors. If package fails or timer/resource exhausted, report `UNKNOWN_PARTIAL`, never zero candidates. **Do not change shard count or budget after results**.
2. For positive `n`, require exact Hasse bound, PARI `isprime(n)==1`, `n.bit_length()==224`, `n!=p`, and no embedding-degree collision for `1..1023`. A positive `ellsea` with composite n is `REJECTED_PRIME_ORDER`; `ellsea(...,1)==0` is `NOT_PRIME_BY_TORSION_TEST` but exact cardinality `UNKNOWN`. Any negative/error = UNKNOWN.
3. For finalists, choose a deterministic low-x on-curve point and separately verify `[n]P=O` in independent Python EC group arithmetic. PARI remains the authority for full cardinality/primality (not Lean-certified).
4. Require the original **7026** case passes and order equals NIST P-224 published `n`. If it fails, experiment invalid/harness RED.
5. Aggregate 8 shard outputs only after all shards pass exact uniqueness/completeness; report index list with exact seed, c, b (canonical), n and small-factor rejection counts. Compare discovered qualified earlier candidates to Anthropic's three-source report; mismatch must remain an explicit unresolved discrepancy.

## Interpretation and falsifiers

- A full census with exactly three pre-7026 prime-order 224-bit candidates is **WARRANTED_BOUNDED_REPRODUCTION**, not discovery of a selection law, proof of historical intent, or proof of ECDSA insecurity. If there are >3, test additional criteria in a NEW preregistered V10 only.
- If the earlier candidates pass exactly the published tests, first-acceptable rule is rejected **within this named model**. A historical last/priority condition remains UNKNOWN.
- If no exact group counts or finite all-prefix execution, classify UNKNOWN_PARTIAL, never invent three indices.
- No inference of original P-224 generator-point derivation, no new math novelty, no general L7; full-lifetime agent baseline NOT_RUN. No upstream or mainline writes, no unsolicited outreach or deployment.
- Preserve all prior V1–V8 results and failures. V9 is an isolated branch.
