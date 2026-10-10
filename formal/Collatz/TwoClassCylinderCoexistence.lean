import Collatz.ThreeNPlusSevenSeparator

namespace CollatzFinal
namespace SourceProduct

/-!
V164 — TWO DISJOINT FUTURE CLASSES CAN BOTH HAVE MEMBERS IN
EACH DYADIC SOURCE RESIDUE CYLINDER.

The synthetic true Nat map G(n)=n/2 if even and (3n+7)/2 if
odd has two REAL disjoint cycles through 5 and 7 (V162).

The exact V160 source-affine construction adapts to G with
identical positive-source, residue and independent-clock checks:
for ANY target b with an explicit power-congruence hit,
one can build a real source in ANY k-bit cylinder joining b.

For b=5 and b=7, the number-theoretic fact that powers of2
enumerate units mod3^a supplies the hits whenever g is a
3-unit. A general primitive-root proof is in the V160 note
and tested exactly in finite ranges, but STILL not reified in
this Lean module: all power-hit premises below remain explicit.
Do NOT claim an unconditional Lean theorem with these omitted.

Consequence: both disjoint synthetic G future classes are
topologically dense in dyadic cylinders, given the elementary
number-theory hits. Thus even *infinite prefix coverage by
each class* cannot force actual two-clock class coalescence.

This is not the actual 3n+1 system. Collatz remains UNKNOWN.
-/

theorem v164_zero_orbit (k : Nat) :
    iter v162Map k 0 = 0 := by
  induction k with
  | zero => rfl
  | succ k ih =>
      rw [v162_iter_succ_last,ih]
      decide

/-- A REAL power target on a parity-cylinder affine chart
    gives a REAL positive source in that residue class, and
    a real future join after two independently meaningful clocks.
    Neither source convergence nor modulus surjectivity is assumed. -/
theorem v164_power_target_is_actual_two_clock_join
    (r k b L q : Nat)
    (hr : r<2^k)
    (hb : 0<b)
    (hPower : iter v162Map k r + 3^v162OddCount r k*q = 2^L*b) :
    ∃ n : Nat,
      0<n ∧ n%2^k=r ∧ iter v162Map (k+L) n=b := by
  let n := r+2^k*q
  have hEndpoint : iter v162Map k n = 2^L*b := by
    dsimp [n]
    rw [v162_exact_cylinder_affine]
    exact hPower
  have hn : 0<n := by
    by_cases he : n=0
    · have hz := v164_zero_orbit k
      rw [he,hz] at hEndpoint
      have hPos : 0<2^L*b :=
        Nat.mul_pos (Nat.pow_pos (by decide)) hb
      omega
    · exact Nat.pos_of_ne_zero he
  have hResidue : n%2^k=r := by
    dsimp [n]
    have hm : r%2^k=r := Nat.mod_eq_of_lt hr
    simp [Nat.add_mod,Nat.mul_mod,hm]
  refine ⟨n,hn,hResidue,?_⟩
  calc
    iter v162Map (k+L) n =
        iter v162Map L (iter v162Map k n) := iter_add _ _ _ _
    _ = iter v162Map L (2^L*b) := by rw [hEndpoint]
    _ = b := v162_iter_even_power L b

/-- A visible NUMBER-THEORY witness interface, not a hidden
    global Collatz hypothesis: arbitrarily large exact power-of-two
    multiples of a prescribed target lie in the affine endpoint
    congruence class. The primitive-root fact supplies it for
    b and g coprime with 3, but that lemma is not built here. -/
def V164UnboundedPowerChartHits (a b g : Nat) : Prop :=
  ∀ H : Nat, ∃ L q : Nat,
    H≤L ∧ g+3^a*q=2^L*b

/-- Under the explicitly supplied primitive-root-type number theory,
    one can construct genuinely source-attached ancestors in EVERY
    fixed parity cylinder, at arbitrarily late TARGET CLOCKS.
    This is a non-circular construction (it never assumes b converges),
    and it does not bound the constructed source size. -/
theorem v164_all_prefix_real_future_ancestors_of_power_hits
    (r k b : Nat) (hr : r<2^k) (hb : 0<b)
    (hHits : V164UnboundedPowerChartHits
      (v162OddCount r k) b (iter v162Map k r)) :
    ∀ H : Nat,
      ∃ n L : Nat,
        H≤L ∧ 0<n ∧ n%2^k=r ∧
        iter v162Map (k+L) n=b := by
  intro H
  obtain ⟨L,q,hL,hPower⟩ := hHits H
  obtain ⟨n,hn,hres,hJoin⟩ :=
    v164_power_target_is_actual_two_clock_join
      r k b L q hr hb hPower
  exact ⟨n,L,hL,hn,hres,hJoin⟩


/-- Genuine two-clock eventual meeting for the distinct synthetic
    G7 system, NOT equality of binary residue classes. -/
def V164FutureMeet (n m : Nat) : Prop :=
  ∃ i j : Nat, iter v162Map i n = iter v162Map j m

theorem v164_meet_symm {n m : Nat}
    (hm : V164FutureMeet n m) :
    V164FutureMeet m n := by
  obtain ⟨i,j,hij⟩ := hm
  exact ⟨j,i,hij.symm⟩

theorem v164_meet_trans {n m p : Nat}
    (hm : V164FutureMeet n m)
    (hp : V164FutureMeet m p) :
    V164FutureMeet n p := by
  obtain ⟨i,j,hij⟩ := hm
  obtain ⟨k,l,hkl⟩ := hp
  refine ⟨i+k,l+j,?_⟩
  calc
    iter v162Map (i+k) n =
        iter v162Map k (iter v162Map i n) :=
      iter_add v162Map i k n
    _ = iter v162Map k (iter v162Map j m) := by rw [hij]
    _ = iter v162Map j (iter v162Map k m) := by
      calc
        _ = iter v162Map (j+k) m :=
          (iter_add v162Map j k m).symm
        _ = iter v162Map (k+j) m := by rw [Nat.add_comm]
        _ = iter v162Map j (iter v162Map k m) :=
          iter_add v162Map k j m
    _ = iter v162Map j (iter v162Map l p) := by rw [hkl]
    _ = iter v162Map (l+j) p :=
      (iter_add v162Map l j p).symm

/-- Exact pointwise coexistence with TWO explicit arithmetic
    power witnesses. No handwaving about continuous limits or
    2-adic sources; both witnesses are genuine positive naturals. -/
theorem v164_two_distinct_future_classes_same_prefix
    (k r LA qA LB qB : Nat)
    (hr : r<2^k)
    (hPowerA :
      iter v162Map k r + 3^v162OddCount r k*qA=2^LA*7)
    (hPowerB :
      iter v162Map k r + 3^v162OddCount r k*qB=2^LB*5) :
    ∃ x y : Nat,
      0<x ∧ 0<y ∧
      x%2^k=r ∧ y%2^k=r ∧
      ¬ V164FutureMeet x y := by
  obtain ⟨x,hx,hxmod,hxJoin⟩ :=
    v164_power_target_is_actual_two_clock_join
      r k 7 LA qA hr (by decide) hPowerA
  obtain ⟨y,hy,hymod,hyJoin⟩ :=
    v164_power_target_is_actual_two_clock_join
      r k 5 LB qB hr (by decide) hPowerB
  refine ⟨x,y,hx,hy,hxmod,hymod,?_⟩
  intro hxy
  have h7x : V164FutureMeet 7 x := by
    refine ⟨0,k+LA,?_⟩
    simpa [iter] using hxJoin.symm
  have hy5 : V164FutureMeet y 5 := by
    refine ⟨k+LB,0,?_⟩
    simpa [iter] using hyJoin
  have h75 := v164_meet_trans (v164_meet_trans h7x hxy) hy5
  exact v162_disjoint_actual_positive_future_classes h75

/-- All witnesses may be arbitrarily late, if the arithmetic
    power hit sequences for both cycle targets are supplied.
    Still NOT a claim that all positive naturals belong to either
    class or that the classes coincide. -/
theorem v164_both_classes_in_prefix_of_unbounded_power_hits
    (k r : Nat) (hr : r<2^k)
    (hA : V164UnboundedPowerChartHits
      (v162OddCount r k) 7 (iter v162Map k r))
    (hB : V164UnboundedPowerChartHits
      (v162OddCount r k) 5 (iter v162Map k r)) :
    ∀ H : Nat,
      ∃ x y LA LB : Nat,
        H≤LA ∧ H≤LB ∧ 0<x ∧ 0<y ∧
        x%2^k=r ∧ y%2^k=r ∧
        ¬ V164FutureMeet x y := by
  intro H
  obtain ⟨LA,qA,hLA,hPowerA⟩ := hA H
  obtain ⟨LB,qB,hLB,hPowerB⟩ := hB H
  obtain ⟨x,y,hx,hy,hxmod,hymod,hnot⟩ :=
    v164_two_distinct_future_classes_same_prefix
      k r LA qA LB qB hr hPowerA hPowerB
  exact ⟨x,y,LA,LB,hLA,hLB,hx,hy,hxmod,hymod,hnot⟩

#print axioms v164_power_target_is_actual_two_clock_join
#print axioms v164_all_prefix_real_future_ancestors_of_power_hits
#print axioms v164_meet_trans
#print axioms v164_two_distinct_future_classes_same_prefix
#print axioms v164_both_classes_in_prefix_of_unbounded_power_hits

end SourceProduct
end CollatzFinal
