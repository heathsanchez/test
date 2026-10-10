import Collatz.ActualEpisode

namespace CollatzFinal
namespace SourceProduct

/-! V159: every fixed-modulus shortcut-invariant label is constant.

The exact Collatz relations f(2n)=f(n) and (for odd n)
f(3n+1)=f(n) reduce any supposed positive period M:
- even M: period M/2
- odd multiple of 3: period M/3
- coprime to 6, M>1: period (M-1)/2 via a commutator.
Strong induction finishes. This is unconditional modular geometry,
NOT a proof that the real positive Collatz graph is connected.
-/

def V159Period {α : Type} (f : Nat → α) (M : Nat) : Prop :=
  ∀ n, f (n+M) = f n

theorem v159_period_multiple {α : Type} (f : Nat → α)
    (M : Nat) (hPer : V159Period f M) (n t : Nat) :
    f (n+t*M) = f n := by
  induction t with
  | zero => simp
  | succ t ih =>
      calc
        f (n+(t+1)*M) = f ((n+t*M)+M) := by
          congr 1
          simp [Nat.succ_mul, Nat.add_assoc]
        _ = f (n+t*M) := hPer _
        _ = f n := ih

theorem v159_even_period_reduction {α : Type} (f : Nat → α)
    (M d : Nat)
    (hDouble : ∀ n, f (2*n) = f n)
    (hPer : V159Period f M)
    (hM : M = 2*d) : V159Period f d := by
  intro n
  calc
    f (n+d) = f (2*(n+d)) := (hDouble (n+d)).symm
    _ = f (2*n+M) := by congr 1; omega
    _ = f (2*n) := hPer _
    _ = f n := hDouble n

theorem v159_odd_period_affine {α : Type} (f : Nat → α)
    (M : Nat) (hOddM : M%2=1)
    (hDouble : ∀ n, f (2*n) = f n)
    (hOdd : ∀ n, n%2=1 → f (3*n+1) = f n)
    (hPer : V159Period f M) (n : Nat) :
    f n = f (3*n+(3*M+1)/2) := by
  have hOddSource : (2*n+M)%2=1 := by omega
  have hU : 2*((3*M+1)/2)=3*M+1 := by omega
  calc
    f n = f (2*n) := (hDouble n).symm
    _ = f (2*n+M) := (hPer (2*n)).symm
    _ = f (3*(2*n+M)+1) := (hOdd _ hOddSource).symm
    _ = f (2*(3*n+(3*M+1)/2)) := by congr 1; omega
    _ = f (3*n+(3*M+1)/2) := hDouble _

theorem v159_odd_third_period_reduction {α : Type} (f : Nat → α)
    (M d : Nat) (hOddM : M%2=1) (hM : M=3*d)
    (hDouble : ∀ n, f (2*n) = f n)
    (hOdd : ∀ n, n%2=1 → f (3*n+1)=f n)
    (hPer : V159Period f M) : V159Period f d := by
  intro n
  let u := (3*M+1)/2
  have hg (x : Nat) : f x = f (3*x+u) :=
    v159_odd_period_affine f M hOddM hDouble hOdd hPer x
  calc
    f (n+d) = f (3*(n+d)+u) := hg (n+d)
    _ = f ((3*n+u)+M) := by congr 1; omega
    _ = f (3*n+u) := hPer _
    _ = f n := (hg n).symm

theorem v159_find_one_mod_six
    (x M : Nat) (hOddM : M%2=1) (hNotThree : M%3≠0) :
    ∃ t q : Nat, x+t*M=6*q+1 := by
  have hmod : M%6=1 ∨ M%6=5 := by omega
  have hh :
    (x+M)%6=1 ∨ (x+2*M)%6=1 ∨ (x+3*M)%6=1 ∨
    (x+4*M)%6=1 ∨ (x+5*M)%6=1 ∨ (x+6*M)%6=1 := by
    rcases hmod with hm | hm
    · omega
    · omega
  rcases hh with h | h | h | h | h | h
  · exact ⟨1,(x+M)/6,by omega⟩
  · exact ⟨2,(x+2*M)/6,by omega⟩
  · exact ⟨3,(x+3*M)/6,by omega⟩
  · exact ⟨4,(x+4*M)/6,by omega⟩
  · exact ⟨5,(x+5*M)/6,by omega⟩
  · exact ⟨6,(x+6*M)/6,by omega⟩

theorem v159_coprime_period_reduction {α : Type} (f : Nat → α)
    (M : Nat)
    (hOddM : M%2=1) (hNotThree : M%3≠0)
    (hDouble : ∀ n, f (2*n) = f n)
    (hOdd : ∀ n, n%2=1 → f (3*n+1)=f n)
    (hPer : V159Period f M) :
    V159Period f ((M-1)/2) := by
  let d := (M-1)/2
  let u := (3*M+1)/2
  have hM : M=2*d+1 := by dsimp [d]; omega
  have hU : u=1+M+d := by dsimp [u]; omega
  have hDoubleU : 2*u=3*M+1 := by dsimp [u]; omega
  have hg (x : Nat) : f x = f (3*x+u) :=
    v159_odd_period_affine f M hOddM hDouble hOdd hPer x
  have hcomm (n : Nat) : f (6*n+1)=f (6*n+u) := by
    have ha : f (6*n+1)=f n := by
      calc
        f (6*n+1) = f ((6*n+1)+3*M) :=
          (v159_period_multiple f M hPer (6*n+1) 3).symm
        _ = f (2*(3*n+u)) := by congr 1; omega
        _ = f (3*n+u) := hDouble _
        _ = f n := (hg n).symm
    have hb : f (6*n+u)=f n := by
      calc
        f (6*n+u) = f (3*(2*n)+u) := by congr 1; omega
        _ = f (2*n) := (hg (2*n)).symm
        _ = f n := hDouble n
    exact ha.trans hb.symm
  intro x
  obtain ⟨t,q,hMeet⟩ := v159_find_one_mod_six x M hOddM hNotThree
  have hPx := v159_period_multiple f M hPer x t
  have hPxd := v159_period_multiple f M hPer (x+d) t
  calc
    f (x+d) = f ((x+d)+t*M) := hPxd.symm
    _ = f ((x+t*M)+d) := by congr 1; omega
    _ = f ((6*q+1)+d) := by rw [hMeet]
    _ = f (6*q+u) := by
      have hz := hPer (6*q+1+d)
      have heq : 6*q+u=(6*q+1+d)+M := by omega
      rw [heq]
      exact hz.symm
    _ = f (6*q+1) := (hcomm q).symm
    _ = f (x+t*M) := by rw [hMeet]
    _ = f x := hPx

theorem v159_all_finite_moduli_collapse {α : Type}
    (f : Nat → α)
    (hDouble : ∀ n, f (2*n)=f n)
    (hOdd : ∀ n, n%2=1 → f (3*n+1)=f n) :
    ∀ M : Nat, 0<M → V159Period f M →
      ∀ n m : Nat, f n=f m := by
  intro M
  induction M using Nat.strongRecOn with
  | ind M ih =>
      intro hPos hPer n m
      by_cases hOne : M=1
      · subst M
        have hf (z : Nat) : f z=f 0 := by
          calc
            f z = f (0+z*1) := by simp
            _ = f 0 := v159_period_multiple f 1 hPer 0 z
        exact (hf n).trans (hf m).symm
      · by_cases hEven : M%2=0
        · let d := M/2
          have hM : M=2*d := by dsimp [d]; omega
          have hDpos : 0<d := by omega
          have hDlt : d<M := by omega
          have hNew := v159_even_period_reduction f M d hDouble hPer hM
          exact ih d hDlt hDpos hNew n m
        · have hOddM : M%2=1 := by omega
          by_cases hThree : M%3=0
          · let d := M/3
            have hM : M=3*d := by dsimp [d]; omega
            have hDpos : 0<d := by omega
            have hDlt : d<M := by omega
            have hNew := v159_odd_third_period_reduction f M d
              hOddM hM hDouble hOdd hPer
            exact ih d hDlt hDpos hNew n m
          · let d := (M-1)/2
            have hDpos : 0<d := by dsimp [d]; omega
            have hDlt : d<M := by dsimp [d]; omega
            have hNew := v159_coprime_period_reduction f M
              hOddM hThree hDouble hOdd hPer
            exact ih d hDlt hDpos hNew n m

theorem v159_step_implies_even_and_odd_invariance {α : Type}
    (f : Nat → α)
    (hStep : ∀ n, f (shortcut n)=f n) :
    (∀ n, f (2*n)=f n) ∧
    (∀ n, n%2=1 → f (3*n+1)=f n) := by
  have hDouble (n : Nat) : f (2*n)=f n := by
    calc
      f (2*n) = f (shortcut (2*n)) := (hStep _).symm
      _ = f n := by rw [shortcut_two_mul]
  constructor
  · exact hDouble
  · intro n hn
    have hEq : 2*shortcut n=3*n+1 := by
      unfold shortcut
      simp only [show ¬n%2=0 by omega, ite_false]
      omega
    calc
      f (3*n+1) = f (2*shortcut n) := by rw [hEq]
      _ = f (shortcut n) := hDouble _
      _ = f n := hStep _

theorem v159_no_nontrivial_fixed_modulus_future_label {α : Type}
    (f : Nat → α)
    (hStep : ∀ n, f (shortcut n)=f n)
    (M : Nat) (hM : 0<M)
    (hPeriod : V159Period f M) :
    ∀ n m : Nat, f n=f m := by
  obtain ⟨hd,ho⟩ := v159_step_implies_even_and_odd_invariance f hStep
  exact v159_all_finite_moduli_collapse f hd ho M hM hPeriod

#print axioms v159_even_period_reduction
#print axioms v159_odd_period_affine
#print axioms v159_odd_third_period_reduction
#print axioms v159_find_one_mod_six
#print axioms v159_coprime_period_reduction
#print axioms v159_all_finite_moduli_collapse
#print axioms v159_step_implies_even_and_odd_invariance
#print axioms v159_no_nontrivial_fixed_modulus_future_label

end SourceProduct
end CollatzFinal
