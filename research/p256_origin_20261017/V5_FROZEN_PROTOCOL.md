# P-256 V5 — independent candidate-876 elliptic group-order certificate (freeze)

Date: 2026-10-17 Pacific/Auckland. Parent V4 SHA `c41af2df7d9c67a3948fcf753134e7feb4a2a1fe`, [GREEN #38985275415](https://github.com/heathsanchez/test/actions/runs/38985275415), [evidence #12083190444](https://github.com/heathsanchez/test/actions/runs/38985275415/artifacts/12083190444). The source V4 result, 876 and 1842 SHA-1 curve coefficients and BOTH candidate-876 ±b roots were frozen before V5.

## Question and exact boundary

Independently determine whether either elliptic curve derived from the *skipped* P-256 candidate 876 has rigorously prime group order, under the NIST prime field p and a=-3. This is currently a SOURCE_REPORTED but not independently warranted claim in V4 (Anthropic 16 Oct 2026). The answer would confirm or falsify the prime-order component of the earlier first-acceptable rule obstruction, but does not reconstruct the original selection reason.

## Source / software authorities
- Original Anthropic report: https://www.anthropic.com/research/ecdsa-curve-origins , recovered lrand48 P-256 candidates 876 and 1842.
- NIST SP 800-186 (2023), Appendix C.1, C.2.1.1, C.3.1: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-186.pdf ; prime group order, nonsingularity, embedded degree k>=1024, non-anomalous.
- PARI/GP documented `ellsea(E,tors)`, `ellcard(E)` and proven `isprime(n)`: https://pari.math.u-bordeaux.fr/dochtml/ref-stable/Elliptic_curves.html and https://pari.math.u-bordeaux.fr/dochtml/ref-stable/Arithmetic_functions.html . PARI has source-defined SEA exact point-counting; the algorithm's correctness is delegated to versioned toolchain, not independently Lean-proved.
- Use pinned Ubuntu 24.04 CI, record installed gp version and seadata availability. Install via OS packages, do not silently fall back to cloud proprietary oracle.

## Frozen two-signed-curve census
At p = FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF, a=-3:
- Candidate 876 roots b_lo = 57B035B319C68D8A8A3315B5631325B46FF3CD238179E6D548E4CAA0217DAA42 and b_hi = A84FCA4BE639727675CCEA4A9CECDA4B900C32DD7E86192AB71B355FDE8255BD.
- Accepted candidate 1842 control b = 5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B and N = FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551.
- For accepted b, exact ellsea(E,1) MUST equal published N, with isprime(N)=1, or classify harness RED. For BOTH 876 roots, call independently SEA-based ellsea(E,1). If returns a positive integer, verify full ellcard via group-law replay on deterministic on-curve points plus Hasse bounds, isprime rigorously. If ellsea returns 0 (early abort when nontrivial small subgroup found), report unknown exact cardinality for that root UNLESS twist identity from a positive cardinality exactly determines it. Never translate 0 into exact group order or prime false without tool-contract support.
- Since p ≡ 3 mod 4 and roots ±b, the curves are quadratic twists. If one exact #E is known, derive the other as 2*(p+1)-#E, with trace explanation and separate primality test. If both independently counted, cross-check sum.
- Reject ANY claim that the original process used the lower root; absent dated implementation source, both signs remain admitted hypotheses.
- Verify prime order via PARI `isprime`, embedding degree >=1024 by iterating (p mod n)^k for k=1..1023, n != p, discriminant nonzero. A source-level test for 876 follows only upon exact group's acceptance, not before. Optional exact native Python `[n]P=O` replay of a deterministic point from V4.
- If at least one 876 root has proven prime order and no disqualifying published criteria, classify FIRST_ACCEPTABLE_RULE_REJECTED_WITHIN_RECONSTRUCTED_1997_RUN. Historical preference/policy remains UNKNOWN. If neither does, classify ANTHROPIC_PRIME_ORDER_REPORT_INDEPENDENTLY_CHALLENGED, preserve evidence for review. If tool times out/fails, classify INDEPENDENT_ORDER_UNKNOWN, no promotion.
- No post-hoc extension to new curves, other seeds or modified candidate grammar; do not compare to LLM agents without actual baseline. No ECDSA vulnerability/private-key claim.

## Qualification
Freeze before point-counting, commit GP source, independent Python replay, CI workflow and exact JSON artifact. Green Actions is only warrant after the original formal GP calculations and Python checks actually ran, source hashes and canonical results inspected. Preserve failures/restarts if they occur. No upstream or production changes.
