# P-256 V4: candidate-876 / candidate-1842 selection test

Date: 17 October 2026 (New Zealand). **Local exact arithmetic: PASS**. An independent GitHub Actions qualification must be checked separately; do not promote based on a green run alone. This work does **not** explain the original historical P-256 seed-selection policy, its base point, or any ECDSA weakness.

## Authorities and frozen boundary

- [V4 frozen source/protocol, commit 0d48ca14](https://github.com/heathsanchez/test/commit/0d48ca1489af07549b5e9a0bd5c67ccfeecb3dac) before candidate computations.
- [Anthropic original finding](https://www.anthropic.com/research/ecdsa-curve-origins) (16 October 2026): P-256 published seed is candidate 1842 from `lrand48` seeded with 1997-08-16T01:52:34Z. Candidate 876 is also **reported** to produce a size-appropriate prime-order curve with the same construction. This point-count conclusion was NOT independently recertified here.
- [NIST SP 800-186](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-186.pdf), February 2023, Appendix C.1, C.2.1.1, C.3.1: `a=-3`; from seed s derive `c` via SHA-1 and require `b²*c ≡ -27 (mod p)`, nonsingularity, suitable prime group order and security tests. The published procedure says to select a base point of order n but does not require selecting the first seed that passes.
- Previous independently replayed V1 / V2 / V3 negative results are not superseded.

## Local independently checkable result

- Two disjoint implementations reproduce the original lrand48 output bytes: 48-bit pure Python recurrence and host libc `srand48`/`lrand48`, yielding the same 20 bytes at candidate 876 and 1842.
- **876** seed `50C71A63F911DB7B2F31618ECF609D37154437F9`. The SHA-1-derived c is `0x276E46B26A6E09FBA8200CDD418D6DC3738C6B169131927838EC8E71DE4E8548`.
- **1842** seed `C49D360886E704936A6678E1139D26B7819F7E90` (exact NIST published seed). Derived c is `0x7EFBA1662985BE9403CB055C75D4F7E0CE8D84A9C5114ABCAF3177680104FA0D`, matching NIST; one modular root gives the exact official b.
- Both seeds produce two algebraic b choices (±) satisfying the NIST c relation and nonsingularity; both curves have constructible sample points. The corresponding root signs are **not** evidence of what the NSA selected.
- The published P-256 G lies on the accepted curve and `[n]G = identity` under a separate exact Python group law. This establishes the scalar multiplication equality, not independent primality or point counting for 876.
- Mutated seed, forbidden c=0, singular c, and nonsquare-ratio c controls correctly fail. Complete exact data in V4_RESULTS.json.

## Epistemic conclusion

**WARRANTED EXACT FINITE:** Reconstruction of the two seeds, c, b possibilities, nonsingularity, sample on-curve points, the published G check, and negative controls.

**CONDITIONAL REJECTION of “first suitable curve wins”:** Conditional on the additional cryptographic qualification reported for candidate 876 by Anthropic, first-success selection would have stopped at 876, not 1842. The observed published selection therefore requires an additional guard, an unrecorded search policy, environmental/history state, or a different procedure. This is a *disjunction*, not a discovered specific cause.

**UNKNOWN:** An independent group-order / embedding-degree certificate for 876, unique selection criterion, historical implementation trace, method generating the NIST base point G, autonomous MathGraph advantage over a strong equally informed baseline. We do not assert that the 1998 standard secretly imposes a “first acceptable candidate” condition.

## Next experiment

Do not add arbitrary post-hoc preferences (“smallest c,” “fewest bits,” etc.) to fit 1842. The next cheapest decisive evidence is an **independent group-order certificate for candidate 876**, retaining explicit alternative ±b roots, or an archival source/log that supplies a new pre-existing selection condition. Only then test that condition on P-224 and both 1997 ANSI runs before calling it a transferable historical rule.