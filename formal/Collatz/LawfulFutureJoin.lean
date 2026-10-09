import Collatz.Shortcut

namespace CollatzFinal

/-!
A verified *source-indexed two-clock future join* is the minimal protected
Collatz capability. It does NOT assign a descent rank to T's quotient, and
a failed grammar search produces no mathematical negative theorem.
-/

structure LawfulFutureJoin where
  source : Nat
  earlier : Nat
  sourceClock : Nat
  earlierClock : Nat
  positive : 0 < earlier
  smaller : earlier < source
  common : iter shortcut sourceClock source =
           iter shortcut earlierClock earlier

namespace LawfulFutureJoin

/-- Existing V65/V66-style lower-source consequence, not a new exit kind. -/
theorem toLowerMerge (w : LawfulFutureJoin) :
    LowerMerge shortcut w.source w.earlier :=
  ⟨w.smaller, w.sourceClock, w.earlierClock, w.common⟩

/-- The original source and the two original clocks remain explicit.
    A common suffix shifts BOTH clocks without inventing a new witness. -/
theorem common_suffix (w : LawfulFutureJoin) (t : Nat) :
    iter shortcut (w.sourceClock + t) w.source =
    iter shortcut (w.earlierClock + t) w.earlier := by
  calc
    iter shortcut (w.sourceClock + t) w.source =
        iter shortcut t (iter shortcut w.sourceClock w.source) :=
      iter_add shortcut w.sourceClock t w.source
    _ = iter shortcut t (iter shortcut w.earlierClock w.earlier) :=
      congrArg (iter shortcut t) w.common
    _ = iter shortcut (w.earlierClock + t) w.earlier :=
      (iter_add shortcut w.earlierClock t w.earlier).symm

/-- The two-clock algebra behind lawful consequence reclosure.
    n joins p at clocks (a,b), and p joins q at (c,d);
    n then joins q at clocks (a+c,d+b). -/
theorem compose_meets
    {n p q a b c d : Nat}
    (hnp : iter shortcut a n = iter shortcut b p)
    (hpq : iter shortcut c p = iter shortcut d q) :
    iter shortcut (a + c) n = iter shortcut (d + b) q := by
  calc
    iter shortcut (a + c) n = iter shortcut c (iter shortcut a n) :=
      iter_add shortcut a c n
    _ = iter shortcut c (iter shortcut b p) :=
      congrArg (iter shortcut c) hnp
    _ = iter shortcut (b + c) p :=
      (iter_add shortcut b c p).symm
    _ = iter shortcut (c + b) p := by rw [Nat.add_comm]
    _ = iter shortcut b (iter shortcut c p) :=
      iter_add shortcut c b p
    _ = iter shortcut b (iter shortcut d q) :=
      congrArg (iter shortcut b) hpq
    _ = iter shortcut (d + b) q :=
      (iter_add shortcut d b q).symm

/-- Monotone certified consequence closure: never execute a new orbit
    merely to rediscover the intermediate already-qualified class merger. -/
def compose (first second : LawfulFutureJoin)
    (hlink : second.source = first.earlier) : LawfulFutureJoin :=
  { source := first.source
    earlier := second.earlier
    sourceClock := first.sourceClock + second.sourceClock
    earlierClock := second.earlierClock + first.earlierClock
    positive := second.positive
    smaller := by
      have hlt : second.earlier < first.earlier := by
        simpa only [hlink] using second.smaller
      exact Nat.lt_trans hlt first.smaller
    common := by
      have hsecond :
          iter shortcut second.sourceClock first.earlier =
          iter shortcut second.earlierClock second.earlier := by
        rw [← hlink]
        exact second.common
      exact compose_meets first.common hsecond }

/-- Any admitted source-indexed certificate refutes the hypothesis that
    its source is the LEAST nonconvergent natural. No global theorem assumed. -/
theorem refutes_minimal_bad (w : LawfulFutureJoin)
    (hmin : MinimalBad (fun n => ¬ CollatzGood n) w.source) : False :=
  (lower_merge_closes_minimal_collatz_bad hmin w.earlier) w.toLowerMerge

/-- Actual *asynchronous* source-relative join: T^6(11)=T(3)=5. -/
def source11_to3 : LawfulFutureJoin :=
  { source := 11, earlier := 3
    sourceClock := 6, earlierClock := 1
    positive := by decide
    smaller := by decide
    common := by decide }

/-- A separately certified smaller-source capability for source 3. -/
def source3_to2 : LawfulFutureJoin :=
  { source := 3, earlier := 2
    sourceClock := 4, earlierClock := 0
    positive := by decide
    smaller := by decide
    common := by decide }

/-- Reclosure reuses two independent valid certificates: 11 joins 2 at
    clocks (10,1), including the terminal phase difference. -/
theorem source11_to2_by_reclosure :
    (compose source11_to3 source3_to2 (by decide)).sourceClock = 10 ∧
    (compose source11_to3 source3_to2 (by decide)).earlierClock = 1 ∧
    LowerMerge shortcut 11 2 := by
  refine ⟨rfl, rfl, ?_⟩
  exact (compose source11_to3 source3_to2 (by decide)).toLowerMerge

#print axioms LawfulFutureJoin.toLowerMerge
#print axioms LawfulFutureJoin.common_suffix
#print axioms LawfulFutureJoin.compose_meets
#print axioms LawfulFutureJoin.compose
#print axioms LawfulFutureJoin.refutes_minimal_bad
#print axioms LawfulFutureJoin.source11_to2_by_reclosure

end LawfulFutureJoin
end CollatzFinal
