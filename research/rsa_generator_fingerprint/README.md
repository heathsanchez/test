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

## V2 — exact 8/16/24/32-bit affine word-stream falsifier (2026-10-17)

**WARRANTED LOCAL EXACT, bounded negative. Independent GitHub Actions qualification has NOT yet been verified.** New [source](affine_word_stream.py) and workflow extension in this branch; [code commit dac00bf](https://github.com/heathsanchez/test/commit/dac00bfde895176100e2d57f82520a69ce3abca3); [workflow commit 2efad37](https://github.com/heathsanchez/test/commit/2efad37bc56cffd8088b7c47d029a446c962d713). Python local execution and a separate BigInt JavaScript implementation reading the pinned `data.json` agree exactly.

A full-output affine LCG `x[i+1] = a*x[i] + c (mod 2**w)` necessarily satisfies `(x2-x1)**2 = (x1-x0)*(x3-x2) (mod 2**w)` for every four consecutive outputs. Check **all bit-phase alignments** in the interior of each already-known prime factor (exclude boundary words). Original 1991 cohort: 32 primes from 16 challenges, 7,768 tested 8-bit windows with 32 incidental matches; **6,232 16-bit / 4,696 24-bit / 3,230 32-bit windows with ZERO necessary-invariant matches.** Separate 1997 RSA-155/232 primes: 1,092 / 900 / 708 / 516 windows with 7 / 0 / 0 / 0 hits respectively. Synthetic planted full-period LCG data pass in each width. Thirty-two size-/high-prefix-/residue-matched synthetic-random controls per width place isolated 8-bit matches at chance-scale. The synthetic controls are not necessarily prime and are NOT tests of unknown RSA factors.

**Inference:** Direct concatenation of consecutive, complete, unaltered affine-LCG state outputs with width 16/24/32 bits is incompatible with these solved factors (indeed every sampled interior 4-word window fails the required identity). This **does not** exclude truncated output, skipped states, hashing/whitening, interleaving, variable chunking, other generators, or a real generator weakness. It does not identify historical firmware, seed entropy, or factors of RSA-270.

**Source distinction:** The [1990 Dussé–Kaliski DSP56000 library paper](https://doi.org/10.1007/3-540-46877-3_21) documents cryptographic *arithmetic and implementation*, not the original challenge-list seed/prime-generation trace. A 24-bit DSP word is motivation to test an explicit candidate, **not evidence** that the random generator produced 24-bit raw words. Further blind bitstream hypotheses offer little leverage absent authenticated 1991-era host/application generator code.

**Residual unchanged:** source-specific prime-generation/RNG call path and entropy provenance UNKNOWN; cross-instance held-out factor prediction UNKNOWN; RSA-270 factors UNKNOWN. Next cheap decisive experiment: recover date-authenticated generating software or operational records and test one frozen full predictive procedure against previously undisclosed solved factors. No claim of weakened RSA security or algorithmic breakthrough.

## V3 — source-provenance gate and bounded RSA-270 special-power screen (2026-10-17)

**ORIGINAL GENERATOR UNKNOWN.** The contemporaneous original decimal challenge description records the 1991–94 RSA DSP / Motorola 56000 board and both primes congruent 2 mod 3; it does not describe the random source, prime selection call path, or seed records ([original challenge list](https://www.ontko.com/pub/rayo/primes/rsa_fact.html)). A later documented **2001-era** BSAFE 4.0 generation process seeded with ComScire QNG bytes pertains to *separate bit-labelled challenges* and must **not** be used to infer the RSA-270 source ([2026 forensics paper](https://doi.org/10.3390/info17090847)). Dussé–Kaliski's 1990 Motorola paper describes arithmetic performance, not authenticated source for the generation path. Targeted archival/web search located no original host generator source. Absence in this search is **UNKNOWN**, not proof that no archive survives.

**WARRANTED LOCAL EXACT, SMALL BOUNDED NEGATIVE:** The separate [special-power probe](special_form_probe.py) asks whether RSA-270 has a simple form \(N=c b^e+r\), where \(2≤b≤4096\), \(1≤c≤64\), \(4≤e≤1024\), \(|r|≤2^{64}\). For each 262,080 (b,c) combination, exact monotone comparisons locate bracketing powers. Evaluated **524,160** closest expressions and found **0** admissible representations. The smallest absolute remainder was **877 bits**; 2/2 planted special-form controls passed. [Code commit abf8ec9](https://github.com/heathsanchez/test/commit/abf8ec9f7f5c7ea758fad44072fe7d3b2cd4f367); [workflow change 653a5a1](https://github.com/heathsanchez/test/commit/653a5a19727f7f824e30ed53a6e87e2873508462). Independent GitHub Actions qualification **NOT YET VERIFIED**, despite local replay. This does not reject arbitrary SNFS polynomial selection, GNFS improvements, or a weak historical RNG.

**Decision / stop condition:** Do not continue blind seed-grammar sweeps or interpret the 32 solved original prime factors as predictive for RSA-270 without evidence of a shared generator state. Either obtain authenticated host-side generation source/entropy records and preregister a held-out exact prediction on already-solved factors, or pursue a separately frozen genuine algorithmic result against untouched semiprimes with matched established factoring baselines. Otherwise park the RSA-270 low-compute shortcut as UNKNOWN; do not silently spend GNFS-scale compute. No factor found.
