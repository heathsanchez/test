# V10 post-qualification parameter sensitivity and independent prior-art audit
**Status:** POST-HOC INTERPRETATION / SOURCE INTAKE, **NOT a new frozen experimental success**. Exact admitted full-order results are qualified in source V10 [GitHub Actions 38997318832](https://github.com/heathsanchez/test/actions/runs/38997318832) commit [d33983a8](https://github.com/heathsanchez/test/commit/d33983a83ff069644fa13172e9cf6dd3fb0be427); artifact #12087189043 SHA256 `366ab0260052c6083ddd8bbdd672c3d06461bd7f95e9976cd82b90b3a1b546a1` independently downloaded/reopened.

## Essential reading of the 1998 source
ANSI X9.62:1998 Annex A.2.2/A.3.2 specifies subgroup-size lower bound **rmin as a chosen security parameter**, subject to minimum >2^160 and security-level advice, rather than one universally fixed value for P224. Original text in [1998 ANSI X9.62 excerpt, question 7 on p-curve choice](https://citeseerx.ist.psu.edu/document?doi=5258c97e3f231473f84504b8e5fcaf99374fac7a&repid=rep1&type=pdf) states an example at field bitlength 191 choosing rmin about 2^185 and says larger fields warrant larger rmin. An independent [DiSSECT standards synopsis](https://dissect.crocs.fi.muni.cz/standards/x962) summarizes near-primality and MOV; its informal "min" formula should not supersede the primary X9.62 parameter-selection text. The V10 frozen **illustrative** rmin>2^160 with small-prime factor lmax255 and MOV cutoff 20 is one permissive instantiation, **NOT** proof the NSA chose that value.

## Exact post-hoc sensitivity from the same 48 full point counts (no new SEA calls)
For index69, verified group order = `26959946667150639794667015087019622232619718199909695814913490730335` = **515 × n69**, h=5×103 and n69=`52349411004175999601295174926251693655572268349339215174589302389` (215-bit prime by PARI and separate SymPy). For index77, group order = `26959946667150639794667015087019640528296954594188780422282879336101` (225-bit prime, h=1). Both are nonanomalous with MOV>20 on the declared tests.

Preserving the other frozen V10 predicates:
| Extra subgroup-size minimum | Earlier accepted indices in 1..77 | First |
|---|---|---|
| n>2^160 | [69,77] | 69 |
| n>2^214 | [69,77] | 69 |
| n>2^215 | [77] | 77 |
| n>2^218 (security-strength illustration, NOT historical evidence) | [77] | 77 |
| n>2^224 | [77] | 77 |

This is a **sensitivity diagnostic after the V10 result**, not a predeclared held-out selection-rule discovery. For the distinct V9 **NIST-like** requirement *full group prime order and exactly 224 group bits*, the earliest eligible index is **777**, followed by 1485,5736,7026. Therefore three different selection *models* lead to 69,77,777—not to the historically standardized 7026. No one model is authenticated as historical.

## Independent external prior work discovered after V10
[aburan28/crypto-autoresearcher — 2026-10-16 open selection problem](https://github.com/aburan28/crypto-autoresearcher/blob/main/problems/nist-seed-selection-rule-unexplained.md) and [historical workflow study](https://github.com/aburan28/crypto-autoresearcher/blob/main/research/nist_seed_1997_workflow_20261016/report.md) **SOURCE_OBSERVED / NOT independently requalified here**. It reports earlier full-six-stream 21 accepted/skipped curve reconstruction, roughly 60 feature and several shared-RNG-consumption hypotheses tested without separating published from skipped seeds. It also documents historical testimony identifying Bob Reiter as author of the original generation code, while no original code/trace has been located. Do not rerun those already attempted filters and call the result novel; verify their runs before treating their outputs as new authority.

## Explicit open result
Original historical source/criterion, how many timestamp runs occurred, point-validation software/CPU ABI, exact RNG call consumption during actual curve generation, and P256 generator point G derivation are **UNKNOWN**. FreeLIP C tested in V10 is a dated mirrored arithmetic library, not the authenticated NSA generator. The x86_64 FreeLIP glibc abort was an ABI incompatibility control resolved on original 32-bit-long ABI, **not** a historical NSA crash. New archival evidence or a genuinely independently predictive preregistered multi-curve rule is required to promote historical origin. No ECDSA security failure or unique public discovery claim.
