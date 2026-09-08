import Std
import Lean.Elab.Tactic.Omega

/-!
A bounded scalar conservation-law experiment, not a Navier--Stokes theorem.
The four-cell and six-cell vector fields are conservative flux differences.
All identities are over arbitrary integer states and an arbitrary flux F.
No finite test is used to justify a universal theorem.
-/

namespace FluidClosure

structure State4 where
  a : Int
  b : Int
  c : Int
  d : Int
  deriving Repr

abbrev Coarse := Int × Int

def observe4 (s : State4) : Coarse := (s.a + s.b, s.c + s.d)

def dynamics4 (F : Int → Int) (s : State4) : State4 :=
  ⟨F s.d - F s.a, F s.a - F s.b,
   F s.b - F s.c, F s.c - F s.d⟩

def delta4 (F : Int → Int) (s : State4) : Int := F s.d - F s.b

def close (d : Int) : Coarse := (d, -d)

theorem projected4 (F : Int → Int) (s : State4) :
    observe4 (dynamics4 F s) = close (delta4 F s) := by
  rcases s with ⟨a,b,c,d⟩
  apply Prod.ext <;> dsimp [observe4, dynamics4, close, delta4] <;> omega

/-- The observed state alone does not determine its projected derivative. -/
def witnessA : State4 := ⟨0,1,0,0⟩
def witnessB : State4 := ⟨1,0,0,0⟩
def square (x : Int) : Int := x*x

theorem same_old_observation : observe4 witnessA = observe4 witnessB := by
  decide

theorem different_projected_derivative :
    observe4 (dynamics4 square witnessA) ≠
      observe4 (dynamics4 square witnessB) := by
  decide

def Repair4 (F : Int → Int) (s t : State4) : Prop :=
  observe4 s = observe4 t ∧ delta4 F s = delta4 F t

/-- The repaired observation preserves the protected one-step consequence. -/
theorem repair_sufficient (F : Int → Int) {s t : State4}
    (h : Repair4 F s t) :
    observe4 (dynamics4 F s) = observe4 (dynamics4 F t) := by
  rw [projected4, projected4, h.2]

/-- Every relation preserving the old observation and this consequence
    must refine the repaired relation.  No choice of coordinates is assumed. -/
theorem repair_necessary (F : Int → Int)
    (R : State4 → State4 → Prop)
    (hOld : ∀ s t, R s t → observe4 s = observe4 t)
    (hConsequence : ∀ s t, R s t →
      observe4 (dynamics4 F s) = observe4 (dynamics4 F t)) :
    ∀ s t, R s t → Repair4 F s t := by
  intro s t h
  refine ⟨hOld s t h, ?_⟩
  have hd := hConsequence s t h
  rw [projected4, projected4] at hd
  exact congrArg Prod.fst hd

/-- The smallest one-step refinement is not generally a dynamical closure.
    Two states can agree on both the old observation and the new flux
    contrast, yet require different derivatives of that contrast. -/
def witnessC : State4 := ⟨2,-1,0,0⟩

def squareContrastDerivative (s : State4) : Int :=
  2*s.d*(square s.c - square s.d) -
    2*s.b*(square s.a - square s.b)

theorem square_contrast_derivative (s : State4) :
    squareContrastDerivative s =
      2*s.d*(dynamics4 square s).d - 2*s.b*(dynamics4 square s).b := by
  rfl

theorem same_first_refinement : Repair4 square witnessA witnessC := by
  unfold Repair4
  constructor <;> decide

theorem different_second_consequence :
    squareContrastDerivative witnessA ≠ squareContrastDerivative witnessC := by
  decide

/-! A held-out six-cell grid.  Its three-cell block sums telescope in
    exactly the same way, for any flux, including cubic flux. -/
structure State6 where
  a : Int
  b : Int
  c : Int
  d : Int
  e : Int
  f : Int
  deriving Repr

def observe6 (s : State6) : Coarse :=
  (s.a+s.b+s.c, s.d+s.e+s.f)

def dynamics6 (F : Int → Int) (s : State6) : State6 :=
  ⟨F s.f-F s.a, F s.a-F s.b, F s.b-F s.c,
   F s.c-F s.d, F s.d-F s.e, F s.e-F s.f⟩

def delta6 (F : Int → Int) (s : State6) : Int := F s.f-F s.c

theorem projected6 (F : Int → Int) (s : State6) :
    observe6 (dynamics6 F s) = close (delta6 F s) := by
  rcases s with ⟨a,b,c,d,e,f⟩
  apply Prod.ext <;> dsimp [observe6, dynamics6, close, delta6] <;> omega

def cube (x : Int) : Int := x*x*x

def witness6A : State6 := ⟨0,0,1,0,0,0⟩
def witness6B : State6 := ⟨1,0,0,0,0,0⟩

theorem six_old_obstruction :
    observe6 witness6A = observe6 witness6B ∧
    observe6 (dynamics6 cube witness6A) ≠
      observe6 (dynamics6 cube witness6B) := by
  decide

theorem six_repair_sufficient (F : Int → Int) {s t : State6}
    (h : observe6 s = observe6 t ∧ delta6 F s = delta6 F t) :
    observe6 (dynamics6 F s) = observe6 (dynamics6 F t) := by
  rw [projected6, projected6, h.2]

#print axioms projected4
#print axioms repair_sufficient
#print axioms repair_necessary
#print axioms different_projected_derivative
#print axioms same_first_refinement
#print axioms different_second_consequence
#print axioms projected6
#print axioms six_old_obstruction
#print axioms six_repair_sufficient

end FluidClosure
