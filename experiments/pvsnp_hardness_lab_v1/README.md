# P vs NP hardness-invariant spike V1

## Verdict

`FINITE SIGNAL`. The run found an exact representation repair and recurring
finite obstruction, but it did not acquire a new hardness capability and then
reuse it prospectively. A classical parity theorem was imported and transferred;
its on/off control is not a developmental acquisition ablation.

This is **not** a new asymptotic circuit lower bound. The retained theorem is
the classical `3m-3` U2 parity bound composed with restriction closure. The
experiment found a useful circuit-state representation and a global-consistency
residual, but no barrier-escaping invariant.

## Frozen circuit model

The primary model has free Boolean inputs, fan-in-two NAND gates, no constants,
free fan-out, one output, and DAG gate count. Truth-table bit `r` is the value at
`x_i=(r>>i)&1`.

## Exact runs

The compact replay in this directory independently closes:

| Inputs | Gates | Exact state counts | New output functions by layer |
|---:|---:|---|---|
| 3 | 0..5 | `1,6,36,206,1252,8188` | `3,6,13,26,43,48` |
| 4 | 0..4 | `1,10,91,811,7700` | `4,10,31,98,293` |

An independent packed-set enumerator and a second bit-set implementation
completed all 256 three-input functions. The exact minimum-size histogram for
sizes 0 through 10 is:

`3,6,13,26,43,48,53,36,22,5,1`.

Raw topologically ordered circuit enumeration independently agrees through five
gates. All retained witnesses were replayed row by row.

## Representation genesis

Output truth table alone is not a sufficient construction-state quotient.
Two states can expose the same designated output but different latent wires, so
one can realize a next target that the other cannot. The minimum repair is to
retain the set of all currently available wire behaviours and the resource
layer.

The smallest numerical version is XOR. Singleton minima predict
`1+max(C(g),C(h))=3`, but the two parents cannot coexist that early; exact joint
coavailability gives `C(XOR)=4`. Formula addition predicts 5 and also fails.
Thus the relevant exact recurrence uses joint availability `J({g,h})`, not only
singleton costs.

This is a genuine MSI-style counterexample-driven refinement, but exact joint
availability is potentially exponential. It is a correct state representation,
not yet an efficient hardness invariant.

## Falsified invariant family

`0x8f` has exact size 2 and `0xea` exact size 3, although they share all twelve
retained scalar summaries: weight, ANF degree and sparsity, maximum and total
sensitivity, Fourier degree and L1 norm, input-permutation automorphism count,
certificate complexities `C,C0,C1`, and essential-variable count.

In a separate ten-property experiment, adding Hamming-layer output counts
perfectly identifies the 80 input-permutation orbits at three variables; that
apparent success is disguised truth-table classification, not explanatory
compression. That ten-property representation fails prospectively at four
variables: `0x8ddd` has exact size 5 and `0x8adf` exact size 6 with the same
ten-property signature and Hamming-layer profile. This pair is **not** a
collision for the twelve-metric bundle above: their automorphism counts differ.

## Reusable exact consequences

1. **Parity-subcube certificate.** If a restriction of `f` is parity or its
   complement on `m` free variables, then `C_NAND(f) >= 3m-3`. Parity4 and
   `z AND parity4` therefore have size greater than 8. Verified upper witnesses
   use 12 and 14 gates. Toggling the imported theorem off returns `UNKNOWN` at
   budget 8. This is a module-dependence sanity check, not evidence that the
   finite loop learned the theorem or that retained state reduced discovery cost.

2. **Global-consistency core.** Majority3 has NAND size exactly 6, but every
   restriction to at most five truth-table rows agrees with some size-at-most-3
   circuit. Rows `{1,2,3,4,5,6}` are a minimum exclusion core. The same six-row
   obstruction survives a fourth dummy input and a basis change to AND/OR/NOT.
   Range avoidance, MCSP-NO, and synthesis-SAT UNSAT are exact encodings of this
   same exclusion; they are not three independent lower-bound proofs.

## Repository reuse and corrections

- MSI `Interface.residual_witness`, `lawful_repair`, `minimum_basis`, and
  congruence checks supplied the finite refinement discipline. Complexity
  sufficiency must be defined against cost-consequence classes, not full
  hypothesis identity.
- RealityGraph's cached consequence field and irreducible separating batches
  supplied exact observable selection, but its identifier separates every
  hypothesis and therefore is not automatically a minimum complexity quotient.
- The existing constructor-expansion V4 acquisition and held-out splits are
  observationally identical under `p -> p+2`; its reported held-out gate is a
  relabeling check, not unseen-family transfer. Its ablation Boolean is also
  copied from the acquisition failure rather than independently rerun.

## Barriers

- **Natural Proofs:** no useful large, truth-table-constructive property against
  polynomial-size general circuits was established. Constant-budget exclusion
  is large and decidable but irrelevant to the needed asymptotic regime.
- **Relativization:** disagreement sets and shared-witness consistency work for
  arbitrary finite hypothesis classes. No essential nonrelativizing step was
  found.
- **Algebrization:** no oracle-lift analysis or nonalgebrizing ingredient was
  established. Avoiding algebra does not establish barrier escape.
- **Magnitude:** the retained parity certificate is linear and basis-sensitive;
  adding XOR gates collapses parity4 to three gates.

Primary references: [Morizumi's account of the Schnorr U2 parity bound](https://arxiv.org/pdf/1504.06731),
[Razborov–Rudich on Natural Proofs](https://mit6875.github.io/PAPERS/natural_proofs.pdf),
and [Aaronson–Wigderson on algebrization](https://www.math.ias.edu/~avi/PUBLICATIONS/ABSTRACT/aw08ab.pdf).

## Highest-information next experiment

Freeze

`h_s(f) = min{|I| : no size-s circuit matches f on rows I}`

and test full-support four-input targets in both NAND and AND/OR/NOT. Demand a
compact explanation of any increase in `h_s`, not a list of all circuits. This
directly tests whether the six-row shared-description obstruction scales, while
rejecting padding, basis artifacts, and scalar-feature overfitting.

## Replay

```bash
python -m unittest discover -s experiments/pvsnp_hardness_lab_v1 -p 'test_*.py' -v
python experiments/pvsnp_hardness_lab_v1/experiment.py
```
