import Collatz.OrdinaryExitReduction

namespace CollatzFinal.SourceProduct

/-- The objective keeps its original source while the current state evolves. -/
def ExitObligation (source current : Nat) : Prop :=
  Eventually shortcut (OrdinaryExit source) current

/-- Once a source-relative exit is earned, every actual continuation retains
it. A smaller endpoint becomes a smaller-source merge witness after a step. -/
theorem ordinary_exit_forward (source : Nat) :
    ForwardInvariant shortcut (OrdinaryExit source) := by
  intro current h
  rcases h with ht | hd | hm
  · exact Or.inl (terminal_forward_invariant current ht)
  · exact Or.inr (Or.inr ⟨current, 1, hd.1, hd.2, rfl⟩)
  · rcases hm with ⟨p, b, hp, hbelow, hmerge⟩
    refine Or.inr (Or.inr ⟨p, b + 1, hp, hbelow, ?_⟩)
    rw [iter_succ_last, hmerge]

/-- Exact weakest-precondition transport along an admitted actual macro. -/
theorem exit_obligation_iter_iff (source current depth : Nat) :
    ExitObligation source current ↔
      ExitObligation source (iter shortcut depth current) := by
  constructor
  · intro h
    exact eventually_iter_forward shortcut (OrdinaryExit source)
      (ordinary_exit_forward source) h depth
  · rintro ⟨k, hk⟩
    exact ⟨depth + k, by simpa [iter_add] using hk⟩

/-- A concrete coalescence warrant permits substitution of the protected
eventual-exit obligation. It supplies no new progress or coverage premise. -/
theorem exit_obligation_coalescent_iff
    (source x y a b : Nat)
    (hmerge : iter shortcut a x = iter shortcut b y) :
    ExitObligation source x ↔ ExitObligation source y := by
  calc
    ExitObligation source x ↔
        ExitObligation source (iter shortcut a x) :=
      exit_obligation_iter_iff source x a
    _ ↔ ExitObligation source (iter shortcut b y) := by rw [hmerge]
    _ ↔ ExitObligation source y := (exit_obligation_iter_iff source y b).symm

/-- Substitution remains valid under arbitrary actual continuations, with
the source held fixed. This avoids assuming an unknown full future quotient. -/
theorem exit_obligation_coalescent_continuations
    (source x y a b u v : Nat)
    (hmerge : iter shortcut a x = iter shortcut b y) :
    ExitObligation source (iter shortcut u x) ↔
      ExitObligation source (iter shortcut v y) := by
  calc
    ExitObligation source (iter shortcut u x) ↔ ExitObligation source x :=
      (exit_obligation_iter_iff source x u).symm
    _ ↔ ExitObligation source y :=
      exit_obligation_coalescent_iff source x y a b hmerge
    _ ↔ ExitObligation source (iter shortcut v y) :=
      exit_obligation_iter_iff source y v

/-- Backward propagation of a witnessed exit through a lawful macro. -/
theorem exit_obligation_of_guarded_macro
    (source current target depth : Nat)
    (hadmit : iter shortcut depth current = target)
    (htarget : ExitObligation source target) :
    ExitObligation source current := by
  apply (exit_obligation_iter_iff source current depth).mpr
  simpa [hadmit] using htarget

/-- A certificate contains actual premises and finite backward dependencies.
There is no unresolved or unsupported cycle constructor. -/
inductive ExitCertificate (source : Nat) : Nat → Type where
  | hit (current : Nat) (hexit : OrdinaryExit source current) :
      ExitCertificate source current
  | viaMacro (current target depth : Nat)
      (hadmit : iter shortcut depth current = target)
      (child : ExitCertificate source target) : ExitCertificate source current
  | coalescent (current target a b : Nat)
      (hmerge : iter shortcut a current = iter shortcut b target)
      (child : ExitCertificate source target) : ExitCertificate source current

theorem ExitCertificate.sound {source current : Nat}
    (certificate : ExitCertificate source current) :
    ExitObligation source current := by
  induction certificate with
  | hit current hexit => exact ⟨0, hexit⟩
  | viaMacro current target depth hadmit child ih =>
      exact exit_obligation_of_guarded_macro source current target depth hadmit ih
  | coalescent current target a b hmerge child ih =>
      exact (exit_obligation_coalescent_iff source current target a b hmerge).mpr ih

/-- A zero-extension observation separates two different source frames. -/
theorem immediate_exit_guard_needs_origin :
    OrdinaryExit 4 3 ∧ ¬ OrdinaryExit 1 3 := by
  constructor
  · exact Or.inr (Or.inl (by decide))
  · intro h
    rcases h with ht | hd | hm
    · rcases ht with h1 | h2 <;> omega
    · omega
    · rcases hm with ⟨p, b, hp, hbelow, _⟩
      omega

/-- This is the actual QED seam. The universal obligation remains a premise
until a separately supplied coverage/exhaustion certificate discharges it. -/
theorem collatz_of_universal_exit_obligation
    (hcomplete : ∀ n, 1 < n → ExitObligation n n) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  exact reaches_one_of_eventual_ordinary_exit_gt_one hcomplete

/-- Successful universal certificate synthesis would actually discharge QED.
The universal certificate-producing function is not supplied here. -/
theorem collatz_of_universal_exit_certificates
    (complete : ∀ n, 1 < n → ExitCertificate n n) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply collatz_of_universal_exit_obligation
  intro n hn
  exact (complete n hn).sound

#print axioms ordinary_exit_forward
#print axioms exit_obligation_iter_iff
#print axioms exit_obligation_coalescent_iff
#print axioms exit_obligation_coalescent_continuations
#print axioms exit_obligation_of_guarded_macro
#print axioms collatz_of_universal_exit_obligation
#print axioms ExitCertificate.sound
#print axioms immediate_exit_guard_needs_origin
#print axioms collatz_of_universal_exit_certificates

end CollatzFinal.SourceProduct
