import Std

/-! A bounded physical closure experiment. The generator supplies finite
counterexamples; Lean independently checks the algebraic statements. -/
namespace FluidClosure

structure Vector2 where
  x : Int
  y : Int
  deriving DecidableEq, Repr

structure Tensor2 where
  xx : Int
  xy : Int
  yy : Int
  deriving DecidableEq, Repr

theorem Tensor2.ext {a b : Tensor2}
    (hxx : a.xx = b.xx) (hxy : a.xy = b.xy) (hyy : a.yy = b.yy) : a = b := by
  cases a
  cases b
  simp_all

structure Field where
  ax : Int
  ay : Int
  bx : Int
  bY : Int
  deriving DecidableEq, Repr

/-- Unnormalised two-cell mean and symmetric quadratic flux. -/
def mean (u : Field) : Vector2 := ⟨u.ax + u.bx, u.ay + u.bY⟩
def flux (u : Field) : Tensor2 :=
  ⟨u.ax*u.ax + u.bx*u.bx, u.ax*u.ay + u.bx*u.bY,
   u.ay*u.ay + u.bY*u.bY⟩

/-- The three independent components of twice the usual Reynolds stress. -/
def stress (u : Field) : Tensor2 :=
  ⟨2*(flux u).xx - (mean u).x*(mean u).x,
   2*(flux u).xy - (mean u).x*(mean u).y,
   2*(flux u).yy - (mean u).y*(mean u).y⟩

theorem stress_identity (u : Field) :
    stress u = ⟨(u.ax-u.bx)*(u.ax-u.bx),
                (u.ax-u.bx)*(u.ay-u.bY),
                (u.ay-u.bY)*(u.ay-u.bY)⟩ := by
  apply Tensor2.ext <;> simp [stress, flux, mean, sub_eq_add_neg, mul_add, add_mul] <;> omega

/-- The recovered interface reconstructs the complete symmetric quadratic flux. -/
def reconstruct (m : Vector2) (t : Tensor2) : Tensor2 :=
  ⟨t.xx + m.x*m.x, t.xy + m.x*m.y, t.yy + m.y*m.y⟩

theorem reconstructed_flux (u : Field) :
    reconstruct (mean u) (stress u) =
      ⟨2*(flux u).xx, 2*(flux u).xy, 2*(flux u).yy⟩ := by
  apply Tensor2.ext <;> simp [reconstruct, stress] <;> omega

/-- Exact factorization through an observation. -/
def Factors {α β γ : Type} (E : α → β) (d : α → γ) : Prop :=
  ∀ x y, E x = E y → d x = d y

theorem factorization_iff {α β γ : Type} [Inhabited γ]
    (E : α → β) (d : α → γ) :
    Factors E d ↔ ∃ g : β → γ, ∀ x, g (E x) = d x := by
  constructor
  · intro h
    classical
    let g : β → γ := fun b =>
      if hb : ∃ a, E a = b then d (Classical.choose hb) else default
    refine ⟨g, ?_⟩
    intro x
    dsimp [g]
    split
    · rename_i hb
      exact h _ x (Classical.choose_spec hb)
    · rename_i hb
      exact False.elim (hb ⟨x, rfl⟩)
  · rintro ⟨g, hg⟩ x y he
    calc
      d x = g (E x) := (hg x).symm
      _ = g (E y) := congrArg g he
      _ = d y := hg y

/-- Adding the consequence is the coarsest common refinement of E and d. -/
def Refines {α β γ : Type} (F : α → β) (E : α → γ) : Prop :=
  ∀ x y, F x = F y → E x = E y

theorem least_consequence_refinement {α β γ δ : Type}
    (E : α → β) (d : α → γ) (F : α → δ) :
    Refines F (fun x => (E x, d x)) ↔ Refines F E ∧ Refines F d := by
  constructor
  · intro h
    exact ⟨(fun x y he => congrArg Prod.fst (h x y he)),
           (fun x y he => congrArg Prod.snd (h x y he))⟩
  · rintro ⟨hE, hd⟩ x y he
    exact Prod.ext (hE x y he) (hd x y he)

/-- A failure cannot be hidden by an exact factorization. -/
theorem failure_of_witness {α β γ : Type} (E : α → β) (d : α → γ)
    (a b : α) (he : E a = E b) (hd : d a ≠ d b) : ¬ Factors E d := by
  intro h
  exact hd (h a b he)

/-- The finite search grammar, with the full interface deliberately held out. -/
inductive Mask where
  | none | xx | xy | yy | xx_xy | xx_yy | xy_yy | all
  deriving DecidableEq, Repr

def observe : Mask → Field → Vector2 × (Int × Int × Int)
  | .none, u => (mean u, (0,0,0))
  | .xx, u => (mean u, ((flux u).xx,0,0))
  | .xy, u => (mean u, (0,(flux u).xy,0))
  | .yy, u => (mean u, (0,0,(flux u).yy))
  | .xx_xy, u => (mean u, ((flux u).xx,(flux u).xy,0))
  | .xx_yy, u => (mean u, ((flux u).xx,0,(flux u).yy))
  | .xy_yy, u => (mean u, (0,(flux u).xy,(flux u).yy))
  | .all, u => (mean u, ((flux u).xx,(flux u).xy,(flux u).yy))

private def witness_none_a : Field := { ax := -2, ay := -2, bx := -2, bY := 0 }
private def witness_none_b : Field := { ax := -2, ay := -1, bx := -2, bY := -1 }

theorem obstruction_none : ¬ Factors (observe .none) flux := by
  apply failure_of_witness (observe .none) flux witness_none_a witness_none_b
  · decide
  · decide

private def witness_xx_a : Field := { ax := -2, ay := -2, bx := -2, bY := 0 }
private def witness_xx_b : Field := { ax := -2, ay := -1, bx := -2, bY := -1 }

theorem obstruction_xx : ¬ Factors (observe .xx) flux := by
  apply failure_of_witness (observe .xx) flux witness_xx_a witness_xx_b
  · decide
  · decide

private def witness_xy_a : Field := { ax := -2, ay := -2, bx := -2, bY := 0 }
private def witness_xy_b : Field := { ax := -2, ay := -1, bx := -2, bY := -1 }

theorem obstruction_xy : ¬ Factors (observe .xy) flux := by
  apply failure_of_witness (observe .xy) flux witness_xy_a witness_xy_b
  · decide
  · decide

private def witness_yy_a : Field := { ax := -2, ay := -2, bx := -1, bY := -1 }
private def witness_yy_b : Field := { ax := -2, ay := -1, bx := -1, bY := -2 }

theorem obstruction_yy : ¬ Factors (observe .yy) flux := by
  apply failure_of_witness (observe .yy) flux witness_yy_a witness_yy_b
  · decide
  · decide

private def witness_xx_xy_a : Field := { ax := -2, ay := -2, bx := -2, bY := 0 }
private def witness_xx_xy_b : Field := { ax := -2, ay := -1, bx := -2, bY := -1 }

theorem obstruction_xx_xy : ¬ Factors (observe .xx_xy) flux := by
  apply failure_of_witness (observe .xx_xy) flux witness_xx_xy_a witness_xx_xy_b
  · decide
  · decide

private def witness_xx_yy_a : Field := { ax := -2, ay := -2, bx := -1, bY := -1 }
private def witness_xx_yy_b : Field := { ax := -2, ay := -1, bx := -1, bY := -2 }

theorem obstruction_xx_yy : ¬ Factors (observe .xx_yy) flux := by
  apply failure_of_witness (observe .xx_yy) flux witness_xx_yy_a witness_xx_yy_b
  · decide
  · decide

private def witness_xy_yy_a : Field := { ax := -2, ay := -2, bx := 0, bY := -2 }
private def witness_xy_yy_b : Field := { ax := -1, ay := -2, bx := -1, bY := -2 }

theorem obstruction_xy_yy : ¬ Factors (observe .xy_yy) flux := by
  apply failure_of_witness (observe .xy_yy) flux witness_xy_yy_a witness_xy_yy_b
  · decide
  · decide

theorem all_proper_masks_fail (m : Mask) (hm : m ≠ .all) :
    ¬ Factors (observe m) flux := by
  cases m with
  | none => exact obstruction_none
  | xx => exact obstruction_xx
  | xy => exact obstruction_xy
  | yy => exact obstruction_yy
  | xx_xy => exact obstruction_xx_xy
  | xx_yy => exact obstruction_xx_yy
  | xy_yy => exact obstruction_xy_yy
  | all => exact False.elim (hm rfl)

theorem full_interface_sufficient : Factors (observe .all) flux := by
  intro x y h
  have hq : flux x = flux y := by
    have := congrArg Prod.snd h
    apply Tensor2.ext
    · exact congrArg Prod.fst this
    · exact congrArg (fun p : Int × Int × Int => p.2.1) this
    · exact congrArg (fun p : Int × Int × Int => p.2.2) this
  exact hq

/-- A conservative three-cell Burgers finite-volume model. -/
def burgers (u : Int × Int × Int) : Int × Int × Int :=
  (u.2.2*u.2.2-u.1*u.1,
   u.1*u.1-u.2.1*u.2.1,
   u.2.1*u.2.1-u.2.2*u.2.2)

def mass (u : Int × Int × Int) : Int := u.1+u.2.1+u.2.2
def q (u : Int × Int × Int) : Int := u.1*u.1+u.2.1*u.2.1+u.2.2*u.2.2
def dq (u : Int × Int × Int) : Int :=
  2*(u.1*(burgers u).1+u.2.1*(burgers u).2.1+u.2.2*(burgers u).2.2)

theorem burgers_mass_conserved (u : Int × Int × Int) :
    mass (burgers u) = 0 := by
  simp [mass, burgers] <;> omega

private def dynamicA : Int × Int × Int := (1,1,-2)
private def dynamicB : Int × Int × Int := (-1,-1,2)

theorem dynamic_closure_obstruction :
    mass dynamicA = mass dynamicB ∧
    q dynamicA = q dynamicB ∧
    dq dynamicA ≠ dq dynamicB := by
  decide

/-- One-step quadratic closure does not imply closure of the next evolution law. -/
theorem no_mass_q_dynamics :
    ¬ Factors (fun u => (mass u, q u)) dq := by
  apply failure_of_witness (fun u => (mass u, q u)) dq dynamicA dynamicB
  · decide
  · decide

end FluidClosure
