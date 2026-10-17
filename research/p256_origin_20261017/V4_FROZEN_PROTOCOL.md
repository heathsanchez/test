# P-256 V4 — first-acceptable selection-rule witness (frozen before candidate computations)

Date: 2026-10-17 NZ. Parent: independently qualified V3 source head `69d1ed904255a32144a0c3c8c9321dc2c9fb0fa0`, GitHub Actions #38981333595. V1-V3 bounded exclusions remain unchanged.

## Sources / authority boundaries
- Primary contemporary NIST retrospective: NIST SP 800-186 (Feb 2023), Appendix C.2.1.1/C.1/C.3.1 and C.3.2, https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-186.pdf . It says for P-256 choose a=-3, generate c from SHA-1 seed, choose b with c*b² ≡ -27 (mod p), exclude singularity, demand prime group order and cryptographic criteria; select any base point G of order n. It does **not** specify selecting the first acceptable stream seed.
- Anthropic original report 2026-10-16, https://www.anthropic.com/research/ecdsa-curve-origins . It publishes source-executable C srand48/lrand48 20-byte candidates from 1997-08-16 01:52:34 UTC; accepted P-256 seed is candidate 1842. It reports candidate 876 yields another size-appropriate prime-order curve constructed with the same parameter procedure. That **reported point count is not an independent mathematical proof**.
- Existing source files and qualified V1-V3 attest official P-256 p, a, b, seed, full G, n. Same exact output as authoritative public constants is an independent known-answer check, not a discovery.

## Question
Can the source-backed first-acceptable algorithm with ONLY published NIST generation criteria explain accepting candidate 1842 rather than 876? What exact predicates can we independently establish for both candidates, without conjecturing a unique historical decision rule?

## Hypotheses and frozen tests
H0: The first SHA-1-consistent, nonsingular P-256 curve satisfying prime-order and published NIST cryptographic constraints is chosen, under this single lrand48 run. Anthropic's externally reported 876 prime-order result challenges H0. Independently assess computable prerequisites, and keep point-count/MOV as externally reported or UNKNOWN if no native independent proof.
H1: The published transcript plus standard criteria uniquely determines the **selection history**. Construct two history assignments, same seed stream and same published criteria, one accepts 876 and another continues to 1842. If all independent acceptance tests agree and any remaining obligation is source-reported, label NON_IDENTIFIABLE_CONDITIONAL rather than a proof of unknown historical facts.

Tests frozen before deriving candidate values:
1. Reproduce exactly 20 bytes at candidate 876 and 1842 using a standalone pure-Python 48-bit LCG and system native libc `srand48/lrand48` (when available). Check 1842 matches standardized C49D360886E704936A6678E1139D26B7819F7E90.
2. Implement *two independent formulations* of the NIST SHA-1 `c` construction, check published P-256 `c`, `b`, p, a=-3 congruence, full G on curve. For 876, compute exact c, prove 0<c<2^255 and 4c+27 nonzero mod p, calculate square-root choices b of (-27/c) mod p if a root exists, confirm both satisfy b² c ≡ -27 mod p and discriminant nonzero. Distinguish root sign and do not attribute a sign-selection rule to historical program absent archival evidence.
3. Collect schema statuses per candidate: seed_extraction=EXACT, SHA1_relation=EXACT, smoothness/nonsingularity=EXACT, actual_curve_cardinality=EXTERNAL_REPORT or UNKNOWN, MOV & anomalous / independent cardinality=UNKNOWN unless certified.
4. Construct a **bounded epistemic witness**: if one accepts Anthropic's prime-order assertion as an assumption, both outputs pass documented criteria and a first-success rule cannot explain the published index. Without that assumption, class solely as CONDITIONAL_OBSTRUCTION/UNKNOWN; not a proof that 876 is fully secure.
5. Restrict evaluation to those two indices and standards-listed tests. No post-hoc priority scores; no scanning newly invented selection criteria. No claim of stronger AI or ECDSA weakness. Record exact code/source digests, independent local execution, and CI only when actual GitHub runner passes.
6. Positive controls deliberately alter a seed byte, c, b and require rejection; an invalid nonresidue root candidate returns NO_SQUARE_ROOT (not a forged b).
7. Expected outcome if both match math predicates: the candidate-selection mechanism remains underdetermined by publicly available documents. If 876 fails a new exact documented predicate, preserve an explicit falsifier and recheck in independent process.

Go/no-go: A true historical selection law requires an authenticated contemporaneous source or additional independently verifiable accepted/rejected examples with non-post-hoc prediction. Don't extend V4 within this protocol.
