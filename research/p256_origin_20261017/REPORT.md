# P-256 base-point origin — exact bounded provenance experiment

**Date:** 17 October 2026 (NZ); all measurements are post-source, not blinded/preregistered.  
**Result:** `WARRANTED_BOUNDED_NEGATIVE` **locally** within declared search grammars; independent external GitHub CI status must be checked before adding a CI warrant.  
**Unresolved:** the true historical process for the P-256 generator G. No flaw in ECDSA or private-key attack is suggested.

## Objective

After Anthropic's 16 October 2026 discovery that 14 standardized curve *seeds* came from `lrand48` and six 1997 base points came from the FreeLIP/early-NTL generator, test whether the still-unexplained NIST P-256 generator point G is produced by an exact, restricted, historically plausible member of the same generator families. Distinguish direct numerical reproduction from historical provenance.

Primary source: https://www.anthropic.com/research/ecdsa-curve-origins

## Independently rechecked controls

- **6/6** source-published FreeLIP base-point x-coordinates exactly reproduced in Python with the published number of rejection-sampling attempts.
- **14/14** source-published `lrand48` curve seeds exactly reproduced (ten prime, four binary, using the publication's timestamp / candidate positions and its tentative binary half-clock convention).
- P-256's official x/y parsed from installed OpenSSL explicit named-curve parameters. Independently checked G satisfies its curve and `[n]G = identity` using pure-Python scalar multiplication.
- The independent compiled C++ FreeLIP enumerator recovered the **actual prime239v1** published Gx at `seed 20420`, `low26`, 11 limbs, most-significant limb first, starting stream offset **29**. It also recovered a Python-generated synthetic P-256-shaped positive at seed 20000, stream offset 7.

## Original negative: exhaustive **within the explicitly declared grammar**

C++ exact integer recurrence: `state <- state * pow(3,121,2**107-1) mod (2**107-1)` from integer seed; derive either low26 or high26 bits of each consecutive state, pack **10 or 11** 26-bit limbs per coordinate in both orders, reduce modulo the published P-256 prime, compare exactly against its standardized Gx. To overcover the original seven-draw warmup/first-on-curve-stop procedure, check **every contiguous** limb window in the first 192 generator outputs (not just fixed seven-draw-aligned windows). This covers warmups 0..15 and the early rejected candidates of the standard 11-limb path, among other offsets.

1. Seeds 0 through 65,535, inclusive: **95,682,560 exact windows**, zero matches.
2. Seeds equal to every second of **1997-08-15 01:52:34 UTC through 1997-08-17 01:52:34 UTC**, centered on Anthropic's recovered P-256 `lrand48` timestamp: **252,289,460 exact windows**, zero matches.
3. Total across nonoverlapping bounded seed regimes: **347,972,020 exact windows**, zero matches.

Separately, the historical `lrand48` byte/word streams were checked for *literal contiguous* raw Gx, reversed Gx, Gy, reversed Gy or uncompressed G using the five published prime-curve timestamps and 150,000 bytes each of the `state >> 40`, 31-bit-big-endian and 31-bit-little-endian representations. Zero matches. This is much narrower than checking candidates transformed by hashing, modulus reduction, scalar multiplication or rejection sampling.

## Scope and limitations

`NO_EXACT_MATCH_IN_DECLARED_GRAMMARS` is **not** a historical nonexistence result. Untested possibilities include: other RNGs, different FreeLIP seed ranges or output positions, 32-bit limbs, different state initialization, x-coordinate hash-to-curve, point scalar multiplication, point compression and candidate-order guards, as well as algorithms absent from the source-derived grammar. An exact matching generating program still would not establish it was historically used without independently authenticating provenance.

The scan is a *post-publication observational probe*, not a preregistered blind breakthrough, not open-ended autonomous constructor genesis, and not evidence of an advantage over an equally informed search implementation. No genuine new recovered point-origin algorithm was found.

## Reproduction

Requires Python 3, OpenSSL (`openssl ecparam`), GNU C++17 and Boost multiprecision headers (`libboost-dev`), no Python package installation or network.

```bash
python3 p256_origin_probe.py --out result.json
```

The Python driver compiles `p256_scan_freelip.cpp` itself if needed, executes both full exact searches, reproduces historical controls, checks compiled historical and synthetic positives, and emits all search bounds, checksums, status and negative lineage to JSON. Typical local exact FreeLIP enumeration takes roughly 22 seconds on this CPU; no promise of CI timing. The `RESULTS.json` archived in this branch records an executed local outcome, while any separate green CI run supplies an independent environment reproduction if it completes.

## Research consequence / next smallest useful experiment

Do **not** blindly widen the same integer seed sweep. Read and pin original circa-1997 FreeLIP/NTL and ANSI X9.62 generation implementations, enumerate the **actual distinct point-construction programs** permitted by their semantics (including 31/32-bit limbs, `zrandomb`, `zrandom`, state initialization and rejection), and use source-derived constraints to choose minimum distinguishing tests against the P-256 Gx/Gy pair. Preserve distinct surviving methods and scope-relative negatives; if the grammar is exhausted and an actual source witness lies outside, use the verified MSI/VDN expansion path. Untouched P-224/P-384/P-521 base-point targets are the prospective validation set. Compare to an equally informed fully executable baseline before attributing any search improvement to MathGraph.

**Other ROS science programs remain unaffected** (UDM G2, kernel performance, MathGraph Check production, etc.).