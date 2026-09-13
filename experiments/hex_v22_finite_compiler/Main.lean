import HexGraphIso.Iso

namespace MathGraph

universe u v

structure Bijection (α : Type u) (β : Type v) where
  toFun : α → β
  invFun : β → α
  left_inv : ∀ x, invFun (toFun x) = x
  right_inv : ∀ y, toFun (invFun y) = y

instance {α : Type u} {β : Type v} : CoeFun (Bijection α β) (fun _ => α → β) :=
  ⟨Bijection.toFun⟩

namespace Bijection

variable {α : Type u} {β : Type v}

def symm (e : Bijection α β) : Bijection β α where
  toFun := e.invFun
  invFun := e.toFun
  left_inv := e.right_inv
  right_inv := e.left_inv

@[simp] theorem symm_apply_apply (e : Bijection α β) (x : α) :
    e.symm (e x) = x :=
  e.left_inv x

@[simp] theorem apply_symm_apply (e : Bijection α β) (y : β) :
    e (e.symm y) = y :=
  e.right_inv y

theorem injective (e : Bijection α β) : Function.Injective e := by
  intro x y h
  calc
    x = e.invFun (e x) := (e.left_inv x).symm
    _ = e.invFun (e y) := congrArg e.invFun h
    _ = y := e.left_inv y

theorem surjective (e : Bijection α β) : Function.Surjective e := by
  intro y
  exact ⟨e.symm y, e.apply_symm_apply y⟩

end Bijection

/--
A finite colored simple graph presented on an arbitrary vertex type V,
together with an explicit numbering by Fin n.
-/
structure FiniteColored (V : Type u) (n k : Nat) where
  number : Bijection V (Fin n)
  color : V → Fin k
  color_onto : Function.Surjective color
  adj : V → V → Bool
  adj_symm : ∀ u v, adj u v = adj v u
  adj_loopless : ∀ u, adj u u = false

namespace FiniteColored

open Hex Hex.GraphIso

variable {V : Type u} {W : Type v} {n k : Nat}

/-- Compile an explicitly numbered finite colored graph to Hex. -/
def toHex (A : FiniteColored V n k) : Colored n k where
  graph :=
    Graph.ofAdj
      (fun i j => A.adj (A.number.symm i) (A.number.symm j))
      (fun i j => by
        exact A.adj_symm (A.number.symm i) (A.number.symm j))
      (fun i => A.adj_loopless (A.number.symm i))
  coloring :=
    { cells := Hex.Vector.ofFn' fun i => A.color (A.number.symm i)
      onto := by
        intro c
        rcases A.color_onto c with ⟨v, hv⟩
        refine ⟨A.number v, ?_⟩
        rw [Hex.Vector.get_eq_getElem]
        simp [hv] }

@[simp] theorem toHex_adj (A : FiniteColored V n k) (i j : Fin n) :
    A.toHex.graph.adj i j = A.adj (A.number.symm i) (A.number.symm j) := by
  simp [toHex]

@[simp] theorem toHex_color (A : FiniteColored V n k) (i : Fin n) :
    A.toHex.coloring.cells[i] = A.color (A.number.symm i) := by
  simp [toHex]

end FiniteColored

/-- Isomorphism before compilation to Hex. -/
structure FiniteColoredIso
    {V : Type u} {W : Type v} {n k : Nat}
    (A : FiniteColored V n k) (B : FiniteColored W n k) where
  map : Bijection V W
  color : ∀ v, B.color (map v) = A.color v
  adj : ∀ u v, B.adj (map u) (map v) = A.adj u v

namespace FiniteColoredIso

open Hex Hex.GraphIso

variable {V : Type u} {W : Type v} {n k : Nat}
variable {A : FiniteColored V n k} {B : FiniteColored W n k}

def finMap (F : FiniteColoredIso A B) (i : Fin n) : Fin n :=
  B.number (F.map (A.number.symm i))

theorem finMap_inj (F : FiniteColoredIso A B) :
    ∀ i j, F.finMap i = F.finMap j → i = j := by
  intro i j h
  apply A.number.symm.injective
  apply F.map.injective
  apply B.number.injective
  exact h

theorem finMap_surj (F : FiniteColoredIso A B) :
    ∀ y : Fin n, ∃ i : Fin n, F.finMap i = y := by
  intro y
  refine ⟨A.number (F.map.symm (B.number.symm y)), ?_⟩
  simp [finMap]

def perm (F : FiniteColoredIso A B) : Hex.Perm n :=
  Hex.Perm.ofFn F.finMap F.finMap_inj F.finMap_surj

theorem toHex_isIso (F : FiniteColoredIso A B) :
    IsIso A.toHex B.toHex F.perm := by
  refine IsIso.mk ?_ ?_
  · intro i
    rw [FiniteColored.toHex_color, FiniteColored.toHex_color]
    simpa [perm, finMap] using F.color (A.number.symm i)
  · intro i j
    rw [FiniteColored.toHex_adj, FiniteColored.toHex_adj]
    simpa [perm, finMap] using F.adj (A.number.symm i) (A.number.symm j)

theorem toHex_isomorphic (F : FiniteColoredIso A B) :
    Isomorphic A.toHex B.toHex :=
  Isomorphic.intro F.perm F.toHex_isIso

end FiniteColoredIso

namespace FiniteColored

open Hex Hex.GraphIso

variable {V : Type u} {W : Type v} {n k : Nat}
variable {A : FiniteColored V n k} {B : FiniteColored W n k}

def mapFromPerm (p : Hex.Perm n) (v : V) : W :=
  B.number.symm (p.get (A.number v))

def invFromPerm (p : Hex.Perm n) (w : W) : V :=
  A.number.symm (p.inv.get (B.number w))

theorem inv_mapFromPerm (p : Hex.Perm n) (v : V) :
    invFromPerm (A := A) (B := B) p (mapFromPerm (A := A) (B := B) p v) = v := by
  simp [mapFromPerm, invFromPerm]

theorem map_invFromPerm (p : Hex.Perm n) (w : W) :
    mapFromPerm (A := A) (B := B) p (invFromPerm (A := A) (B := B) p w) = w := by
  simp [mapFromPerm, invFromPerm]

def nodeBijectionFromPerm (p : Hex.Perm n) : Bijection V W where
  toFun := mapFromPerm (A := A) (B := B) p
  invFun := invFromPerm (A := A) (B := B) p
  left_inv := inv_mapFromPerm (A := A) (B := B) p
  right_inv := map_invFromPerm (A := A) (B := B) p

end FiniteColored

/--
An explicit finite numbering is a semantics-preserving compiler boundary:
abstract finite-colored isomorphism is equivalent to Hex colored-graph
isomorphism.
-/
theorem finiteColoredIso_iff_hexIsomorphic
    {V : Type u} {W : Type v} {n k : Nat}
    (A : FiniteColored V n k) (B : FiniteColored W n k) :
    Nonempty (FiniteColoredIso A B) ↔
      Hex.GraphIso.Isomorphic A.toHex B.toHex := by
  constructor
  · rintro ⟨h⟩
    exact h.toHex_isomorphic
  · intro h
    rcases Hex.GraphIso.Isomorphic.elim h with ⟨p, hp⟩
    refine ⟨{
      map := FiniteColored.nodeBijectionFromPerm (A := A) (B := B) p
      color := ?_
      adj := ?_
    }⟩
    · intro v
      have hc := Hex.GraphIso.IsIso.cells_eq hp (A.number v)
      rw [FiniteColored.toHex_color, FiniteColored.toHex_color] at hc
      simpa [FiniteColored.nodeBijectionFromPerm, FiniteColored.mapFromPerm] using hc
    · intro u v
      have ha := Hex.GraphIso.IsIso.adj_eq hp (A.number u) (A.number v)
      rw [FiniteColored.toHex_adj, FiniteColored.toHex_adj] at ha
      simpa [FiniteColored.nodeBijectionFromPerm, FiniteColored.mapFromPerm] using ha

end MathGraph
