import Std

namespace CollatzFinal

def iter (f : Nat → Nat) : Nat → Nat → Nat
  | 0, n => n
  | k + 1, n => iter f k (f n)

theorem iter_add (f : Nat → Nat) (a b n : Nat) :
    iter f (a + b) n = iter f b (iter f a n) := by
  induction a generalizing n with
  | zero =>
      simp [iter]
  | succ a ih =>
      simp [Nat.succ_add, iter, ih]

theorem iter_positive
    (f : Nat → Nat)
    (hpos : ∀ n, 0 < n → 0 < f n) :
    ∀ k n, 0 < n → 0 < iter f k n := by
  intro k
  induction k with
  | zero =>
      intro n hn
      simpa [iter] using hn
  | succ k ih =>
      intro n hn
      simpa [iter] using ih (f n) (hpos n hn)

def MinimalBad (Bad : Nat → Prop) (n : Nat) : Prop :=
  Bad n ∧ ∀ m, m < n → ¬ Bad m

theorem no_bad_of_no_minimal
    (Bad : Nat → Prop)
    (hNoMin : ∀ n, ¬ MinimalBad Bad n) :
    ∀ n, ¬ Bad n := by
  intro n
  induction n using Nat.strong_induction_on with
  | h n ih =>
      intro hbad
      have hmin : MinimalBad Bad n := by
        refine ⟨hbad, ?_⟩
        intro m hm
        exact ih m hm
      exact hNoMin n hmin

structure Exits (State : Type) where
  descent : State → Prop
  lowerMerge : State → Prop
  recurrence : State → Prop

def NoExit {State : Type} (exits : Exits State) (s : State) : Prop :=
  ¬ exits.descent s ∧ ¬ exits.lowerMerge s ∧ ¬ exits.recurrence s

def Residual {State : Type}
    (Normalized : State → Prop)
    (exits : Exits State)
    (s : State) : Prop :=
  Normalized s ∧ NoExit exits s

def PostFixed {State : Type}
    (Next : State → State → Prop)
    (S : State → Prop) : Prop :=
  ∀ s, S s → ∃ t, Next s t ∧ S t

def KernelEmpty {State : Type}
    (ResidualState : State → Prop)
    (Next : State → State → Prop) : Prop :=
  ∀ S : State → Prop,
    (∀ s, S s → ResidualState s) →
    PostFixed Next S →
    ∀ s, ¬ S s

theorem no_residual_of_kernel_empty
    {State : Type}
    (ResidualState : State → Prop)
    (Next : State → State → Prop)
    (hprogress : ∀ s, ResidualState s → ∃ t, Next s t ∧ ResidualState t)
    (hempty : KernelEmpty ResidualState Next) :
    ∀ s, ¬ ResidualState s := by
  intro s hs
  have hpf : PostFixed Next ResidualState := by
    intro x hx
    exact hprogress x hx
  have hsub : ∀ x, ResidualState x → ResidualState x := by
    intro x hx
    exact hx
  exact hempty ResidualState hsub hpf s hs

theorem no_bad_of_normalized_empty_kernel
    {State : Type}
    (Bad : Nat → Prop)
    (Normalized : State → Prop)
    (source : State → Nat)
    (Next : State → State → Prop)
    (exits : Exits State)
    (hnormalize :
      ∀ n, MinimalBad Bad n →
        ∃ s, Normalized s ∧ source s = n)
    (hminimalNoExit :
      ∀ s n,
        Normalized s →
        source s = n →
        MinimalBad Bad n →
        NoExit exits s)
    (hprogress :
      ∀ s,
        Residual Normalized exits s →
        ∃ t, Next s t ∧ Residual Normalized exits t)
    (hempty :
      KernelEmpty (Residual Normalized exits) Next) :
    ∀ n, ¬ Bad n := by
  apply no_bad_of_no_minimal Bad
  intro n hmin
  obtain ⟨s, hnorm, hsource⟩ := hnormalize n hmin
  have hno : NoExit exits s :=
    hminimalNoExit s n hnorm hsource hmin
  have hres : Residual Normalized exits s := ⟨hnorm, hno⟩
  have hnone :
      ∀ x, ¬ Residual Normalized exits x :=
    no_residual_of_kernel_empty
      (Residual Normalized exits) Next hprogress hempty
  exact hnone s hres

theorem reaches_one_of_strict_descent
    (f : Nat → Nat)
    (hpos : ∀ n, 0 < n → 0 < f n)
    (hdesc : ∀ n, 1 < n → ∃ k, iter f k n < n) :
    ∀ n, 0 < n → ∃ k, iter f k n = 1 := by
  intro n
  induction n using Nat.strong_induction_on with
  | h n ih =>
      intro hn
      cases n with
      | zero =>
          exact (Nat.lt_irrefl 0 hn).elim
      | succ m =>
          cases m with
          | zero =>
              exact ⟨0, rfl⟩
          | succ m =>
              let n' := Nat.succ (Nat.succ m)
              have hgt : 1 < n' := by
                exact Nat.succ_lt_succ (Nat.zero_lt_succ m)
              obtain ⟨k, hk⟩ := hdesc n' hgt
              have hypos : 0 < iter f k n' :=
                iter_positive f hpos k n' (Nat.zero_lt_succ _)
              obtain ⟨l, hl⟩ := ih (iter f k n') hk hypos
              refine ⟨k + l, ?_⟩
              rw [iter_add]
              exact hl

end CollatzFinal
