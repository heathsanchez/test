# V6: root-choice policy test across five standardized curves

Status: **WARRANTED_BOUNDED_LOCAL until independent GitHub Actions qualification.** Source pre-freeze [`ac022b760f`](https://github.com/heathsanchez/test/commit/ac022b760f5bdd785b5e127c2814d4214c336779). Parent V5 [CI #38985936321](https://github.com/heathsanchez/test/actions/runs/38985936321): skipped P-256 seed 876 gives one prime-order b-root and one composite-order b-root. Original V4 [CI #38985275415](https://github.com/heathsanchez/test/actions/runs/38985275415) reconstructs both seeds and all coefficients exactly.

## Result (source-derived exact native OpenSSL parameters)

For P-192, P-224, P-256, P-384, and P-521, independently read original standardized p, b, 160-bit seed using `openssl ecparam -name ... -param_enc explicit -text -noout`. Each of the five returned b values satisfies the independently constructed SHA-1 c relation `c*b² ≡ -27 mod p`, with a=-3. Results are recorded, including all full p/seed/b/c/source output hashes, in `V6_RESULTS.json`.

- `R_min = min(b, p-b)` matches **3/5** published choices, but fails P-224 and P-384. Thus a single universal *numerically smaller b* convention is falsified across published NIST curves.
- `R_even = even(b)` matches **2/5**, failing P-192, P-256 and P-384. Thus a uniform even root convention is falsified.
- For the four prime fields p≡3 mod4 (P-192, P-256, P-384, P-521), the direct exponentiation root `pow(-27/c,(p+1)/4,p)` matches **4/4** published b choices; P-224 is **NOT_APPLICABLE** (p≡1 mod4). This rule chooses the **prime-order HIGH root of candidate 876**, and therefore does **not** explain why 876 was skipped if the historical program used it with first-acceptable selection.
- Locally for P-256 only, `R_min` chooses the composite-order lower b of 876 and the published prime-order lower b of 1842, so it **can** rationalize a first-success selection. But its failure across P-224 and P-384 means it cannot be promoted to a uniform generator convention.

## Epistemic boundary

These are exact cross-standard mathematical compatibility/falsification tests, **not** historical execution witnesses. The discovery of a common b-root selected by exponentiation is **consistent**, not historical authentication. The 1998 standards do not bind the historical programmer's square-root choice, and root choice could differ by curve, platform, or code version. Original reason for index1842 selection **UNKNOWN**; original P-256 G origin **UNKNOWN**. Do not claim crypto weakness or an independent general historical generating law.

## Next decisive evidence

Locate dated ANSI/NSA original curve generator C source or execution trace specifying modular square root, root sign/order choice and stop conditions, rather than inventing another post-hoc selector. Alternatively, preregister cross-curve earlier viable skip tests, with accepted point counts and both roots, before reading decisions. No new universal claim without independent provenance.