import IdealLean.Semantics

/-! Compile-time interface tests for the portable semantic specification. -/

#check IdealLean.openBinder_bvar_zero
#check IdealLean.openBinder_bvar_succ
#check IdealLean.openBinder_const
#check IdealLean.Install.installed_theorem_has_no_body
#check IdealLean.Install.type_correct_in_prior_environment
#check IdealLean.Install.theorem_type_is_prop_in_prior_environment
#check IdealLean.Install.prior_environment_is_prefix
#check IdealLean.Install.checked_proof_uses_prior_environment
#check IdealLean.Install.checked_theorem_is_not_self_referential

#check IdealLean.OpaqueInstall.validated_closed_inductive_promotion_preserves_environment_validity
#check IdealLean.OpaqueInstall.installed_signature_has_no_body
