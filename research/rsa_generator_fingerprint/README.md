# Historical RSA generator fingerprint: retrospective bounded diagnostic

**Status: EXPLORATORY / CANDIDATE, NOT a cryptanalytic breakthrough.** This branch deliberately preserves the negative and UNKNOWN results. No unfactored RSA challenge has been factored; no original RSA DSP prime-generation software or random seed has been identified.

## Current objective

Find a *source-specific* and predictively validated low-compute mechanism for the original RSA challenge generation, if one exists. Test against known factors before touching RSA-270. Avoid reproducing the already-published generic high-bit and modulo-3 constraints as though they were vulnerabilities.

## Evidence boundaries

- Primary contemporaneous challenge-list text: https://www.ontko.com/pub/rayo/primes/rsa_fact.html. It names the RSA DSP/Motorola 56000 arithmetic board and requires both primes to be 2 modulo 3. Its document date does **not** independently date the creation of every original modulus. RSA-155/RSA-232 were explicitly added in 1997.
- Pinned factors/corpus in `data.json`: https://github.com/Hermann-SW/RSA_numbers_factored/blob/main/RSA_numbers_factored.js (Git blob `53d375e582daa25ba7938a49f193fb0b7d99389a`). Independently validate all 18 solved original-list products and their factor residues; compare selected original checksums RSA-100/RSA-250/RSA-270.
- Historical-era comparison *only*, **not established as the DSP implementation**: RSAREF-like RSAEuro code https://github.com/mort666/RSAEuro/blob/master/source/r_keygen.c and https://github.com/mort666/RSAEuro/blob/master/source/prime.c, which draws a random candidate and advances in steps of 2 until probable prime, then checks exponent compatibility.
- Related prior art: https://doi.org/10.3390/info17090847 reports high-bit/residue construction-family signatures but no reduced factoring resistance.

## Smallest executable tests

`python3 replay.py` compiles `prime_context.c` using GCC/GMP and reruns:

1. **Exact batch GCD** over 56 catalogue moduli (1,540 unordered pairs); observed nontrivial common divisors: **zero**.
2. **Prime-gap fingerprint**, using 32 published known prime factors of 16 original challenge numbers. RSA-155 and RSA-232 (1997 additions) are excluded from the main source-cohort statistic. For each actual prime compare the gap to the preceding prime with 12 nearby eligible primes on either side (also 6 and 24 controls), conditioned on factor congruence 2 modulo 3.
3. Source-conditional alternative **scan+2**: sampled random start advances by 2 to *any* prime, then rejects resulting primes not 2 mod 3. Sampling probability proportional to the preceding all-prime gap.
4. Alternative **scan+6**: random start advances in the eligible residue class; sampling probability proportional to preceding eligible-prime gap.
5. Uniform-acceptance alternative: sample directly from eligible primes with equal weights.

Local pilot: at 12 neighbours per direction, mean observed all-prime gap/log(p) 1.237 vs matched uniform 0.995 (one-sided exploratory p around 0.083); scan+2 expected 1.881 (lower-tail p around 0.0004); mod-3 gap/log(p) observed 2.488 vs scan+6 expected 3.689 (lower-tail p around 0.0014). Similar separation at radii 6 and 24. Deterministic CI replay results are source-bound **retrospective diagnostics**, not independent prospective discovery. Control prime neighbours are screened with GMP 25-round probable-prime checks; this is not an independent primality-proof oracle.

## Causal interpretation and residual

The simple increment-scan models are poor fits to the observed prime-gap distribution in this local control design. **Do not promote** that to the claim that RSA chose a direct-rejection sampler, that RSAEuro was used, that the actual RNG was weak, or that RSA-270 is easier to factor. The relevant generator call path, RNG state/entropy, and independently withheld generator predictions remain **UNKNOWN**.

**Cheapest consequential next experiment:** obtain historically authenticated RSA DSP generation/seed source or operational records; before inspecting target factors, freeze one exact generator hypothesis and test on known-factor challenge primes held out from its derivation. Only then evaluate whether it yields a bounded, computationally feasible prediction for RSA-270. Without the original call path, new statistical fitting or seed sweeps are unlikely to provide attributable evidence.

**Why this matters for MathGraph:** reused MSI's source-relative identifiability boundary and evidence-governed selection, rather than adding a new capability framework. No new factoring law or general AI advantage is established.
