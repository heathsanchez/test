# V3 controlled semantic mutation freeze — source already exposed
This is an EXPOSED training/control experiment, not the sealed V2 prospective evaluation or an independent expert study.

Target: upstream Mathlib v4.34.0, Mathlib/Algebra/Order/BigOperators/Group/Finset.lean, documented theorem `prod_le_prod`. Source identity remains blob 04fc6ed3e31ef9cd594f3db95e8edf87bf593bf3.

Finite observation model: natural-number factors (0,1,2) for two indexed positions. Reference proposition R is `(a≤b ∧ c≤d) → a*c≤b*d`. We check 81 combinations by exhaustive enumeration.

Fixed candidate forms:
- R original, faithful.
- R with the conjuncts exchanged, faithful.
- R with a duplicated left conjunct but missing right conjunct, wrong.
- R with conclusion reversed, wrong.
- R with additional premise a=0, strictly stronger premise and hence weaker claim, wrong as an equivalent formalization (may still be provable).
- R with an added tautological premise, faithful.

The labels are design expectations, not independently adjudicated natural-language intent. Equivalence means identical Boolean truth tables over the finite domain. This can refute equivalence with a witness but cannot prove unrestricted theorem equivalence. Kernel verification and an equally informed human baseline remain separate unexecuted gates. No promotion to a held-out source or automatic mathematical understanding.
