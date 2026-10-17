# V10 PRE-RESULT PROTOCOL CORRECTION — near-primality is not prime-only

This amendment was committed **before** computing any V10 PARI or native FreeLIP result. Preserve the original V10 freeze as historical provenance; this narrower statement supersedes its overbroad first-acceptable interpretation.

Important correction: X9.62-1998 Annex A.3.2 allows **nearly prime** orders `u=h*n` where `h` is smooth and `n` is a sufficiently large prime. The V9 `ellsea(E,1)` scan stopped early on curves with small torsion. Those were correctly rejected for a *whole-group prime* test but were **not proven inadmissible under 1998 near-primality**.

Therefore, candidate 77 is only the first **whole-group prime order** known from V9 (225-bit), NOT necessarily the first 1998 ANSI-eligible curve. In particular, don't claim ANSI first admissible = 77 before testing every earlier complete order and its cofactor.

## Additional frozen decisive census

- Exactly original V9 indices **1 through 77 inclusive**, no parameter changes after learning results. Reuse the source-frozen P224 seed generation, SHA1-to-c, and ±b isomorphism quotient. This set contains **48 coefficient-eligible curves** and 29 nonresidues. Independent source: V9 candidate-table SHA256 `6ae4d488768e622d5ff307ca7bb1af2c2b7d10c0f6935fac2e7107eac1fa5d22`.
- Use PARI/GP complete `ellsea(E,0)`, NOT `ellsea(E,1)`, to obtain an exact cardinality for every one of the 48 eligible curves. A zero/errors/incomplete row -> `UNKNOWN_RESOURCE_OR_TOOL`, never reject. Require exact published/archived order at 77. Run <= 25 minutes on native GitHub runner with source and raw logs.
- Fixed original-standard instantiation: `rmin` strictly greater than both `2^160` and `4*sqrt(p)`, `lmax=255` (the ANSI illustrative guide), MOV threshold `B=20`, nonanomalous trace `u!=p`.
- For each complete `u`, factor out **every prime factor <=255 with multiplicity** and set `h` to their product. Remainder `n=u/h` must satisfy rigorous PARI `isprime(n)==1`, `n>2^160`, `n^2>16*p`, `u!=p`, and `p^k % n !=1` for `1<=k<=20`. h=1 allowed. This checks *only the declared ANSI near-primality instantiation*. Do not call exact `lmax=255` historically used; it is a predeclared example from ANSI.
- Determine minimum admitted prefix index, if **all** earlier case labels complete. Freeze positive controls at 77 whole-prime and 7026 official order (latter already V9 proven, not rerun in the 48-cardinality gate). Independently compare exact n against archived results at 77.
- In separate 1997 FreeLIP native C test, assess only `zprobprime(n,1),zprobprime(n,5),zprobprime(n,12)` on **five preselected known prime orders** (77,777,1485,5736,7026) plus composites `3*n_77`, `3*n_7026`. Reproduce its state separation from `lrand48` through native control. This tests one library's API and RNG independence, *not* the NSA's unknown generator or 1998 near-prime validation.
- If a new early near-prime with smooth h is found, it **supersedes** any suggestion that 77 is the first ANSI-compatible seed. Do not call it historical rejection or historical practice.
- Original V10 statements not mentioning this alternative are retained as negative lineage but no longer decision authority. Preserve all old V9 evidence. No ECDSA security implication, no claimed AI discovery advantage.
