import VerifiedDevelopmentalNavigation.DevelopmentCertificate

/-!
This file instantiates the unchanged upstream VDN definitions with a finite
source-hash transition table. It does not execute or verify Python.
-/
namespace V54

open VerifiedDevelopmentalNavigation

inductive NativeOutcome where
  | passed | failed | timedOut | error | unknown
  deriving DecidableEq, Repr

structure Candidate where
  sourceSha256 : String
  outcome : NativeOutcome
  deriving DecidableEq, Repr

structure Snapshot where
  start : String
  warm : String
  target : String
  startOutcome : NativeOutcome
  warmOutcome : NativeOutcome
  targetOutcome : NativeOutcome
  cold : List Candidate
  deriving DecidableEq, Repr

def candidateOutcome : List Candidate → String → NativeOutcome
  | [], _ => .unknown
  | c :: cs, x => if c.sourceSha256 = x then c.outcome else candidateOutcome cs x

def outcome (s : Snapshot) (x : String) : NativeOutcome :=
  if x = s.start then s.startOutcome
  else if x = s.warm then s.warmOutcome
  else if x = s.target then s.targetOutcome
  else candidateOutcome s.cold x

abbrev OldAction (s : Snapshot) := Fin s.cold.length

inductive AcquiredAction where
  | O1 | O2
  deriving DecidableEq, Repr

abbrev NewAction (s : Snapshot) := Sum (OldAction s) AcquiredAction

def oldWorld (s : Snapshot) : World String Unit (OldAction s) NativeOutcome where
  observe := fun _ x => outcome s x
  step := fun a x =>
    if x = s.start then some (s.cold.get a).sourceSha256 else none

def newWorld (s : Snapshot) : World String Unit (NewAction s) NativeOutcome where
  observe := fun _ x => outcome s x
  step := fun a x => match a with
    | .inl old => (oldWorld s).step old x
    | .inr .O1 => if x = s.start then some s.warm else none
    | .inr .O2 => if x = s.warm then some s.target else none

def oldBoundary (s : Snapshot) : World.TraceBoundary (A := OldAction s) :=
  fun trace => trace.length ≤ 1

def oldCover (s : Snapshot) : List (List (OldAction s)) :=
  [] :: (List.finRange s.cold.length).map (fun a => [a])

theorem oldCover_complete (s : Snapshot) :
    World.CompleteCover (oldBoundary s) (oldCover s) := by
  intro trace hb
  cases trace with
  | nil => simp [oldCover]
  | cons a tail =>
    cases tail with
    | nil =>
      simp only [oldCover, List.mem_cons, List.mem_map]
      exact Or.inr ⟨a, List.mem_finRange a, rfl⟩
    | cons b tail =>
      simp [oldBoundary] at hb

def extension (s : Snapshot) : ActionExtension (oldWorld s) (newWorld s) where
  embed := Sum.inl
  step_preserved := fun _ _ => rfl

theorem newWitness (s : Snapshot) :
    (newWorld s).Reachable s.start s.target := by
  refine ⟨[Sum.inr .O1, Sum.inr .O2], ?_⟩
  simp [World.run, newWorld]

theorem oldCover_blocked (s : Snapshot)
    (hstart : s.start ≠ s.target)
    (hcold : ∀ c ∈ s.cold, c.sourceSha256 ≠ s.target) :
    ∀ trace ∈ oldCover s,
      (oldWorld s).run trace s.start ≠ some s.target := by
  intro trace ht
  simp only [oldCover, List.mem_cons, List.mem_map] at ht
  rcases ht with hnil | ⟨a, _, ha⟩
  · subst trace
    simpa [World.run] using hstart
  · subst trace
    have hc := hcold (s.cold.get a) (List.get_mem _ _)
    simpa [World.run, oldWorld] using hc

theorem coldExcludesTarget_of_check (s : Snapshot)
    (h : s.cold.all (fun c => decide (c.sourceSha256 ≠ s.target)) = true) :
    ∀ c ∈ s.cold, c.sourceSha256 ≠ s.target := by
  simpa only [List.all_eq_true, decide_eq_true_eq] using h

theorem coldNonpassing_of_check (s : Snapshot)
    (h : s.cold.all (fun c => decide (c.outcome ≠ NativeOutcome.passed)) = true) :
    ∀ c ∈ s.cold, c.outcome ≠ NativeOutcome.passed := by
  simpa only [List.all_eq_true, decide_eq_true_eq] using h

theorem candidateOutcome_nonpassing (cs : List Candidate)
    (h : ∀ c ∈ cs, c.outcome ≠ NativeOutcome.passed) (x : String) :
    candidateOutcome cs x ≠ NativeOutcome.passed := by
  induction cs with
  | nil => simp [candidateOutcome]
  | cons c cs ih =>
    simp only [candidateOutcome]
    split
    · exact h c (by simp)
    · exact ih (fun d hd => h d (by simp [hd]))

theorem outcome_nonpassing (s : Snapshot)
    (hs : s.startOutcome ≠ NativeOutcome.passed)
    (hw : s.warmOutcome ≠ NativeOutcome.passed)
    (hc : ∀ c ∈ s.cold, c.outcome ≠ NativeOutcome.passed)
    (x : String) (hx : x ≠ s.target) :
    outcome s x ≠ NativeOutcome.passed := by
  simp only [outcome]
  split
  · exact hs
  · split
    · exact hw
    · simpa only [if_neg hx] using candidateOutcome_nonpassing s.cold hc x

/-- All surviving outcomes in the old one-rewrite table lack a recorded pass.
This is about the supplied observation table, including explicit timeouts. -/
theorem oldBoundary_no_recorded_pass (s : Snapshot)
    (hstart : s.start ≠ s.target)
    (hexclude : ∀ c ∈ s.cold, c.sourceSha256 ≠ s.target)
    (hs : s.startOutcome ≠ NativeOutcome.passed)
    (hw : s.warmOutcome ≠ NativeOutcome.passed)
    (hc : ∀ c ∈ s.cold, c.outcome ≠ NativeOutcome.passed) :
    ∀ trace, oldBoundary s trace → ∀ x,
      (oldWorld s).run trace s.start = some x →
      (oldWorld s).observe () x ≠ NativeOutcome.passed := by
  intro trace hb x hrun
  have ht := oldCover_complete s trace hb
  simp only [oldCover, List.mem_cons, List.mem_map] at ht
  rcases ht with hnil | ⟨a, _, ha⟩
  · subst trace
    have hx : s.start = x := by simpa [World.run] using hrun
    subst x
    exact outcome_nonpassing s hs hw hc s.start hstart
  · subst trace
    have hx : (s.cold.get a).sourceSha256 = x := by
      simpa [World.run, oldWorld] using hrun
    subst x
    exact outcome_nonpassing s hs hw hc _ (hexclude _ (List.get_mem _ _))

def certificate (s : Snapshot)
    (hstart : s.start ≠ s.target)
    (hcold : ∀ c ∈ s.cold, c.sourceSha256 ≠ s.target) :
    CapabilityPhaseChangeCertificate
      (oldWorld s) (newWorld s) s.start s.target where
  boundary := oldBoundary s
  cover := oldCover s
  complete := oldCover_complete s
  blocked := oldCover_blocked s hstart hcold
  extension := extension s
  witness := newWitness s

theorem boundedPhaseChange (s : Snapshot)
    (hstart : s.start ≠ s.target)
    (hcold : ∀ c ∈ s.cold, c.sourceSha256 ≠ s.target) :
    (¬ (oldWorld s).ReachableWithin (oldBoundary s) s.start s.target) ∧
      (newWorld s).Reachable s.start s.target :=
  (certificate s hstart hcold).phase_change

theorem retainsOldCapability (s : Snapshot) {x y : String}
    (h : (oldWorld s).Reachable x y) : (newWorld s).Reachable x y :=
  (extension s).reachability_monotone h

end V54
