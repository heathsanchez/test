import Collatz.DensityAmplificationClosure
import Collatz.RetroactiveFutureQuotient

namespace CollatzFinal
namespace SourceProduct

/-!
V169 — ORDINARY-TO-SHORTCUT TIMED TARGET BRIDGE AND COMPONENT LOWER BOUND.

This is an honest two-part frontier:
  (A) UNCONDITIONALLY, when b % 3 = 2, any ordinary
      Collatz orbit reaching b in <= H steps also reaches EXACT
      b along the true shortcut in <= H steps. The ordinary
      odd intermediate 3n+1 is 1 (mod 3), so a 2 (mod 3) target
      can only be encountered at a shortcut-state boundary.
  (B) A hypothetical bad b in that residue class, plus an
      EXACT SOURCE-AND-CLOCK-COMPLETE finite future ledger,
      forces a *single* unseeded future component to contain
      every ordinary predecessor reaching b within H steps.

A timed positive-natural-density target input (such as the
September 2026 WordCertDensity Shaik preprint) would upgrade
(B) into a MACROSCOPIC unseeded component at dyadic heights
and clock H(k)=8k. Its ordinary-step logarithmic source
requires an independent proof import, with c=11 satisfying
11 > 3/log(4/3) and 11*log(2) < 8.

The conjecture then follows IF a genuinely independent
all-scale no-giant inequality holds. That inequality is not
proved here. V151 asks for ALL uncertified mass to vanish;
the new proposed target asks ONLY for the largest unseeded
future component to be negligible.

The weighted V168B S(40)->S(60) reduction is a ONE-block
gain, not an all-scale argument. Nothing here iterates it.
GLOBAL COLLATZ UNKNOWN — NO QED.
-/

/-- The exact ordinary map already used by V150 (no accidental
    substitution of the shortcut at odd intermediate clocks). -/
theorem v169_even_ordinary_is_shortcut
    (n : Nat) (he : n%2=0) :
    v150Ordinary n = shortcut n := by
  simp [v150Ordinary, shortcut, he]

/-- For an odd source, TWO ordinary steps equal ONE actual
    shortcut step: n -> 3n+1 -> (3n+1)/2. -/
theorem v169_odd_two_ordinary_steps
    (n : Nat) (hn : n%2=1) :
    iter v150Ordinary 2 n = shortcut n := by
  have hodd : n%2≠0 := by omega
  have hev : (3*n+1)%2=0 := by omega
  have ho : v150Ordinary n=3*n+1 := by
    simp [v150Ordinary,hodd]
  have ht : shortcut n=(3*n+1)/2 := by
    simp [shortcut,hodd]
  change v150Ordinary (v150Ordinary n) = shortcut n
  rw [ho,ht]
  simp [v150Ordinary,hev]

/-- ALL ordinary hits of a 2-mod-3 target are genuine shortcut
    hits, with no increase in the hitting-clock upper bound.
    This is unconditional and does not assume convergence. -/
theorem v169_ordinary_to_shortcut_unit_target :
    ∀ t n b : Nat,
      b%3=2 →
      iter v150Ordinary t n=b →
      ∃ i : Nat, i≤t ∧ iter shortcut i n=b := by
  intro t
  induction t using Nat.strongRecOn with
  | ind t ih =>
      intro n b hb h
      cases t with
      | zero =>
          exact ⟨0,by omega,by simpa [iter] using h⟩
      | succ u =>
          by_cases he : n%2=0
          · have hstep := v169_even_ordinary_is_shortcut n he
            have hrest : iter v150Ordinary u (shortcut n)=b := by
              simpa only [iter,hstep] using h
            obtain ⟨i,hi,hiHit⟩ :=
              ih u (by omega) (shortcut n) b hb hrest
            refine ⟨i+1,by omega,?_⟩
            simpa only [iter] using hiHit
          · cases u with
            | zero =>
                have hfirst : v150Ordinary n=b := by
                  simpa [iter] using h
                have hodd : v150Ordinary n=3*n+1 := by
                  simp [v150Ordinary,he]
                rw [hodd] at hfirst
                omega
            | succ j =>
                have hodd : n%2=1 := by omega
                have htwo := v169_odd_two_ordinary_steps n hodd
                have hLong : iter v150Ordinary (2+j) n=b := by
                  have hClock : (j+1)+1 = 2+j := by omega
                  rw [← hClock]
                  exact h
                rw [iter_add,htwo] at hLong
                obtain ⟨i,hi,hiHit⟩ :=
                  ih j (by omega) (shortcut n) b hb hLong
                refine ⟨i+1,by omega,?_⟩
                simpa only [iter] using hiHit

/-- Finite executable endpoint-hit relations; the Clock k here
    refers to the true original source, never a quotient ghost. -/
def V169OrdinaryTimedHit (b H n : Nat) : Prop :=
  ∃ t : Nat, t≤H ∧ iter v150Ordinary t n=b

def V169ShortcutTimedHit (b H n : Nat) : Prop :=
  ∃ t : Nat, t≤H ∧ iter shortcut t n=b

theorem v169_timed_ordinary_hit_to_actual_shortcut
    (b H n : Nat) (hb : b%3=2)
    (hh : V169OrdinaryTimedHit b H n) :
    V169ShortcutTimedHit b H n := by
  obtain ⟨t,ht,hOrd⟩ := hh
  obtain ⟨i,hi,hShort⟩ :=
    v169_ordinary_to_shortcut_unit_target t n b hb hOrd
  exact ⟨i,by omega,hShort⟩

/-- Every such actual meeting already admits a genuine two-clock
    future-equivalence witness, independent of target termination. -/
theorem v169_timed_hit_is_genuine_future_join
    (b H n : Nat) (h : V169ShortcutTimedHit b H n) :
    V155FutureMeet n b := by
  obtain ⟨i,_hi,heq⟩ := h
  exact ⟨i,0,by simpa [iter] using heq⟩

/-- A source may be in an unseeded component even though its
    future has been computed and unioned with many other sources.
    No global divergence predicate is decided by the finite ledger. -/
def V169UnseededComponent
    (E : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (b n : Nat) : Prop :=
  0<n ∧ V168Path E n b ∧ ¬ V168LedgerCloses E seeds n

theorem v169_bad_target_cannot_have_a_terminal_seeded_path
    (E : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (b n : Nat)
    (hBad : ¬ CollatzGood b)
    (hPath : V168Path E n b) :
    ¬ V168LedgerCloses E seeds n := by
  intro hLedger
  have hGoodN : CollatzGood n :=
    v168_every_ledger_closure_is_genuine E seeds n hLedger
  have hMeetN1 : V155FutureMeet n 1 :=
    (v155_future_meets_one_iff_good n).mpr hGoodN
  have hMeetBN : V155FutureMeet b n :=
    v155_future_meet_symm (v168_path_sound E hPath)
  have hMeetB1 : V155FutureMeet b 1 :=
    v155_future_meet_trans hMeetBN hMeetN1
  exact hBad ((v155_future_meets_one_iff_good b).mp hMeetB1)

/-- Sound finite-clock coverage criterion for an independently
    constructed exact two-clock ledger. A FULL ledger can be
    enumerated without knowing which components will converge. -/
def V169TimedLedgerComplete
    (E : List V168TwoClockEdge)
    (b H X : Nat) : Prop :=
  ∀ n, 0<n → n<X →
    V169ShortcutTimedHit b H n → V168Path E n b

/-- Counting only positive sources with a tested ordinary hit. -/
noncomputable def v169OrdinaryTimedCount (b H X : Nat) : Nat := by
  classical
  exact v150Count
    (fun n => 0<n ∧ V169OrdinaryTimedHit b H n) X

/-- Counting ALL source vertices in a specified unseeded
    genuine future component, without a convergence oracle. -/
noncomputable def v169UnseededComponentCount
    (E : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (b X : Nat) : Nat := by
  classical
  exact v150Count (V169UnseededComponent E seeds b) X

/-- An actual bad 2-mod-3 target forces the finite total population
    of its TIMED ordinary predecessors into ONE and the SAME
    as-yet-unseeded actual two-clock component.

    It does not assert the existence of a bad target or a positive
    timed-hitting density. It is a genuine finite count inequality. -/
theorem v169_bad_target_forces_one_unseeded_component
    (E : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (b H X : Nat)
    (hb : b%3=2)
    (hBad : ¬ CollatzGood b)
    (hComplete : V169TimedLedgerComplete E b H X) :
    v169OrdinaryTimedCount b H X ≤
      v169UnseededComponentCount E seeds b X := by
  classical
  change
    v150Count
      (fun n => 0<n ∧ V169OrdinaryTimedHit b H n) X ≤
    v150Count (V169UnseededComponent E seeds b) X
  apply v150_count_monotone_below
  intro n hn hOrd
  have hShort :=
    v169_timed_ordinary_hit_to_actual_shortcut b H n hb hOrd.2
  have hPath := hComplete n hOrd.1 hn hShort
  exact ⟨hOrd.1,hPath,
    v169_bad_target_cannot_have_a_terminal_seeded_path
      E seeds b n hBad hPath⟩

/-- EXTERNAL INPUT, NOT AN AXIOM:
    positive natural density of TIMED ordinary predecessors,
    in a clock H(k), for each 2-mod-3 target b.

    Shaik's documented result with c=11, ordinary hits at
    <=11*Real.log n, translates to H(k)=8k for n<2^k
    because 11*log(2)<8. The Mathlib theorem, natural-density
    liminf bridge and log inequality have NOT been imported here.
-/
def V169TimedTargetDensity (H : Nat → Nat) : Prop :=
  ∀ b : Nat, b%3=2 →
    ∃ q X0 : Nat, 0<q ∧
      ∀ k : Nat, X0≤2^k →
        2^k ≤ q*v169OrdinaryTimedCount b (H k) (2^k)

/-- An exact full finite-clock source graph is built without
    treating uncertified components as known divergent.
    Quantifying all b is a CHECKABLE recording criterion. -/
def V169CompleteSourceLedger
    (E : Nat → List V168TwoClockEdge)
    (H : Nat → Nat) : Prop :=
  ∀ k b : Nat, b<2^k →
    V169TimedLedgerComplete (E k) b (H k) (2^k)

/-- Proposed quantitative breakthrough, NOT proved:
    even the LARGEST unseeded finite future component
    eventually contains less than any fixed fraction of
    all sources at some arbitrarily large dyadic cutoff.
    Much weaker-looking than vanishing TOTAL uncertified mass,
    but still a major open arithmetic obligation. -/
def V169SparseNoGiantComponent
    (E : Nat → List V168TwoClockEdge)
    (seeds : Nat → List V168TerminalSeed) : Prop :=
  ∀ q X0 : Nat, 0<q →
    ∃ k : Nat, X0≤2^k ∧
      ∀ b : Nat, 0<b → b<2^k →
        q*v169UnseededComponentCount
          (E k) (seeds k) b (2^k) < 2^k

/-- No fake QED:
    from the external TIMED targetwise positive-density input,
    PLUS independently recorded complete source ledgers,
    PLUS the currently UNKNOWN sparse no-giant estimate,
    full Collatz would follow. No premise is hidden.

    The proof uses the V150 *unconditional* least-bad successor
    b=T(m) congruent 2 mod3, so the ordinary/shortcut clock
    conversion applies without a spurious endpoint phase. -/
theorem v169_collatz_of_timed_density_and_no_giant
    (H : Nat → Nat)
    (E : Nat → List V168TwoClockEdge)
    (seeds : Nat → List V168TerminalSeed)
    (hDensity : V169TimedTargetDensity H)
    (hComplete : V169CompleteSourceLedger E H)
    (hNoGiant : V169SparseNoGiantComponent E seeds) :
    ∀ n : Nat, 0<n → CollatzGood n := by
  have hNoMin : ∀ m : Nat, ¬ MinimalBad PositiveBad m := by
    intro m hMin
    obtain ⟨hBadB,hModB⟩ :=
      v150_minimal_bad_has_nonthree_bad_successor hMin
    let b := shortcut m
    obtain ⟨q,X0,hq,hTimedLower⟩ :=
      hDensity b hModB
    obtain ⟨k,hX,hGiantUpper⟩ :=
      hNoGiant q (X0+b+1) hq
    have hbBound : b<2^k := by omega
    have hX0 : X0≤2^k := by omega
    have hCompleteB :
        V169TimedLedgerComplete
          (E k) b (H k) (2^k) :=
      hComplete k b hbBound
    have hCount :=
      v169_bad_target_forces_one_unseeded_component
        (E k) (seeds k) b (H k) (2^k)
        hModB hBadB.2 hCompleteB
    have hWeighted :=
      Nat.mul_le_mul_left q hCount
    have hLower := hTimedLower k hX0
    have hUpper :=
      hGiantUpper b hBadB.1 hbBound
    omega
  have hNoBad := no_bad_of_no_minimal PositiveBad hNoMin
  intro n hn
  apply Classical.byContradiction
  intro hBad
  exact hNoBad n ⟨hn,hBad⟩

#print axioms v169_even_ordinary_is_shortcut
#print axioms v169_odd_two_ordinary_steps
#print axioms v169_ordinary_to_shortcut_unit_target
#print axioms v169_timed_ordinary_hit_to_actual_shortcut
#print axioms v169_timed_hit_is_genuine_future_join
#print axioms v169_bad_target_cannot_have_a_terminal_seeded_path
#print axioms v169_bad_target_forces_one_unseeded_component
#print axioms v169_collatz_of_timed_density_and_no_giant

end SourceProduct
end CollatzFinal
