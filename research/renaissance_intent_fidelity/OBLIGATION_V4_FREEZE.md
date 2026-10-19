# V4 freeze: obligation-aware comparison, exposed controls only

Prior V3 run 39221961893 is green and reveals an extra-premise false acceptance.
This V4 is a **post-outcome repair** evaluated only on exposed V3 controls; NOT prospective or source-distinct.

Frozen before implementing V4 observer:
- Original obligation: hypotheses (a<=b, c<=d), conclusion a*c<=b*d.
- Comparison operates on separately evaluated *premise and conclusion functions*, not truth of implication.
- Order of conjunctive premises is immaterial; duplicate premises are idempotent; tautological premises may be removed.
- Adding non-tautological a=0 is a mismatch, even if the entire implication is true.
- Removing c<=d is a mismatch; reversing conclusion is a mismatch.
- All claims are bounded to Nat factors 0..2; exhaustive 81 assignments.
- Baseline 1: implication-truth-table equivalence (V3).
- Baseline 2: equally informed normalized-obligation comparator (same algorithm and data); expected tie, NOT a win.
- No model-generated variants, independent human adjudication, or general proof of intent fidelity.
- Fail if V4 loses any V3 passing harmless control.
