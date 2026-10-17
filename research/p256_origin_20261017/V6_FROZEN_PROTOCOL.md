# P-256 V6 — root-choice policy as an explanation for skipped candidate 876 (pre-result freeze)

Date 2026-10-17 Pacific/Auckland. Parent: independently qualified V5 PARI/GP exact point counts at commit `d7e44280604b72f2266f172415b1487264ce9eb2` / [GREEN #38985936321](https://github.com/heathsanchez/test/actions/runs/38985936321), original RED #38985804466 retained (PARI warnings misclassified). 

## Why test this?
Candidate 876 yields two coefficients satisfying c*b²=-27 mod p. V5 proves prime group order for the numerically larger root b_hi, but the *smaller root* b_lo has composite order (factor 3). At selected candidate 1842, the published P-256 b is the smaller root and has prime order. Thus a consistent b-root choice could explain skipping 876 WITHOUT hypothesizing some unknown preference for index 1842.

## Primary competing rules (frozen, do not introduce post-hoc scores)
- R_min: choose min(b,p-b).
- R_even: choose the unique even representative of {b,p-b} for odd p.
- R_mod4: for p ≡ 3 mod 4, choose pow(-27*inverse(c), (p+1)//4, p) as the literal textbook modular square-root implementation (not necessarily the smaller root). For other primes, report NOT_APPLICABLE instead of forcing an invented root convention.
- R_general: no universal sign rule; selecting a root may depend on implementation version, curve family, epoch, or other historical state. This is the honest baseline.

## Inputs, controls, and outcome
- Source: original NIST public constants for P-192, P-224, P-256, P-384, P-521. Fetch **p**, published **b**, published seed from read-only source via OpenSSL `openssl ecparam -name <curve> -param_enc explicit -text -noout`, and confirm p,b,seed reproducibly. Fetch c by generic seed SHA-1 construction (rightmost p_bits-1 bits of chained SHA1((seed + j) mod 2^160) chunks, enough to reach p_bits-1). Source NIST 1998 Appendix and NIST SP800-186 2023; source 2023 is retrospective, not history authentication.
- Test each of the 5 published b values for relation c*b² ≡ -27 mod p. If the formula differs for a specific curve or the extraction is incomplete, fail closed/UNKNOWN for it; do not quietly omit a failed curve.
- Apply R_min, R_even, R_mod4. Count exact matches on each of five accepted curves. If R_min or R_even fails on any accepted curve, reject it as a **uniform** NIST root convention, even if it fits the 876/1842 local puzzle.
- For candidate 876, check R_min/R_even/R_mod4 choice of root against prime-order V5 result. For accepted 1842 check same rules choose published b. Any rule that rejects 876 (composite choice) AND accepts 1842 (prime published b) is a LOCAL candidate; it is not historical evidence. A global rule requires prospective acceptance across P-192, P-224, P-384, P-521; a mere match is a compatibility check, NOT proof of actual use.
- Standardized source constants and V5 both-b arithmetic are controls. No *new* group counts for P224/P384/P521 are performed. No claim of security issue, private-key attack, actual historical NSA method, or unrestricted autonomous genesis.
- Independent GitHub CI check exact receipt after native execution; archive source/output and failures. Epithet: WIN=SOURCE-COMPATIBLE_RULE_ONLY, REJECT=UNIFORM_RULE_FALSIFIED, UNKNOWN=HISTORICAL_SELECTION.
- Do not run a second hypothesis search after seeing failures without a newly frozen V7 criterion; no opportunistic extension to 1997 FreeLIP seeds.
