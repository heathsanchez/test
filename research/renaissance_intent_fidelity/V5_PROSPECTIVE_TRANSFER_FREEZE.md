# V5 prospective transfer freeze (before inspecting source)
Prior V4 exposed calibration GREEN run 39222552623. V4 algorithm is frozen, no target-specific modification permitted.
Unopened source: leanprover-community/mathlib4 tag v4.34.0, Mathlib/Data/Nat/GCD/Basic.lean.
Eligibility: first theorem/lemma with an immediately adjacent docstring, and with a statement containing an implication or a hypothesis. If none, STOP with INSUFFICIENT_SOURCE.
Construct three generic candidate transformations only after admission:
(1) swap two conjunctive hypotheses if present (harmless);
(2) append an explicit tautological hypothesis True (harmless);
(3) append an explicit substantive hypothesis False (non-equivalent obligation).
If no conjunctive hypotheses, record NOT_APPLICABLE for (1), no substitution.
Observer: the exact V4 premise/conclusion finite-observation algorithm. Since V4 operates only on four Nat factors, any unmatched source signature must return INAPPLICABLE rather than silently applying a new parser.
Comparator: an equally informed human/conventional obligation comparison has access to same theorem source and transformations; no superiority claim absent measured blind baseline.
Source pin and admission before reading mathematical outcomes. Preserve UNKNOWN, no cherry-picked replacement.
