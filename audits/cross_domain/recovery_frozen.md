# Held-out source-estimate recovery

Baseline: 84e0da436a28f818a3d5fd0d4518c43b7a05b31c. This protocol is frozen before the recovery run.

The source theorem `EulerBlowup.self_sub_cube_le_arctan` and its proof body are withheld from the recovery generator. They are permitted only in the final independent comparison. The source of the derivative identity is Mathlib; the target is the genuine OpenAI polar-chart definition at 8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538.

The unchanged `experiment.develop` is first run with the lower estimate removed. It must return a separating residual or grammar insufficiency, not silently accept a failed target. A new, explicitly separate synthesis operator may then extend the grammar. No claim is made that the frozen controller itself has acquired unrestricted synthesis.

Frozen synthesis grammar: polynomial minorants `x - c*x^3`, with rational c unknown and no prelisted value 1/3. Available facts are arctan(0)=0, its derivative 1/(1+x^2), exact rational polynomial arithmetic, and the sufficient certificate that a polynomial has nonnegative coefficients on x>=0. The operator clears the positive denominator, solves the coefficient inequalities for the least nonnegative rational c, and emits a candidate and certificate. The generator must not read the withheld source theorem or its proof.

Qualification: recover the exact coefficient; independently replay a Lean proof without the withheld lemma; check standard axioms; transfer the recovered theorem to the actual baseChart and all four localChart indices; compare the recovered statement with the withheld source theorem only after the candidate is frozen. The original selection baseline, budget, and no-residual control remain unchanged. Report generation, proof construction, and resource failures separately. A successful scalar recovery is not a new Navier-Stokes regularity theorem or a repair of a missing blow-up step.
