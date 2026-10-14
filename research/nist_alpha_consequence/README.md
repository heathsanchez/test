# NIST/CODATA 2022 alpha: source-annotated consequence qualification

**Status: CANDIDATE until exact-head GitHub Actions reports success and artifacts are inspected.** Isolated research branch; do not merge, deploy, contact upstream, or claim original CODATA analysis reproduced.

## Objective
Test the one selected MathGraph scientific consequence use case on real published NIST 2022 CODATA data: preserve a >5 sigma Cs-vs-Rb recoil disagreement, replay the deliberately simplified three-source weighted mean with CODATA's published factor-2.5 uncertainty expansion, derive the atomic unit of velocity and related SI constants, avoid double-counting descendants as new evidence, and reject unsupported optimal-experiment recommendations.

## Frozen upstream authority (manually transcribed, not upstream-byte-pinned)
- NIST/CODATA original report (2022 adjustment, 2025 publication): https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958143 ; DOI 10.1103/RevModPhys.97.025002 . Table XXV D1–D6 (PDF page index 37), Eq. (92), Table XXVI (D5–D6 correlation 0.1032), Section XVI.A (PDF page index 53), Table XXXV (PDF page index 49).
- Parker et al. cesium recoil: https://arxiv.org/abs/1812.04130 : inverse alpha 137.035999046(27).
- Morel et al. rubidium recoil: https://www.nature.com/articles/s41586-020-2964-7 : inverse alpha 137.035999206(11).
- Fan et al. electron magnetic-moment plus QED inference: https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.130.071801 : inverse alpha 137.035999166(15).
- 2022 CODATA external reference: inverse alpha 137.035999177(21); atomic velocity 2187691.26216(34) m/s. These are **not** fourth measurements.

## Strong baseline and falsifiers
A direct independent Python stdlib weighted-least-squares implementation is the baseline. Success requires all of:
1. Independent exact-rational and Decimal implementations agree; unexpanded Cs–Rb difference exceeds five combined standard uncertainties.
2. The unexpanded three-source fit has chi-squared >25 on 2 degrees of freedom and must **not** be presented as internally consistent. CODATA's prior published factor 2.5 reduces the largest residual below two.
3. Reconstructed inverse alpha and velocity agree with the rounded 2022 CODATA references within 0.1 of the latter's published uncertainty. This is a historical replay, **not** independent confirmation of source measurements or novel science.
4. A duplicate measurement identity adds zero statistical information. Changing a source changes downstream values but not exact SI h/e/c or h/e². Report uncertain physical experiment design as **UNKNOWN**.
5. The upstream PDF's original bytes and full correlated adjustment remain unverified. This is a **bounded numerical replay**; do not promote source-native verification, complete 133x79 adjustment, new physical discoveries or external adoption.

## Local independent package
An additional 20-test local Python suite, exact decimals, source-annotated frozen data, receipts and the full report were created in the model's working container. The isolated CI here is a **separate numerical implementation**, not a proof the uncommitted package is identical. Both are bounded by the original-source byte-attestation gap.

## Consequential residual
The genuine next step is a frozen source-byte/checksum and measurement ingestion path that can reproduce a **previously unseen independent external scientific measurement**, including covariance and systematic-hypothesis dependence, with no target-specific hand-coded adapter and a well-matched conventional LSA baseline. Until that boundary is crossed, the optimal new physical experiment remains UNKNOWN.
