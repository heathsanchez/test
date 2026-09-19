# V20 Precommit — existential viability factorization

## Frozen residual

`POLICY_STRUCTURE_UNDERDETERMINED_BY_LEAVE_ONE_MECHANISM_OUT`

V19 showed that the full corpus admits the compositional policy

`candidate_preexists OR cover_witness -> SAME_FRAME_REPAIR`

but leave-one-mechanism-out transfer fails because the two proof modes are represented as unrelated Boolean atoms.

## Hypothesis

H20: heterogeneous witness-producing mechanisms with common codomain `Theta_same` factor through the proposition

`Inhabited(V_same(rho)) := exists verified witness w : Option[Theta_same]`.

The developmental action depends on that proposition rather than witness-mechanism identity.

## Withheld information

The policy learner is not given the semantic names `candidate_preexists` or `cover_witness`, domain labels, StrCC quotient keys, or dependency edges. Witness mechanism ids are opaque and are permuted by metamorphic controls.

## Supplied structure / boundary

This is a finite exact experiment. We supply:

- a typed witness interface;
- the distinction between codomains `Theta_same` and `Theta_other`;
- a finite witness-mechanism carrier;
- a finite compositional policy grammar containing both name-sensitive atoms and type-level existential operators;
- an exact finite action verifier and CompleteCover status.

This does **not** test automatic adequacy-map discovery, automatic type-system discovery, or unrestricted policy-language invention.

## Deciding tests

1. **Mechanism holdout:** for each same-frame witness mechanism, remove every positive episode using that mechanism from training. The frozen learned policy must classify the held-out positive mechanism correctly.
2. **Intensionality:** the selected minimum program must be the type-level existential viability predicate, not a mechanism-name formula.
3. **Alpha/reorder invariance:** policy output must survive witness-id permutation and mechanism reordering.
4. **Typed-interface ablation:** remove type-level existential operators, leaving anonymous/name-sensitive Boolean atoms. Mechanism-holdout transfer must fail.
5. **Exact verification:** every held-out action is independently checked against exact finite admissible actions.
6. **Hostile controls:** noncausal and preservation-failure cases must be rejected by the verifier even if the policy proposes an intervention.

## Frozen gates

- `existential_viability_object_synthesized=true`
- `minimum_under_declared_policy_grammar=true`
- `leave_one_positive_mechanism_out_100pct=true`
- `all_heldout_actions_completecover_verified=true`
- `positive_mechanism_names_never_required=true`
- `alpha_rename_and_mechanism_reorder_invariant=true`
- `typed_interface_ablation_breaks_mechanism_transfer=true`
- `hostile_noncausal_and_preservation_controls_rejected=true`

Only if all are true may V20 report `EXISTENTIAL_VIABILITY_FACTORIZATION_GATE=true`.
