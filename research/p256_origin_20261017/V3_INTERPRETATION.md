# P-256 origin V3 — source-meaning separator and bounded negative

**Status:** V1/V2 remain independently qualified. V3 is WARRANTED_BOUNDED_NEGATIVE only after exact-head GitHub Actions replay passes. The historical P-256 base-point origin remains UNKNOWN. No ECDSA weakness, private-key recovery, or model-advantage claim.

## Historical finding

The original ANSI X9.62 (1998) algorithm deterministically derives the *curve coefficient* from SHA-1 of the published curve seed. It **does not** provide a verifiably random derivation of the *base point G* from that seed. Instead G is sampled as a random on-curve point of the correct order. FIPS 186-2 Sec. 1.5 permits any point of order n. The later 2005 verifiably-random G procedure cannot retroactively explain 1997 point choice.

Primary sources: [Anthropic 2026-10-16](https://www.anthropic.com/research/ecdsa-curve-origins); [original FIPS 186-2](https://csrc.nist.gov/files/pubs/fips/186-2/final/docs/fips186-2.pdf); [ANSI X9.62 algorithm analysis](https://dissect.crocs.fi.muni.cz/standards/x962); [1997 FreeLIP 1.1 archive](https://github.com/lrobot/freelip/tree/00898a4814d2cc1244bf348682be6ed10dda35f0).

## Freeze and controls

V3 grammar frozen before implementation at [commit 9905639d](https://github.com/heathsanchez/test/commit/9905639d6e834e126a6b778fbcc2a16ef8d443a8). Qualified V2 [green #38978950149](https://github.com/heathsanchez/test/actions/runs/38978950149) remains unchanged. Exact controls: reproduce NIST P256 SHA1-derived c and b*b*c congruent -27 modulo p; published G lies on curve; recovered lrand48 timestamp yields original P-256 seed candidate 1842; native glibc lrand48 outputs agree 20/20; actual 1997 FreeLIP prime239v1 generator x recovered from seed 20420 at offset 29 and 26-bit limbs; 30-bit reference outputs agree; positive constructed hits physically recovered for each of the three newly searched families.

## Reproducible local and independent-code census

| Frozen source-derived candidate family | Exact windows | Gx matches |
|---|---:|---:|
| SHA-1 curve-SEED increment, adjacent hashes 0..4095, six candidate projections | 24,570 | 0 |
| Timestamp-seeded lrand48 top8/low8 bytes; 80,000 samples each; lengths 32/33/40/64, two byte orders, reduction mod p | 1,279,340 | 0 |
| FreeLIP PRNG seeded from five published-SEED presentations; NBITS 26/30/62; native large-bound limb widths; first 512 outputs and two orders | 15,120 | 0 |
| **Total V3** | **1,319,030** | **0** |

Candidate windows overlap. The fact that SHA-1 explains curve coefficient c is WARRANTED_BOUNDED; using it to produce G is only a tested speculative hypothesis. None of these negatives identifies the original sampling generator. The local source+results bundle contains a separate full scanner; the GitHub scanner is a compact independent reimplementation. P-224/P-384/P-521 base points withheld.

## Correct next experiment

Find the **original 1997-1998 elliptic-curve parameter generator call path** or contemporaneous run logs, binary/source, or verifiable testimony specifying the random point function and PRNG state used for G. If unavailable, pivot to a distinct *selection rule* investigation: source-reconstructed accepted NIST P-256 candidate 1842 versus skipped valid candidate 876, with independent P-224/X9.62 skipped candidates as constraints. Freeze rule hypotheses before inspecting those outcomes; preserve identifiability-UNKNOWN. Do not grow the unrelated PRNG seed sweep and claim progress. Strong matched AI comparator NOT_RUN. General developmental L7 NOT_RUN.
