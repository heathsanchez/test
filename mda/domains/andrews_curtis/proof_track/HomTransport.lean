import AC

/-!
# Functorial transport of Andrews--Curtis reachability

AC moves are built only from inversion, multiplication and conjugation.
Consequently every endomorphism of the ambient free group transports AC
steps and finite AC paths.

This theorem isolates the algebraic soundness principle used by symmetry-based
search: a search may transport a certificate through a free-group symmetry
provided the transformed standard basis is itself normalized back to the
official standard target.
-/

namespace AC

/-- Apply a free-group endomorphism pointwise to every relator. -/
def mapRelatorsBy {n : ℕ} (φ : Word n →* Word n)
    (R : Relators n) : Relators n :=
  fun i => φ (R i)

/-- Pointwise mapping commutes with replacing one relator. -/
theorem mapRelatorsBy_update {n : ℕ} (φ : Word n →* Word n)
    (R : Relators n) (i : Fin n) (w : Word n) :
    mapRelatorsBy φ (Function.update R i w) =
      Function.update (mapRelatorsBy φ R) i (φ w) := by
  funext k
  by_cases hki : k = i
  · subst k
    simp [mapRelatorsBy]
  · simp [mapRelatorsBy, hki]

/-- Every primitive AC step is equivariant under every free-group
endomorphism. -/
theorem step_mapRelatorsBy {n : ℕ} (φ : Word n →* Word n)
    {R S : Relators n} (h : Step R S) :
    Step (mapRelatorsBy φ R) (mapRelatorsBy φ S) := by
  cases h with
  | inv i =>
      simpa [mapRelatorsBy_update, mapRelatorsBy] using
        Step.inv (mapRelatorsBy φ R) i
  | mulRight i j hij =>
      simpa [mapRelatorsBy_update, mapRelatorsBy] using
        Step.mulRight (mapRelatorsBy φ R) i j hij
  | conj i w =>
      simpa [mapRelatorsBy_update, mapRelatorsBy] using
        Step.conj (mapRelatorsBy φ R) i (φ w)

/-- Every finite AC path transports through every free-group endomorphism. -/
theorem reachable_mapRelatorsBy {n : ℕ} (φ : Word n →* Word n)
    {R S : Relators n} (h : Reachable R S) :
    Reachable (mapRelatorsBy φ R) (mapRelatorsBy φ S) := by
  induction h with
  | refl =>
      exact Relation.ReflTransGen.refl
  | tail hprefix hstep ih =>
      exact Relation.ReflTransGen.tail ih (step_mapRelatorsBy φ hstep)

/-- A pointwise left inverse on words is also a left inverse on relator
tuples. -/
theorem mapRelatorsBy_leftInverse {n : ℕ}
    (φ ψ : Word n →* Word n)
    (hleft : ∀ w : Word n, ψ (φ w) = w)
    (R : Relators n) :
    mapRelatorsBy ψ (mapRelatorsBy φ R) = R := by
  funext i
  exact hleft (R i)

/-- Generic symmetry/retract principle for the ordinary AC target.

If:
* `ψ` undoes `φ` on every word;
* the image of the standard tuple under `φ` can be AC-normalized to standard;
* the image of the standard tuple under `ψ` can also be normalized to standard,

then applying `φ` to every relator preserves and reflects reachability to
the official standard presentation.

This packages the certificate-transport argument used by generator
permutations and signed-generator symmetries.
-/
theorem standard_reachable_iff_mapRelatorsBy {n : ℕ}
    (R : Relators n)
    (φ ψ : Word n →* Word n)
    (hleft : ∀ w : Word n, ψ (φ w) = w)
    (hφstd : Reachable (mapRelatorsBy φ (standard n)) (standard n))
    (hψstd : Reachable (mapRelatorsBy ψ (standard n)) (standard n)) :
    Reachable R (standard n) ↔
      Reachable (mapRelatorsBy φ R) (standard n) := by
  constructor
  · intro hR
    exact (reachable_mapRelatorsBy φ hR).trans hφstd
  · intro hφR
    have hback := reachable_mapRelatorsBy ψ hφR
    have hsrc :
        mapRelatorsBy ψ (mapRelatorsBy φ R) = R :=
      mapRelatorsBy_leftInverse φ ψ hleft R
    rw [hsrc] at hback
    exact hback.trans hψstd

end AC
