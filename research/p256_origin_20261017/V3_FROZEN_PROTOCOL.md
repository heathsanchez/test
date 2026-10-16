# P-256 V3 — source-derived curve-seed / base-point mechanism separator (freeze before implementation)

**Date:** 2026-10-17 (NZ). **Parent qualified head:** `heathsanchez/test@f56f2ceb50f2327da10654167819d8324c221043`, V2 green Actions `38978950149`. New isolated branch; V1/V2 immutable and not reinterpreted.

## Historic sources and exact interfaces

- Anthropic, *Claude reveals ECDSA curve origins*, 2026-10-16: `https://www.anthropic.com/research/ecdsa-curve-origins` (P-256 seed reproduced from `srand48(1997-08-16T01:52:34Z)` at candidate 1842, 20 one-byte PRNG draws per candidate; six May 1997 Gx reconstructed from FreeLIP).
- FIPS 186-2 (2000), `https://csrc.nist.gov/files/pubs/fips/186-2/final/docs/fips186-2.pdf`, Sec 1.5 states any point of order n may be sample G; original P-256 seed, curve coefficient c, b, and point coordinates published. NIST curve coefficient uses 1998 ANSI X9.62 SHA-1 seed derivation, not a mandated seed-to-G formula.
- ANSI X9.62-1998 Annex A.3.1 and D.3.1: random x in [0,p), test x^3-3x+b for modular square-root, then cofactor handling. Confirmed in `https://dissect.crocs.fi.muni.cz/standards/x962`. The 2005 verifiably-random G algorithm is anachronistic to the 1997 construction.
- FreeLIP 1.1 source mirror `lrobot/freelip@00898a4814d2cc1244bf348682be6ed10dda35f0`, `lip.c` Git blob `a86ce8ae5be49e0f35999a2c87f52e1718ebdb81`, `lip.h` Git blob `080cda8aec8c0939348452ea3beb9f1afad845ef`. `zrstart`, `zrandom`, `zrandomb` are distinct from C `lrand48`; V1/V2 tested several integer/time seeds and direct 31-bit windows but NOT the three finite classes below.

## Exact target

Published P-256 `p=FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF`, `Gx=6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296`, `Gy=4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5`, `b=5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B`, `seed=C49D360886E704936A6678E1139D26B7819F7E90`, `c=7EFBA1662985BE9403CB055C75D4F7E0CE8D84A9C5114ABCAF3177680104FA0D`.

## Frozen candidate families (no post-outcome widening)

**H_SHA1_1998**: First independently reproduce EXACT NIST `c`: `SHA1(SEED+i)` for `i=0,1`, with `c = int(digest0||digest1) mod 2^255`, and verify `b^2*c % p == -27 % p`. Then for `i=0..4094`, search exact P-256 Gx for each of SIX explicitly typed candidate transformations of `SHA1(seed+i)`, `SHA1(seed+i+1)` interpreted as 320-bit `AB` or `BA`: `full320 % p`, `rightmost256`, `leftmost256` (two concat orders × three transforms). **This is speculative**: ANSI source warrants SHA-1 as curve coefficient generator, NOT as basepoint generator. Its purpose is to separate this plausible but *unasserted* carryover hypothesis. A match still needs full-point/provenance checks.

**H_LRAND_BYTE_MOD**: 1997 timestamp seeded `lrand48`. Derive per-call top8 via high byte of state (`state>>40`, as recovered seed generator), and low8 of standard `lrand48` output (`state>>17 & 0xff`) as an alternate C sampling idiom. For offsets in 0..79,999, candidate byte widths 32,33,40,64, byte orders big and little. For each contiguous candidate, interpret as integer and reduce modulo published p before Gx comparison. Search windows counted EXACTLY; run covers published seed position 1842*20, but not all possible source sampling. Check one planted positive in each stream with known nonzero offset. Note direct raw top8-byte equality had already been checked in V1; transformed modulo >32-byte candidates and low8 path are new.

**H_FREELIP_SEED_FROM_CURVE_SEED**: Seed the exact FreeLIP 107-bit state by `int.from_bytes(20-byte curve seed, big)`, `little`, `int.from_bytes(SHA1(seed),big)`, and the top and bottom 32-bit unsigned integers of the seed. These are FIVE finite source-derived seed presentations. For each, test `NBITS=26,30,62`, first 512 accepted `zrandom(2^NBITS)` outputs, both most-/least-significant-first contiguous limb packing and native large-bound limb counts of `ceil(256/NBITS)+1` (11,10,6), reduce modulo p. Keep FreeLIP rejection semantics exact and report actual rejections. This is a constructed cross-library hypothesis, not independently established historical practice.

## Required independent controls, verdicts, and stopping boundary

- Reproduce known published curve seed exactly as `lrand48 top8` candidate 1842 and NIST `c` and `b^2*c ≡ -27 mod p`; SHA-1 RFC / hashlib known-answer check.
- Reproduce one published actual FreeLIP 1997 x from the existing V1 historical positive; check the newly written FreeLIP sampler against independent previous V2 source first-20 outputs for a named seed. Check P-256 G lies on curve and has published y value; optional full-point nG independent primitive if practical, but prior qualified verification exists.
- Plant recoverable positives for every *new* scanner family (SHA concat, byte-mod each stream, FreeLIP big-seed). If calibration fails, report APPARATUS_RED; do not interpret any negative.
- Exact exhaustive enumerations inside these bounded candidate grammars only; preserve grammar counts, distinct underlying generator states, any overlaps, source hashes, and verified negative/positive artifacts. Zero match => `WARRANTED_BOUNDED_NEGATIVE` **after independent CI**, `UNKNOWN_HISTORICAL_ORIGIN` always. Hit => `CANDIDATE_NUMERICAL_FIT` pending independently verified full-point y selection and prospective other NIST base-point tests, plus historical source evidence.
- No claim of ECDSA break or private key weakness, no claim of unique historical method, no autonomous method/selection economic advantage; no independent strong LLM comparator is planned. P-224/P-384/P-521 basepoint targets remain sealed until P-256 hit. Do not overstate number of independent hypotheses from millions of overlapping stream windows.

If all three finite source-linked bridges fail, the next high-value action is ARCHIVAL provenance discovery (original circa-1997 ECC generator call path / contemporaneous source or independent logs), or pivot to the skipped viable 876-vs-1842 *selection-predicate* question with actual sampled candidate outputs, NOT another blind seed-range enlargement.