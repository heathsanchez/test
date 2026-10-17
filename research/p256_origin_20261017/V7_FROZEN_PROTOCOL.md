# P-256/V7 — 1997 FreeLIP zsqrtmod source-selector test (frozen before computation)

Date: 2026-10-17 NZ. Parent qualified V6 head `526448074c3d5fe45aebad38c57c42069f0d3cd5`, GitHub Actions #38986335266. Original V1-V6 results remain unchanged.

## Historical source pin and declared counterfactual

Use `lrobot/freelip` mirror commit `00898a4814d2cc1244bf348682be6ed10dda35f0` (2019 mirror containing FreeLIP v1.1 dated 21 July 1997), `lip.c` Git blob `a86ce8ae5be49e0f35999a2c87f52e1718ebdb81`, function `zsqrtmod` around lines 11734-11825; `lip.h` Git blob `080cda8aec8c0939348452ea3beb9f1afad845ef`. This is *historically available* routine, NOT evidence that NSA or X9.62 code used it.

Source algorithm: for p mod4=3 return `pow(a,(p+1)//4,p)` if squared result equals a (else 0). For p mod4=1, factor p-1 = odd q * 2^r; choose first odd prime n≥3 with Jacobi(n,p)=-1, initialize z=n^q modp, x=a^((q-1)//2)*a modp, b=a*(a^((q-1)//2))^2 modp, y=z, then iterate smallest m such that b^(2^m)=1; choose t=y^(2^(r-m-1)), update x,b,y,r as original code, return x when b=1. The native function uses `zjacobis` and its documented signs; execute the original source in CI to verify the translation for at least P224, standard P256 and relevant mutants.

## Single falsifiable research question

Does the unmodified 1997 FreeLIP `zsqrtmod` root-selection operation reproduce the published b choice of each five NIST prime curves, and which root does it select for the qualifying skipped P-256 candidate 876?

## Frozen tests and outcomes

1. Use the existing source-pinned V6 p,c,b input values for NIST P-192/P-224/P-256/P-384/P-521. Do not relabel roots after output. Compute `a_root=-27*inverse(c) mod p`; compare returned b DIRECTLY to published b (not ±). Confirm each equation and each root is valid, and run independently derived Euler/Legendre & reference Tonelli for P224, plus exact OpenSSL source checks.
2. Use V4/V5 pinned candidate 876 c and exact b_hi prime / b_lo composite status. Compare `zsqrtmod` result to both values and independently qualified V5 order statuses. No point-count rerun in V7.
3. Use deterministic invalid square-input mutant and zero-input control. Native FreeLIP comparison is required before promotion from Python to independent-exact-source compatibility; CI should fail if results differ. Record exact version/compile flags and output hashes.
4. A 5/5 root sign match is a mathematical source-compatibility **candidate**, not historical proof of the original program. If candidate 876 returns b_hi prime, this source routine does not explain its rejection under hypothetical first-acceptable selection. If returns b_lo composite, the local first-acceptable explanation remains possible, but requires historical provenance and cross-curve validation. If any accepted curve disagrees, report falsification of **uniform** FreeLIP zsqrtmod as an explanation, without excluding other routines.
5. Do not reinterpret ANS X9.62 standards as specifying this exact library; standardized b alone does not identify the software. P224 earlier candidates are the reserved prospective target; do not fit to those candidates after examining this test. For a future P224 point-count experiment freeze its indices/rules separately before running.
6. Strict epistemic states: source compatibility versus actual historic use versus P256 base-point origin versus cryptographic security kept separate. Strong equal-info agent baseline NOT_RUN.

Independent artifact must include executable source, JSON results, original source hash, Python-vs-native transcript, and exact GitHub Actions run. No upstream writes, no mainline merge, no new general framework.