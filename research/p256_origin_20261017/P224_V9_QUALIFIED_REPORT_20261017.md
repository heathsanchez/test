# P-224 skipped-seed census V9 — independent external native qualification (2026-10-17)

**Epistemic status:** `WARRANTED_BOUNDED_PARIGP_SEA_REPRODUCTION` (within the exact published lrand48/seed-to-curve grammar and declared security predicates). **Historical selection mechanism: UNKNOWN.** This is NOT the discovery of a new ECDSA vulnerability, an independently authenticated historical program, or proof of general autonomous agent advantage.

## Source and provenance

- Source input: [Anthropic, 16 Oct 2026](https://www.anthropic.com/research/ecdsa-curve-origins), 1998-04-03 12:52:07 UTC `srand48`, five high bits? **Actual emitted seed bytes are `lrand48()>>23`, equivalently `state>>40`**, index 7026 official P-224 seed. Anthropic reported three earlier viable curves, but ordinary article text did not list their indices.
- 1998 ANSI X9.62 / NIST P-224 seed-SHA1 relation and public parameters, verified separately in [V6 source](https://github.com/heathsanchez/test/tree/research/p256-coefficient-sign-v6-20261017/research/p256_origin_20261017). P224 sign quotient mathematically certified in [V8](https://github.com/heathsanchez/test/commit/6df818d531984d07eddc7120ada374f350428c7f).
- **V9 protocol frozen BEFORE V9 calculations** at [40555025](https://github.com/heathsanchez/test/commit/405550256a06c74d1a06d9af30a57b84f0ef9457).
- **Qualified source/CI head:** [be67866d](https://github.com/heathsanchez/test/commit/be67866dda38e2e3f4776f398d29d036b0993de8); independent [GitHub Actions #38994719714 SUCCESS](https://github.com/heathsanchez/test/actions/runs/38994719714), all ten jobs successful (construction, 8 SEA shards, aggregation).
- [Original aggregate artifact #12086199147](https://github.com/heathsanchez/test/actions/runs/38994719714/artifacts/12086199147) GitHub SHA256 = `0038872cb5cab8524a69106a8c7d7e7b54a53f0504426d25512887af018a3849`, independently downloaded and reopened at same digest. **All eight shard ZIP SHA256 digests** independently compared with GitHub artifact records; no mismatch.
- Complete candidate-table canonical JSON SHA256 = `6ae4d488768e622d5ff307ca7bb1af2c2b7d10c0f6935fac2e7107eac1fa5d22`; audited expected published 7026 seed.

## Exact result

| Stage | Cases | Status |
|---|---:|---|
| All chronological P-224 `lrand48` candidates, 1..7026 | 7,026 | exact generated + SHA1 checked |
| Seed-to-coefficient failures (nonresidue) | 3,481 | eliminated by exact finite-field test |
| Valid nonsingular curve coefficient candidates, after ±b quotient | 3,545 | one PARI point count per class |
| PARI `ellsea(E,1)` early small-factor rejection | 3,289 | not prime order; exact cardinality not asserted |
| PARI `ellsea(E,1)` positive composite counts | 244 | composite |
| PARI exact prime-order counts | 12 | rigorous `isprime`, independent `[n]P=O` checks |
| Prime-order curves with 225-bit order (wrong specified size) | 8 | excluded by bit-length |
| Prime-order curves with 224-bit order, no anomalous or k<=1023 collision | **4** | eligible within declared tests |

**The four qualifying candidates:** 

| Index | Exact 160-bit seed | Group order (hex) |
|---:|---|---|
| **777** | `D00720E7691D403449C0D91BE84BFB2C7501A267` | `ffffffffffffffffffffffffffff3fa279701925749a7de262aa8cc3` |
| **1485** | `18CFDBCBB825568171212BC1610A5B8A8004E5C4` | `fffffffffffffffffffffffffffff819afa992d9c9222076db1ef949` |
| **5736** | `3C170A30EE6709DF9B4C9EA0B6C1E95FCD6200CE` | `ffffffffffffffffffffffffffff610362eb9e61800d49507468b249` |
| **7026 (published)** | `BD71344799D5C7FCDC45B59FA3B9AB8F6A948BC5` | `ffffffffffffffffffffffffffff16a2e0b8f03e13dd29455c5c2a3d` |

**3/3** independently reconstructed earlier qualifying indices agrees with the Anthropic source-reported *count* three. This alone does not establish novelty of those indices; they might already appear in the source figure.

## Exact bounded discriminator

Define `obs(i)` as the vector of *only the tested public admissibility predicates*: NIST SHA-1 coefficient equation; nonsingularity; 224-bit prime curve order; nonanomalous `n ≠ p`; no embedding degree `1..1023`; and ±b isomorphism quotient. The four candidates above have the **same positive observation vector**. Thus no selector that factors **only through this boolean observation vector** can uniquely choose index 7026. The "first acceptable in this exact set of tests" algorithm would choose **777**, not 7026. This is an exact consequence of the verified census, not an inferred historical intent.

Additional historical criteria (root sign, base point generator, private code state, convenience or manual choice) may distinguish the four. The real 1998 procedure, actual sequence of decisions, and P-224/P-256 base-point origins remain **UNKNOWN**. Do not treat this finite predicate quotient as universal equivalence or a security audit of every NIST criterion.

## Decisive next experiment

Find independently authenticated 1997–98 source, logs, or selection documentation that supplies a previously unfitted criterion. Freeze it, run **unchanged on the four candidates**, require a prediction selecting 7026 and at least one source-distinct accepted curve (e.g. P-256 1842) while rejecting earlier viable alternatives, or preserve UNKNOWN. No more arbitrary seed sweeps, post-hoc score fitting, or second root-sign SEA on P-224.

Exact source code in the [V9 frozen branch](https://github.com/heathsanchez/test/tree/research/p224-preselection-census-v9-20261017/research/p256_origin_20261017); retained old V1–V8 results are unchanged.
