# P-224 V10 — contemporary ANSI admission versus 1997 FreeLIP primality
Date: 2026-10-17 NZ. Freeze BEFORE native original-C evaluations. Parent qualified V9 [run 38994719714](https://github.com/heathsanchez/test/actions/runs/38994719714), preserving V1–V9 evidence. **No historical NSA implementation is claimed.**

## Objective
Correct an evidence-model conflation and falsify ONE historically plausible validator-failure mechanism:
- The 1998 X9.62 Annex A.3.2 predicate permits near-prime orders with prime subgroup n greater than 2^160 and 4 sqrt(p), near-prime cofactor l-smooth (e.g. lmax=255), MOV B>=20 and nonanomalous; no universal mandate that n has exactly the bit length of the field.
- V9 intentionally used a later/narrower P-224 target: **224-bit prime whole-group order**, which leaves four candidates 777/1485/5736/7026.
- V9's original protected SEA census ALSO independently classified candidate 77 as a **prime order with 225 bits** (source: PARI-GP shard-5 original retained V9 artifact), requiring a separate ANSI-vs-NIST interpretation.

Sources:
- Original public ANSI X9.62 1998 mirrored PDF https://safecurves.cr.yp.to/grouper.ieee.org/groups/1363/private/x9-62-09-20-98.pdf ; contextual source-linked summary https://dissect.crocs.fi.muni.cz/standards/x962; excerpt A.3.2 and A.2.2, including rmin, cofactor, MOV, anomaly.
- 1997 FreeLIP v1.1 (21 July 1997) original (2019 mirror) exact commit https://github.com/lrobot/freelip/commit/00898a4814d2cc1244bf348682be6ed10dda35f0, lip.c blob a86ce8ae5be49e0f35999a2c87f52e1718ebdb81, lip.h blob 080cda8aec8c0939348452ea3beb9f1afad845ef. Native APIs: zprobprime, zprime, zmcomposite, zrseed. A mirrored library is NOT evidence NSA used it.
- V9 full original verified native shard outputs and CRC/digest; don't substitute manually supplied n as proof without comparing pinned inputs.

## Frozen tests
A. From archived V9 shard-5 and aggregate, select **exactly** indices 77,777,1485,5736,7026. Verify each order, bit length, prime status, field P224, p ≡ 1 mod 4, cofactor1, Hasse, n != p, and p^k mod n !=1 for k=1..20. Independently reject one altered order and swapped index as integrity mutants. Treat earlier V9 other 225-bit prime results as existing positive n source, no new SEA claim.
B. Build FreeLIP v1.1 original C with gcc on Ubuntu 24.04, compile native wrapper, invoke zprobprime(n,1), zprobprime(n,5), zprobprime(n,12) on ALL five frozen V9 primes using exact decimal orders; expect 1 for each. Composites: 3*n77 and 3*n7026, expect 0. Print machine readable labels. Capture nonzero/timeout/crash as UNKNOWN or apparatus RED, NOT primality failure.
C. Test library-local vs libc-PRNG state: get lrand48() after srand48(891607927); reseed, perform all FreeLIP primality calls, get first lrand48() again and compare exactly. ALSO test explicit control srand48+one lrand48 state consumption alters the next output (not a vacuous equality). Hypothesis source-separable states: native FreeLIP primality does not consume libc lrand48; this is bounded to that C library and exact workflow, not original NSA curve generator.
D. Preserve predeclared ambiguity: historical code, PRNG coupling if other functions call libc rand, root selection, and whether 225-bit candidates were accepted in original design remain UNKNOWN. Does NOT prove original generator skipped 77 for that reason. No private-key/security weakness inference.
E. Repeat native test on default 64-bit; optionally 32-bit only if toolchain available without changing code. Same-ABI results not evidence other platforms. Record stdout, compiler, SHA/source and reproducibility. Strong agent comparator NOT_RUN.
F. Independent GitHub CI run and original source ZIP/artifact needed for WARRANTED_BOUNDED_SOURCE_BEHAVIOUR. Locally reconstructed old source arithmetic can be reported only as local. Don't claim passed CI until checked.

## Decision
- If 77 conforms to the 1998 model and original FreeLIP primality reports probable prime, then **1998 ANSI-only first-admissible would be 77, while V9's NIST-like 224-bit first-admissible is 777**. This is scope-relative, not a historical selection decision.
- If original zprobprime rejects verified primes, investigate **that exact source-function** defect and only then consider direct historical relevance. Otherwise reject only this *particular legacy checker* false-negative explanation.
- Any unexpected call failure is UNKNOWN, preserve code, logs and predecessor.
No upstream/contact/production/mainline writes.
