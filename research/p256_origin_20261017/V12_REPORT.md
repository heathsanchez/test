# V12 — Source-sized eleven-limb inversion without a billion-quotient search

**Experimental date:** 17 October 2026 (NZ). **Freeze before V12 source:** [commit 9578ccae](https://github.com/heathsanchez/test/commit/9578ccae67a49f68c4e85ebe0103f46733e8125e). **Current result:** `WARRANTED_BOUNDED_LOCAL` under declared no-rejection FreeLIP generator model, external CI not yet established. **Historical P-256 generator origin:** `UNKNOWN`.

## Why this result is distinct

Previous V1/V2 FreeLIP tests enumerated selected seed ranges; V11 inverted every 107-bit state but only for a ten-limb geometry. This experiment uses the **original eleven 26-bit limb geometry** implied by `zrandomb(p)` on a 256-bit p (when built in 26-bit-limb mode), and quantifies every seed/state and every possible reduction quotient *without enumerating either*. The program did NOT test actual NSA source code or any source-independent historical origin.

## Exact invariant, all q

For the public P-256 prime `p=2^256−2^224+2^192+2^96−1` and standardized Gx, every 286-bit raw integer mapping to Gx mod p is `raw=Gx+q*p`, with `0≤q<2^30`. Let `d0..d10` be its little-endian base-`2^26` digits. Whole-range exact congruences and endpoint inequalities prove:

| Digit | Number of low bits forced independent of q |
|---|---:|
| d2 | 26 |
| d3 | 18 |
| d5 | 26 |
| d6 | 26 |
| d7 | 10 |
| **Total** | **106** |

The proof uses `p ≡ −1 (mod 2^96)` and `p ≡ 2^96−1 (mod 2^192)` plus positive exact carry/borrow margins. Every possible modular quotient has **the same five masked observations**. These do not require 2^30 enumeration.

## Invert the full 107-bit state

For observations at temporal indices `i_j` with `b_j` known low bits `t_j`, write `s_ij=t_j+2^bj*h_j`. With `A=3^121 mod (2^107−1)` and `M=2^107−1`, consecutive PRNG states satisfy `s_ij=A^(ij−i0)*s_i0 (mod M)`. The corresponding high-part congruences define an exact 5D **integer-weighted lattice**, with coordinate scales `2^bj`.

An exact Euclidean sphere covers all feasible high-state boxes. SymPy LLL produces a reduced basis; exact integer determinant and transform checks certify that its lattice is unchanged. An exact rational Gram–Schmidt coefficient enumerator exhausts all lattice points inside the sphere, without floating-point bounds. The independently written verifier requires only standard Python arithmetic and checks the supplied unimodular basis transformation.

## Exact outcome

- **1,073,741,824 q values covered by proof**, no q iteration.
- **All 107-bit states** admitted at the selected first-observation time, without seed or clock restriction.
- Five fixed observation masks, **106 forced output bits**.
- **Source-native high-to-low order:** 46 lattice nodes, 17 sphere leaves, **2 compatible full hidden states**, neither reproduces Gx after the other six outputs are reconstructed.
- **Reverse limb order control:** 50 nodes, 20 sphere leaves, zero compatible hidden states.
- Four planted positive controls from real FreeLIP recurrence states (seed 20000/7 and 20420/29, each limb order) recovered the exact hidden state and full eleven raw words.
- Both target orientations: **zero** full 11-limb P-256 Gx matches. Exact-source certificate in `V12_CERTIFICATE.json` is roughly 7 KB, not an expensive search transcript.

## Source and limits

The 1997 FreeLIP mirror is [pinned at 00898a4](https://github.com/lrobot/freelip/commit/00898a4814d2cc1244bf348682be6ed10dda35f0) and is independently connected to the 1997 base-point controls by Anthropic's source-reproduction description. `zrandomb` uses one extra limb above the field length, draws in high-to-low order, and reduces modulo the input bound. Under a build with `NBITS=26`, P-256 requires 11 limbs. **The theorem is conditional on consecutive accepted outputs with no internal `zrandom` rejection**; the original generator could, rarely, advance state more than once while seeking an accepted output. Those paths have not been excluded. Further open grammars: other NBITS builds, state seeding variants, hash-to-curve/scalar multiplication, any different point generation algorithm. This result is **not** a cryptographic weakness, a historical attribution, or a new generally applicable elliptic-curve theorem.

## Reproduce

```
python -m pip install sympy==1.14.0
python v12_inverse.py --out V12_CI_RESULTS.json
python make_v12_certificate.py
python verify_v12_certificate.py     # Python standard library only
```

**Next consequential residual:** independently qualify this certificate, then attempt *exact internal-rejection skip variants* of the original 11-limb sampler. Do not widen random seed ranges again. Historical source provenance is still separately required even if a numerical match were ever produced.
