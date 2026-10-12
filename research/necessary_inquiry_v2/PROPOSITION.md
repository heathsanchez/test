# Observation-completion lemma — GF(2), finite declared interface

## Exact statement

Let the world outputs be `y = N a + T b` over GF(2), where the unknown nuisance `a` and target coefficients `b in GF(2)^m` are disjoint parameters. Let `P` be the vector space of *physically/admissibly available* parity-probe weights `p` for which `p^T N=0`; each probe produces one bit `p^T y`. Let the old observations span `P0 <= P`. Define `L(p)=p^T T`, the target consequence signature. Write `r0 = rank L(P0)` and `r = rank L(P)`.

Then (1) the old observations leave `2^(m-r0)` candidate target coefficient differences observationally indistinguishable, and the full admissible interface leaves `2^(m-r)`; (2) exactly `r-r0` additional independent binary measurements are necessary and sufficient to reach *all distinguishability allowed by P*; (3) complete target identification is possible iff `r=m`; otherwise there is an explicit nonzero `delta b in ker L(P)` that no allowed probe and no postprocessing of such probes can distinguish from zero.

This is an elementary rank-nullity / basis-extension theorem, subject to the declared linear world, nuisance, and probe model. It is not a Lean-kernel proof, an empirical theorem, a guarantee that P is physically accessible, or a universal discovery law. Synthesizing a member of P may require substantial computation, raw observations, disturbance, or calibration beyond one ideal aggregate bit.

## Proof

Each probe returns `p^T (N a + T b) = (p^T N)a + (p^T T)b = L(p)b`; thus only the row space `L(P)` can carry target information. The fibers of the corresponding linear observation map have dimension `m-r` by rank-nullity. From an old row basis of rank `r0`, every new one-bit probe can increase rank by at most one, so at least `r-r0` new independent rows are required. Since `L(P0) <= L(P)`, extend a basis of `L(P0)` to one of `L(P)` using `r-r0` admissible rows; this achieves the bound. If `r<m`, choose nonzero `delta b` in the nontrivial nullspace: it changes the target but leaves all admissible consequences invariant. Postprocessing cannot restore the distinction because every available record is identical for `b` and `b+delta b`. QED.

## Instantiation and qualification boundaries

V2 one-sided cut observations on complete graph quadratic interactions: all cuts depend only on vertex degree parity, so `r0=n-1` for n>=2, while `m=choose(n,2)`. The exact missing rank is `choose(n,2)-n+1`; source-derived affine-null probes supply the missing 6, 10, 21 measurements for n=5,6,8. Exhaustive identification n=5,6; rank + heldout synthetic qualification n=8. These ideal aggregated measurements cannot be counted as free raw source reads.

V3 repaired generic generator: an observed nuisance-feature rank replaces the V2 hardcoded `n+1` rank. The unchanged V2 cubic-transfer attempt FAILED. After the explicit repair and prospective freeze, the same V3 source synthesized eight-input cubic and sixteen-input quartic parity operators, each reaching full target rank in seeded protected families. These are ordinary Reed-Muller / Boolean Möbius algebra constructions conditional on a **designer-supplied** polynomial feature grammar. The strong equally informed stateless interpolation control TIES in solvability and cached raw input requirements.

Source: research/necessary_inquiry_v2/generator_v3.py, V3_FROZEN_GATE.md and verify_v3.py in GitHub branch `research/necessity-driven-inquiry-v2-20261012`; independent qualification run #38191873313 at commit 7216181f5d5e1a3c535cef902ae0281883f702c8 SUCCESS. Stronger use requires new exact-head run after any later commit.

## Transfer rule / limits

Reusable invariant: `obstruction (nonzero kernel) -> describe admissible probes -> augment measurement basis -> source-check -> reclassify remaining nullspace`. This is a useful mathematical construction rule, not evidence that a system can independently invent a missing semantic feature language. A raw-observation-retention control shows some apparent discovery gaps arise from discarding source data, not missing physics. The next decisive experiment must REMOVE the supplied target-feature table and require source-derived representation invention on genuinely unrelated untouched tasks with matched-cost strong baselines. Do not pay to repeat polynomial degree experiments without changing that boundary.
