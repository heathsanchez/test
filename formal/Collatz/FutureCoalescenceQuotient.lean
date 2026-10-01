import Collatz.EarlierSourceCollision

namespace CollatzFinal.SourceProduct

/-- Two positive-world states are identified when their deterministic futures
meet. This is the exact orbit-coalescence relation used by lower-source merge. -/
def OrbitCoalescent (x y : Nat) : Prop :=
  ∃ a b, iter shortcut a x = iter shortcut b y

theorem orbitCoalescent_refl (x : Nat) : OrbitCoalescent x x := by
  exact ⟨0, 0, rfl⟩

theorem orbitCoalescent_symm {x y : Nat} :
    OrbitCoalescent x y → OrbitCoalescent y x := by
  rintro ⟨a, b, h⟩
  exact ⟨b, a, h.symm⟩

theorem orbitCoalescent_trans {x y z : Nat} :
    OrbitCoalescent x y → OrbitCoalescent y z → OrbitCoalescent x z := by
  rintro ⟨a, b, hxy⟩ ⟨c, d, hyz⟩
  refine ⟨a + c, d + b, ?_⟩
  calc
    iter shortcut (a + c) x =
        iter shortcut c (iter shortcut a x) := iter_add shortcut a c x
    _ = iter shortcut c (iter shortcut b y) := by rw [hxy]
    _ = iter shortcut (b + c) y := (iter_add shortcut b c y).symm
    _ = iter shortcut (c + b) y := by rw [Nat.add_comm b c]
    _ = iter shortcut b (iter shortcut c y) := iter_add shortcut c b y
    _ = iter shortcut b (iter shortcut d z) := by rw [hyz]
    _ = iter shortcut (d + b) z := (iter_add shortcut d b z).symm

/-- Orbit coalescence is an actual equivalence relation, so it defines a lawful
quotient of the deterministic future system. -/
def orbitCoalescentSetoid : Setoid Nat where
  r := OrbitCoalescent
  iseqv := ⟨orbitCoalescent_refl, orbitCoalescent_symm, orbitCoalescent_trans⟩

/-- One Collatz step never changes the future-coalescence class. -/
theorem step_same_coalescence_class (x : Nat) :
    OrbitCoalescent x (shortcut x) := by
  refine ⟨1, 0, ?_⟩
  simp [iter]

/-- Nor does any finite lawful continuation. Thus the induced dynamics on the
coalescence quotient is stationary. -/
theorem iter_same_coalescence_class (x k : Nat) :
    OrbitCoalescent x (iter shortcut k x) := by
  exact ⟨k, 0, rfl⟩

/-- Eventual earlier-source collision is exactly membership in a
future-coalescence class containing some strictly earlier positive source. -/
theorem eventual_earlierSourceCollision_iff_smaller_coalescent
    {source current : Nat} :
    Eventually shortcut (EarlierSourceCollision source) current ↔
      ∃ p, 0 < p ∧ p < source ∧ OrbitCoalescent current p := by
  constructor
  · rintro ⟨k, hk⟩
    rcases hk with ⟨p, b, hp, hlt, hpb⟩
    exact ⟨p, hp, hlt, ⟨k, b, hpb.symm⟩⟩
  · rintro ⟨p, hp, hlt, hcoal⟩
    rcases hcoal with ⟨a, b, hab⟩
    exact ⟨a, ⟨p, b, hp, hlt, hab.symm⟩⟩

/-- The protected ExitObligation therefore depends only on the original source
and whether the current coalescence class already contains a smaller source. -/
theorem exitObligation_iff_smaller_coalescent
    {source current : Nat} (hsource : 1 < source) :
    ExitObligation source current ↔
      ∃ p, 0 < p ∧ p < source ∧ OrbitCoalescent current p := by
  calc
    ExitObligation source current ↔
        Eventually shortcut (EarlierSourceCollision source) current :=
      exitObligation_iff_eventual_earlierSourceCollision hsource
    _ ↔ ∃ p, 0 < p ∧ p < source ∧ OrbitCoalescent current p :=
      eventual_earlierSourceCollision_iff_smaller_coalescent

/-- Collatz closes if every source above 1 belongs to a coalescence class whose
positive representative can be lowered. There is no separate local trajectory
rank in this QED seam. -/
theorem collatz_of_every_source_coalesces_lower
    (hlower :
      ∀ n, 1 < n →
        ∃ p, 0 < p ∧ p < n ∧ OrbitCoalescent n p) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply collatz_of_universal_exit_obligation
  intro n hn
  exact (exitObligation_iff_smaller_coalescent hn).mpr (hlower n hn)

/-- Coalescence transports eventual terminal goodness because the two futures
literally share a tail. -/
theorem orbitCoalescent_preserves_collatzGood
    {x y : Nat} (hxy : OrbitCoalescent x y) (hy : CollatzGood y) :
    CollatzGood x := by
  rcases hxy with ⟨a, b, hab⟩
  have htailY : CollatzGood (iter shortcut b y) :=
    eventually_iter_forward shortcut Terminal terminal_forward_invariant hy b
  have htailX : CollatzGood (iter shortcut a x) := by
    simpa [hab] using htailY
  rcases htailX with ⟨k, hk⟩
  exact ⟨a + k, by simpa [iter_add] using hk⟩

/-- Reaching 1 is exactly belonging to 1's future-coalescence class. -/
theorem reaches_one_iff_coalescent_one (n : Nat) :
    (∃ k, iter shortcut k n = 1) ↔ OrbitCoalescent n 1 := by
  constructor
  · rintro ⟨k, hk⟩
    exact ⟨k, 0, by simpa [iter] using hk⟩
  · intro hcoal
    have hgood1 : CollatzGood 1 := ⟨0, Or.inl rfl⟩
    exact collatzGood_eventually_one
      (orbitCoalescent_preserves_collatzGood hcoal hgood1)

/-- Exact quotient statement of Collatz: the positive future-coalescence
quotient has a single class, represented by 1. -/
theorem collatz_iff_single_positive_coalescence_class :
    (∀ n, 0 < n → ∃ k, iter shortcut k n = 1) ↔
      (∀ n, 0 < n → OrbitCoalescent n 1) := by
  constructor
  · intro h n hn
    exact (reaches_one_iff_coalescent_one n).mp (h n hn)
  · intro h n hn
    exact (reaches_one_iff_coalescent_one n).mpr (h n hn)

#print axioms orbitCoalescent_refl
#print axioms orbitCoalescent_symm
#print axioms orbitCoalescent_trans
#print axioms step_same_coalescence_class
#print axioms iter_same_coalescence_class
#print axioms eventual_earlierSourceCollision_iff_smaller_coalescent
#print axioms exitObligation_iff_smaller_coalescent
#print axioms collatz_of_every_source_coalesces_lower
#print axioms orbitCoalescent_preserves_collatzGood
#print axioms reaches_one_iff_coalescent_one
#print axioms collatz_iff_single_positive_coalescence_class

end CollatzFinal.SourceProduct
