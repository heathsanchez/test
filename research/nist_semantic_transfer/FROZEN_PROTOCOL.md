# Source-semantic transfer V4 — frozen before implementation

## Objective
From the original Nature v1 PDF source previously used in V3, recover the 1:2 fine-structure multiplicity ratio, two experimental frequencies with reported uncertainties, and signed HFS correction from original SOURCE TEXT. Do not let the human manually enter (1/3,2/3), experimental frequency values, or HFS offset for the V4 calculation. Use the SAME exact affine library qualified in V3.

## Fixed source and critical limitation
- Original Nature v1: https://arxiv.org/pdf/2602.14980v1 exact PDF SHA256 758181d221327797c87758f17cabfece0632a9f0394138da0c9ebac10d4b25f4.
- Original Bullis v1: https://arxiv.org/pdf/2604.26401v1 exact PDF SHA256 79b0e291be20049b5df9bf895722c6b39a4c2e68e5e17bc86669de5a6e0ebe7e.
- Both papers have ALREADY been seen and studied by the human author of the parser. This is NOT a blinded independent third-paper transfer nor autonomously invented method. Numeric coefficients, source-specific frequency literals, and expected original output may only appear in independent test specifications, never in the parser or derivation logic.

## Precommitted success conditions
1. The original immutable Nature PDF must be re-fetched and byte-pinned, verified before inspecting extracted text.
2. The only source-ratio allowed is a natural-language fine-structure multiplicity ratio of A:B. The unrelated spectroscopy laser-power 2:1 ratio in the same source is a required negative control, and cannot qualify the source ratio. Report source span.
3. Extract two large observed source frequencies and their reported standard uncertainties from the original measurement section, associate them with 1/2 and 3/2 respectively from source context. No target output search to choose a convenient input or weight. Ambiguous label map returns UNKNOWN_SOURCE_SEMANTIC_BINDING.
4. Extract a signed hyperfine frequency correction with reported uncertainty from an HFS-context clause and check units. Missing or unsigned correction fails closed. Report source span.
5. General ratio-to-weights law (a,b) maps to (a/(a+b),b/(a+b)), both >=0 and sum=1, independent of target value. Execute same frozen V3 affine kernel; independently check with Decimal. Only AFTER calculation compare with original Eq 8 target extracted separately from paper.
6. Deliberately flip/source-swap ratio, HFS sign, one measured value; inject unrelated 2:1; corrupt original source byte. Reject or report changed outcome, never 'WARRANTED' for altered original.
7. The source's original published 0.48 kHz centroid uncertainty cannot be inferred from just the input marginal uncertainties without covariance; return UNKNOWN, not an invented RSS equality.
8. Output qualified only for explicitly extracted original source, not general scientific parsing or another user paper.

## Verdict and next boundary
Pass: WARRANTED_BOUNDED_SOURCE_DERIVED_RATIO_AND_OFFSET, with human-authored reusable semantic grammar. Any failure: UNKNOWN or specific text representation obstruction. Not L7 method genesis, autonomous theory discovery, novel physics, or verified physical covariance. Include source hashes, exact CI and artifact, original source spans, all predecessor negatives and no deployment.
