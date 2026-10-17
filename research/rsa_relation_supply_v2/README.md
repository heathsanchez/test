# RSA relation-supply symmetry V2: exact candidate audit and strong SIQS control

**Status: WARRANTED_LOCAL_BOUNDED for finite source-specific result; novel factoring algorithm REJECTED/NOT CLAIMED; independent GitHub Actions GREEN not yet verified.**

## Scientific result

[Preregistered commit 3f5d2da](https://github.com/heathsanchez/test/commit/3f5d2da19c706d68c449849188b2065c6f2a9533) froze 11 distinct synthetic balanced semiprimes, factor commitments, source grammar, 40,000 candidate budget each, factor base <=1000, matched-cofactor cap <=100000, SIQS bound 2000, interval 8000, fixed seed 1234. All are separate from prior RSA-270 and V1 synthetic tests. Split: 3 calibration (58/62/66 bits), 8 protected heldout (58/60/62/64/66/68/70/72 bits). No post-hoc operator or task choice for the first heldout run.

[Original implementation d62b4b](https://github.com/heathsanchez/test/commit/d62b4b76218d40623a5fcdf51ae0064d5c0ec71e) was committed after preregistration and before opening heldout outcomes. It reuses the prior original-source GF(2) dependence and witness extraction, independent of producer selection. Two source representations are compared:
- **Forward-only** x=ceil(sqrt(N))+i for i=0..39999, direct trial division of Q(x)=x²-N.
- **Symmetric** x=ceil(sqrt(N)), then alternating x−1,x+1,x−2,x+2,..., with exact -1 sign parity for negative Q.
- **Exact p-adic/root sieve**: calculate residue solutions x²=N mod p^k (Hensel lift), mark exactly all prime-power divisibility, and reproduce exponents and cofactor without per-prime trial division on all 40000 values. This changes evaluation costs, not the set of relations under a fixed producer. Classical quadratic sieve techniques, NOT newly invented mathematics.
- **Mature equal-task control**: actually executed SymPy 1.14 SIQS (self-initializing quadratic sieve), all factors independently checked against frozen commitments. Historical full GNFS was not run and is NOT implied.

## Protected results (fully charged same candidate budget for forward and symmetric)

| Case | Forward useful relations | Symmetric useful relations | Forward factor | Symmetric factor | Mature SIQS |
|---|---:|---:|---|---|---|
| 58 bits | 9 | 14 | No | No | Yes |
| 60 bits | 64 | 103 | No | Yes, candidate 29,675 | Yes |
| 62 bits | 72 | 98 | No | Yes, candidate 39,165 | Yes |
| 64 bits | 66 | 96 | No | Yes, candidate 36,847 | Yes |
| 66 bits | 18 | 23 | No | No | Yes |
| 68 bits | 6 | 5 | No | No | Yes |
| 70 bits | 27 | 31 | No | No | Yes |
| 72 bits | 7 | 8 | No | No | Yes |
| **Heldout sum** | **269** | **378 (+40.52%)** | **0/8** | **3/8** | **8/8** |

For calibration, forward relation total 434, symmetric 600; factor success 2/3 each; mature SIQS 3/3. All eight protected cases are synthetic not real external RSA challenge instances. The one 68-bit heldout is a *negative counterexample* to universal per-instance improvement.

## Verification authority

- The source-disjoint [independent verifier](https://github.com/heathsanchez/test/blob/research/rsa-relation-supply-symmetry-20261018/research/rsa_relation_supply_v2/verify_v2_independent.py) re-executed **every** polynomial candidate of both producers over all eleven cases using a separate direct division implementation (880,000 candidate observations) and matched the ordered prime-exponent/cofactor stream SHA256, smooth counts and matched-partial counts for BOTH direct trial and exact root sieve (four compared runs per n).
- Independently recovered all 11 factor pairs from actual SIQS outputs, checked 11 preregistered SHA256 factor commitments, each prime as classified by SymPy, seven factor witnesses from the two producers over calibration+heldout, seven tampered congruence negative controls, and reconstructed nontrivial idempotents where valid. Outcome: **WARRANTED_LOCAL_INDEPENDENT_EXHAUSTIVE_AUDIT**. The full verifier is source-disjoint from the producer, but both use SymPy primality classification for above-64-bit factors.
- Original full candidate/certificate results and independent audit were recorded separately in local evidence files. Repo workflows regenerate raw result files and upload them as artifacts; they are NOT claimed to have already passed in independent hosted CI.
- [Independent Actions workflow](https://github.com/heathsanchez/test/blob/research/rsa-relation-supply-symmetry-20261018/.github/workflows/rsa-relation-supply-v2.yml) pins Python 3.13 and SymPy 1.14, performs both original runs, source-disjoint audit and the separately recorded post-result timing correction.

## Timing correction and epistemic limit

The original frozen direct-trial method redundantly executed a second factor-base sweep solely to count operations. This biases its measured wall time. **The original source and first heldout outputs are preserved, not silently rewritten.** [V2b corrected source](https://github.com/heathsanchez/test/blob/research/rsa-relation-supply-symmetry-20261018/research/rsa_relation_supply_v2/experiment_v2b.py) performs only one trial sweep. [Mechanical invariance checker](https://github.com/heathsanchez/test/blob/research/rsa-relation-supply-symmetry-20261018/research/rsa_relation_supply_v2/assert_equivalence.py) passed on all 11 original/replayed cases, retaining the original factor certificate bytes, stream hashes, counts and native SIQS success flags. This is **POST-HOC TIMING DIAGNOSTIC**, not independent prospective validation.

Corrected local heldout (8 cases, one host) summed forward trial 2.272s versus exact sieve 0.933s (2.44× faster), symmetric trial 2.302s versus sieve 0.943s (2.44× faster). These charged times include generator, root preparation and verification but depend on Python and a single host; do not generalize to mature QS/SIQS/field sieve performance. Mature SIQS remained successful on all 8; the new producer is not competitive as a factorer.

## General law and residual

**WARRANTED mathematically at the stated interface:** any linear combination of a fixed family of relation vectors remains in its existing F2 span. Quotienting, caching or rescheduling those same vectors cannot *increase* their rank. Changing the relation-generating polynomial input stream can change which parity vectors are observed and therefore change the future reachable witness set. Conversely, extracting an existing overlooked dependency may still find a factor without increasing rank; do not confuse these mechanisms.

This experiment distinguishes cheap exact source-relative evaluation from productive access to new source observations. The latter helped, but both techniques are **quadratic-sieve prior art**. It does not demonstrate any novel algebraic operator, GNFS relation-yield gain, RSA-270 factors, or scalable asymptotic effect. Strong mature SIQS still wins success 8/8 versus 3/8.

**Next most consequential question:** identify and pre-specify genuinely distinct relation-producing algebra (not known symmetric root sampling, sieve filters, partial pairing or polynomial choice), and test on untouched externally sourced inputs with equal-information mature factoring baselines. If no distinct source-backed operation is available, park RSA as UNKNOWN rather than running larger QS compute. Cross-program reuse of MSI/FLASH source-relative distinction applies to selection and verification, not a claim of new factoring laws.
